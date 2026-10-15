from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from app.core.dependencies import get_current_user
from app.schema.chat import ConversationCreateRequest, ConversationResponse, MarkReadRequest, MessageResponse, MessageSendRequest
from app.service import chat_service, chat_notification_service
from app.realtime.socket_server import (
    emit_new_message, emit_message_status, users_in_conversation,
)
from app.models.user_models import User
from app.realtime.socket_server import emit_new_message, emit_message_status


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/conversations", response_model=ConversationResponse)
async def get_or_create_conversation(
    data: ConversationCreateRequest, current_user: User = Depends(get_current_user)
):
    return await chat_service.get_or_create_conversation(current_user, data)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(current_user: User = Depends(get_current_user)):
    return await chat_service.list_conversations(current_user)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(conversation_id: int, before_id: int | None = Query(None, ge=1), after_id: int | None = Query(None, ge=1), limit: int = Query(30, ge=1, le=100), current_user: User = Depends(get_current_user)):
    return await chat_service.get_messages(
        current_user, conversation_id, before_id, after_id, limit
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: int,
    data: MessageSendRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    message = await chat_service.send_message(current_user, conversation_id, data)
    await emit_new_message(message)
    background_tasks.add_task(
        chat_notification_service.notify_new_message,
        message,
        users_in_conversation(conversation_id),
    )
    return message


@router.post("/conversations/{conversation_id}/read")
async def mark_read(conversation_id: int, data: MarkReadRequest, current_user: User = Depends(get_current_user)):
    result = await chat_service.mark_read(current_user, conversation_id, data)
    await emit_message_status(conversation_id, "read", result["read_message_ids"])
    return result