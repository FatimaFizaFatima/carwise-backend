from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.unit_of_work.unit_of_work import UnitOfWork
from app.core.exceptions import AppException
from app.core.roles import Role
from app.models.user_models import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.schema.chat import (
    ConversationCreateRequest, ConversationResponse,
    MessageSendRequest, MessageResponse, MarkReadRequest,
)


def _is_customer_side(conversation: Conversation, user: User) -> bool:
    """True if the user is the customer of this conversation.
    False if the user is staff of its workshop. Otherwise raises 403."""
    if user.id == conversation.customer_id:
        return True
    if user.role == Role.WORKSHOP_STAFF and user.workshop_id == conversation.workshop_id:
        return False
    raise AppException("You do not have access to this conversation", status_code=403)


async def _get_conversation_for_user(uow: UnitOfWork, conversation_id: int, user: User):
    conversation = await uow.conversations.get_by_id(conversation_id)
    if conversation is None:
        raise AppException("Conversation not found", status_code=404)
    for_customer = _is_customer_side(conversation, user)
    return conversation, for_customer


def _to_message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id, conversation_id=message.conversation_id,
        sender_id=message.sender_id, text=message.text, status=message.status,
        delivered_at=message.delivered_at, read_at=message.read_at,
        created_at=message.created_at,
    )


async def _build_conversation_response(
    uow: UnitOfWork, conversation: Conversation, for_customer: bool
) -> ConversationResponse:
    booking = await uow.bookings.get_by_id(conversation.booking_id)

    if for_customer:
        workshop = await uow.workshops.get_by_id(conversation.workshop_id)
        other_party_name = workshop.workshop_name if workshop else "Workshop"
    else:
        customer = await uow.users.get_by_id(conversation.customer_id)
        other_party_name = customer.full_name if customer else "Customer"

    last = await uow.messages.get_last(conversation.id)
    unread = await uow.messages.count_unread(
        conversation.id, conversation.customer_id, for_customer
    )
    return ConversationResponse(
        id=conversation.id, booking_id=conversation.booking_id,
        booking_reference=booking.booking_reference,
        other_party_name=other_party_name,
        last_message=last.text if last else None,
        last_message_at=conversation.last_message_at,
        unread_count=unread,
    )


async def get_or_create_conversation(
    current_user: User, data: ConversationCreateRequest
) -> ConversationResponse:
    async with UnitOfWork() as uow:
        booking = await uow.bookings.get_by_id(data.booking_id)
        if booking is None:
            raise AppException("Booking not found", status_code=404)

        is_customer = booking.user_id == current_user.id
        is_staff = (
            current_user.role == Role.WORKSHOP_STAFF
            and current_user.workshop_id == booking.workshop_id
        )
        if not (is_customer or is_staff):
            raise AppException("Booking not found", status_code=404)

        conversation = await uow.conversations.get_by_booking_id(booking.id)
        if conversation is None:
            conversation = Conversation(
                booking_id=booking.id,
                customer_id=booking.user_id,
                workshop_id=booking.workshop_id,
            )
            uow.conversations.add(conversation)
            try:
                await uow.commit()
            except IntegrityError:
                await uow.rollback()
                conversation = await uow.conversations.get_by_booking_id(booking.id)

        return await _build_conversation_response(uow, conversation, is_customer)


async def list_conversations(current_user: User) -> list[ConversationResponse]:
    async with UnitOfWork() as uow:
        if current_user.role == Role.CUSTOMER:
            conversations = await uow.conversations.get_for_customer(current_user.id)
            for_customer = True
        elif current_user.role == Role.WORKSHOP_STAFF and current_user.workshop_id:
            conversations = await uow.conversations.get_for_workshop(current_user.workshop_id)
            for_customer = False
        else:
            raise AppException("Chat is only for customers and workshop staff", status_code=403)

        return [
            await _build_conversation_response(uow, c, for_customer)
            for c in conversations
        ]


async def send_message(
    current_user: User, conversation_id: int, data: MessageSendRequest
) -> MessageResponse:
    async with UnitOfWork() as uow:
        conversation, _ = await _get_conversation_for_user(uow, conversation_id, current_user)

        message = Message(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            text=data.text,
        )
        uow.messages.add(message)
        conversation.last_message_at = datetime.now(timezone.utc)
        await uow.commit()
        await uow.session.refresh(message)
        return _to_message_response(message)


async def get_messages(
    current_user: User, conversation_id: int,
    before_id: int | None = None, after_id: int | None = None, limit: int = 30,
) -> list[MessageResponse]:
    limit = max(1, min(limit, 100))
    async with UnitOfWork() as uow:
        await _get_conversation_for_user(uow, conversation_id, current_user)

        if after_id is not None:
            messages = await uow.messages.get_after(conversation_id, after_id, limit)
        else:
            messages = await uow.messages.get_history(conversation_id, before_id, limit)
            messages.reverse()

        return [_to_message_response(m) for m in messages]


async def mark_read(
    current_user: User, conversation_id: int, data: MarkReadRequest
) -> dict:
    async with UnitOfWork() as uow:
        conversation, for_customer = await _get_conversation_for_user(
            uow, conversation_id, current_user
        )
        read_ids = await uow.messages.mark_read(
            conversation.id, conversation.customer_id, for_customer, data.up_to_message_id
        )
        await uow.commit()
        return {"read_message_ids": read_ids}