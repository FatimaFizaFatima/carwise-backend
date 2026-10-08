import logging
import socketio
from pydantic import ValidationError
from socketio.exceptions import ConnectionRefusedError
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.securtiy import decode_token
from app.core.roles import AccountStatus
from app.models.user_models import User
from app.schema.chat import MessageSendRequest, MessageResponse, MarkDeliveredRequest, MarkReadRequest
from app.service import chat_service, chat_notification_service
from app.unit_of_work.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.allowed_origins,
)


def conversation_room(conversation_id: int) -> str:
    return f"conversation_{conversation_id}"


connections: dict[str, dict] = {}


def _user_in_conversation(
    user_id: int, conversation_id: int, exclude_sid: str | None = None
) -> bool:
    return any(
        s != exclude_sid
        and info["user_id"] == user_id
        and conversation_id in info["conversations"]
        for s, info in connections.items()
    )


def _online_in_conversation(conversation_id: int, exclude_user_id: int) -> list[dict]:
    users = {}
    for info in connections.values():
        if conversation_id in info["conversations"] and info["user_id"] != exclude_user_id:
            users[info["user_id"]] = info["role"]
    return [{"user_id": uid, "role": role} for uid, role in users.items()]


async def _emit_presence(
    conversation_id: int, user_id: int, role: str, online: bool, skip_sid: str | None = None
) -> None:
    await sio.emit(
        "presence_update",
        {"conversation_id": conversation_id, "user_id": user_id, "role": role, "online": online},
        to=conversation_room(conversation_id),
        skip_sid=skip_sid,
    )

def users_in_conversation(conversation_id: int) -> set[int]:
    return {
        info["user_id"]
        for info in connections.values()
        if conversation_id in info["conversations"]
    }

async def _get_socket_user(sid: str) -> User:
    session = await sio.get_session(sid)
    async with UnitOfWork() as uow:
        user = await uow.users.get_by_id(session["user_id"])
        if user is None or user.status != AccountStatus.ACTIVE:
            raise AppException("User not allowed", status_code=403)
        return user


async def emit_new_message(message: MessageResponse, skip_sid: str | None = None) -> None:
    await sio.emit(
        "new_message",
        message.model_dump(mode="json"),
        to=conversation_room(message.conversation_id),
        skip_sid=skip_sid,
    )

async def emit_message_status(
    conversation_id: int, status: str, message_ids: list[int], skip_sid: str | None = None
) -> None:
    if not message_ids:
        return
    await sio.emit(
        "message_status",
        {"conversation_id": conversation_id, "status": status, "message_ids": message_ids},
        to=conversation_room(conversation_id),
        skip_sid=skip_sid,
    )

@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token")
    if not token:
        raise ConnectionRefusedError("Token missing")

    try:
        payload = decode_token(token)
    except AppException:
        raise ConnectionRefusedError("Invalid or expired token")

    if payload.get("type") != "access" or not payload.get("sub"):
        raise ConnectionRefusedError("Invalid token")

    async with UnitOfWork() as uow:
        user = await uow.users.get_by_id(int(payload["sub"]))
        if user is None or user.status != AccountStatus.ACTIVE:
            raise ConnectionRefusedError("User not allowed")
        session_data = {
            "user_id": user.id,
            "role": user.role,
            "workshop_id": user.workshop_id,
        }
        
    await sio.save_session(sid, session_data)
    await sio.enter_room(sid, f"user_{session_data['user_id']}")
    connections[sid] = {
        "user_id": session_data["user_id"],
        "role": session_data["role"],
        "conversations": set(),
    }
    logger.info("Socket connected: sid=%s user_id=%s", sid, session_data["user_id"])


@sio.event
async def disconnect(sid):
    info = connections.pop(sid, None)
    logger.info("Socket disconnected: sid=%s", sid)
    if info is None:
        return

    for conversation_id in info["conversations"]:
        if not _user_in_conversation(info["user_id"], conversation_id):
            await _emit_presence(conversation_id, info["user_id"], info["role"], False)


@sio.on("join_conversation")
async def join_conversation(sid, data):
    try:
        user = await _get_socket_user(sid)
        conversation_id = int(data["conversation_id"])
        await chat_service.check_conversation_access(user, conversation_id)
    except AppException as e:
        return {"ok": False, "error": e.message}
    except (KeyError, TypeError, ValueError):
        return {"ok": False, "error": "conversation_id is required"}

    info = connections.get(sid)
    if info is None:
        return {"ok": False, "error": "Not connected"}

    was_present = _user_in_conversation(info["user_id"], conversation_id)

    await sio.enter_room(sid, conversation_room(conversation_id))
    info["conversations"].add(conversation_id)

    if not was_present:
        await _emit_presence(
            conversation_id, info["user_id"], info["role"], True, skip_sid=sid
        )

    return {
        "ok": True,
        "room": conversation_room(conversation_id),
        "online": _online_in_conversation(conversation_id, info["user_id"]),
    }

@sio.on("send_message")
async def send_message(sid, data):
    try:
        user = await _get_socket_user(sid)
        conversation_id = int(data["conversation_id"])
        payload = MessageSendRequest(text=data["text"])
        message = await chat_service.send_message(user, conversation_id, payload)
    except AppException as e:
        return {"ok": False, "error": e.message}
    except ValidationError:
        return {"ok": False, "error": "Invalid message text"}
    except (KeyError, TypeError, ValueError):
        return {"ok": False, "error": "conversation_id and text are required"}

    await emit_new_message(message, skip_sid=sid)
    sio.start_background_task(
        chat_notification_service.notify_new_message,
        message,
        users_in_conversation(conversation_id),
    )
    return {"ok": True, "message": message.model_dump(mode="json")}


@sio.on("message_delivered")
async def message_delivered(sid, data):
    try:
        user = await _get_socket_user(sid)
        conversation_id = int(data["conversation_id"])
        payload = MarkDeliveredRequest(up_to_message_id=data["up_to_message_id"])
        result = await chat_service.mark_delivered(user, conversation_id, payload)
    except AppException as e:
        return {"ok": False, "error": e.message}
    except ValidationError:
        return {"ok": False, "error": "up_to_message_id must be a number"}
    except (KeyError, TypeError, ValueError):
        return {"ok": False, "error": "conversation_id and up_to_message_id are required"}

    await emit_message_status(conversation_id, "delivered", result["delivered_message_ids"], sid)
    return {"ok": True, **result}


@sio.on("messages_read")
async def messages_read(sid, data):
    try:
        user = await _get_socket_user(sid)
        conversation_id = int(data["conversation_id"])
        payload = MarkReadRequest(up_to_message_id=data["up_to_message_id"])
        result = await chat_service.mark_read(user, conversation_id, payload)
    except AppException as e:
        return {"ok": False, "error": e.message}
    except ValidationError:
        return {"ok": False, "error": "up_to_message_id must be a number"}
    except (KeyError, TypeError, ValueError):
        return {"ok": False, "error": "conversation_id and up_to_message_id are required"}

    await emit_message_status(conversation_id, "read", result["read_message_ids"], sid)
    return {"ok": True, **result}
