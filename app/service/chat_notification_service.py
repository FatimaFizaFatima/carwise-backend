import logging
from app.core.roles import NotificationType
from app.schema.chat import MessageResponse
from app.service import notification_service
from app.unit_of_work.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)

MAX_PREVIEW_LENGTH = 100


async def notify_new_message(message: MessageResponse, online_user_ids: set[int]) -> None:
    """Push a notification to the other side of the chat, except users who are in
    the conversation right now. Never raises: a failed push must not break chat."""
    try:
        async with UnitOfWork() as uow:
            conversation = await uow.conversations.get_by_id(message.conversation_id)
            sender = await uow.users.get_by_id(message.sender_id)
            if conversation is None or sender is None:
                return

            booking = await uow.bookings.get_by_id(conversation.booking_id)
            if sender.id == conversation.customer_id:
                recipient_ids = await uow.users.get_active_staff_ids_by_workshop(
                    conversation.workshop_id
                )
            else:
                recipient_ids = [conversation.customer_id]

            sender_name = sender.full_name
            booking_id = conversation.booking_id
            booking_reference = booking.booking_reference if booking else None

        to_notify = [uid for uid in recipient_ids if uid not in online_user_ids]
        skipped = [uid for uid in recipient_ids if uid in online_user_ids]
        logger.info(
            "Chat push: conversation=%s sender=%s notify=%s skipped_online=%s",
            message.conversation_id, message.sender_id, to_notify, skipped,
        )

        text = message.text
        preview = text if len(text) <= MAX_PREVIEW_LENGTH else text[:MAX_PREVIEW_LENGTH - 3] + "..."

        for user_id in to_notify:
            await notification_service.send_notification(
                user_id,
                title=sender_name,
                message=preview,
                notification_type=NotificationType.NEW_CHAT_MESSAGE,
                reference_id=message.conversation_id,
                data={
                    "conversation_id": message.conversation_id,
                    "booking_id": booking_id,
                    "booking_reference": booking_reference,
                },
            )
    except Exception:
        logger.exception("Chat push failed for conversation=%s", message.conversation_id)