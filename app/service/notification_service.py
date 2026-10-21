import logging
import httpx
from app.unit_of_work.unit_of_work import UnitOfWork
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.roles import NotificationType, Role
from app.models.device_token import DeviceToken
from app.models.booking import Booking
from app.models.user_models import User
from app.schema.notification import DeviceTokenRegisterRequest, DeviceTokenResponse, BroadcastNotificationRequest, MarkAllReadResponse, NotificationResponse, NotificationType, UnreadCountResponse
from datetime import datetime, timezone
from app.models.notification import Notification


logger = logging.getLogger(__name__)

ONESIGNAL_API_URL = "https://api.onesignal.com/notifications"
NOT_SAVED_TYPES = {NotificationType.NEW_CHAT_MESSAGE}

def _notification_to_response(n: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=n.id, title=n.title, message=n.message,
        notification_type=n.notification_type, reference_id=n.reference_id,
        data=n.data, is_read=n.is_read, read_at=n.read_at, created_at=n.created_at,
    )


def _to_response(device_token: DeviceToken) -> DeviceTokenResponse:
    return DeviceTokenResponse(
        id=device_token.id, device_type=device_token.device_type,
        is_active=device_token.is_active, created_at=device_token.created_at,
    )


async def register_device_token(user_id: int, data: DeviceTokenRegisterRequest) -> DeviceTokenResponse:
    async with UnitOfWork() as uow:
        existing = await uow.device_tokens.get_by_token(data.token)

        if existing is None:
            device_token = DeviceToken(
                user_id=user_id, token=data.token, device_type=data.device_type, is_active=True,
            )
            uow.device_tokens.add(device_token)
        else:
          
            device_token = await uow.device_tokens.update(existing, {
                "user_id": user_id, "device_type": data.device_type, "is_active": True,
            })

        await uow.commit()
        return _to_response(device_token)


async def unregister_device_token(user_id: int, token: str) -> None:
    async with UnitOfWork() as uow:
        device_token = await uow.device_tokens.deactivate(token, user_id)
        if device_token is None:
            raise AppException("Device token not found", status_code=404)
        await uow.commit()


async def send_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    reference_id: int | str | None = None,
    data: dict | None = None,
) -> None:
    """Core reusable sender. Sends one push to every active device belonging to
    user_id, via OneSignal. Opens its own UnitOfWork so it's safe to run as a
    FastAPI BackgroundTask, after the caller's own uow has already closed.
    Deliberately never raises -- a failed or skipped notification should never
    break the business action that triggered it."""
    async with UnitOfWork() as uow:
        if notification_type not in NOT_SAVED_TYPES:
            try:
                uow.notifications.add(Notification(
                    user_id=user_id, title=title, message=message,
                    notification_type=notification_type,
                    reference_id=reference_id if isinstance(reference_id, int) else None,
                    data=data or None,
                ))
                await uow.commit()
            except Exception:
                logger.exception("Failed to save notification history for user_id=%s", user_id)
                await uow.rollback()
        tokens = await uow.device_tokens.get_active_by_user(user_id)
    if not tokens:
        return
    if not tokens:
        return

    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "include_subscription_ids": [t.token for t in tokens],
        "target_channel": "push",
        "headings": {"en": title},
        "contents": {"en": message},
        "data": {"type": notification_type, "reference_id": reference_id, **(data or {})},
    }
    headers = {
        "Authorization": f"Key {settings.ONESIGNAL_REST_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(ONESIGNAL_API_URL, json=payload, headers=headers)
        if response.status_code >= 400:
            logger.error(
                "OneSignal send failed for user_id=%s status=%s body=%s",
                user_id, response.status_code, response.text,
            )
        else:
            body = response.json()
            if body.get("errors") or body.get("recipients", 0) == 0:
                logger.warning("OneSignal send for user_id=%s reached 0 recipients: %s", user_id, body)
    except httpx.HTTPError as exc:
        logger.error("OneSignal request error for user_id=%s: %s", user_id, exc)


async def notify_booking_created(booking: Booking) -> None:
    await send_notification(
        booking.user_id,
        title="Booking received",
        message=f"Your booking {booking.booking_reference} has been received and is pending confirmation.",
        notification_type=NotificationType.BOOKING_CREATED,
        reference_id=booking.id,
    )


async def notify_booking_confirmed(booking: Booking) -> None:
    await send_notification(
        booking.user_id,
        title="Booking confirmed",
        message=f"Your booking {booking.booking_reference} has been confirmed.",
        notification_type=NotificationType.BOOKING_CONFIRMED,
        reference_id=booking.id,
    )


async def notify_booking_status_updated(booking: Booking, new_status: str) -> None:
    await send_notification(
        booking.user_id,
        title="Booking status updated",
        message=f"Your booking {booking.booking_reference} is now {new_status.replace('_', ' ')}.",
        notification_type=NotificationType.BOOKING_STATUS_UPDATED,
        reference_id=booking.id,
        data={"status": new_status},
    )


async def notify_booking_cancelled(booking: Booking) -> None:
    await send_notification(
        booking.user_id,
        title="Booking cancelled",
        message=f"Your booking {booking.booking_reference} has been cancelled.",
        notification_type=NotificationType.BOOKING_CANCELLED,
        reference_id=booking.id,
    )


async def notify_booking_rescheduled(booking: Booking, old_date, old_time) -> None:
    await send_notification(
        booking.user_id,
        title="Booking rescheduled",
        message=(
            f"Your booking {booking.booking_reference} was moved from "
            f"{old_date} {old_time} to {booking.scheduled_date} {booking.scheduled_time}."
        ),
        notification_type=NotificationType.BOOKING_RESCHEDULED,
        reference_id=booking.id,
        data={
            "old_scheduled_date": str(old_date), "old_scheduled_time": str(old_time),
            "new_scheduled_date": str(booking.scheduled_date), "new_scheduled_time": str(booking.scheduled_time),
        },
    )

async def _save_broadcast_history(
    user_ids: list[int], title: str, message: str, notification_type: str
) -> None:
    try:
        async with UnitOfWork() as uow:
            uow.notifications.add_many([
                Notification(user_id=uid, title=title, message=message,
                             notification_type=notification_type)
                for uid in user_ids
            ])
            await uow.commit()
    except Exception:
        logger.exception("Failed to save broadcast history")

async def send_broadcast_notification(title: str, message: str, notification_type: str) -> None:
    """Targets every active device directly via our own device_tokens table,
    rather than OneSignal's built-in 'Subscribed Users' segment -- that segment
    is computed asynchronously on OneSignal's side and was observed rejecting
    a genuinely subscribed device with 'All included players are not
    subscribed', while direct subscription-id targeting (what send_notification
    already uses successfully) reached the same device with no issue."""
    async with UnitOfWork() as uow:
        tokens = await uow.device_tokens.get_all_active()

    if not tokens:
        raise AppException("No active device tokens registered to broadcast to", status_code=409)
    
    user_ids = sorted({t.user_id for t in tokens})

    headers = {
        "Authorization": f"Key {settings.ONESIGNAL_REST_API_KEY}",
        "Content-Type": "application/json",
    }

    total_recipients = 0
    all_errors = []
    token_values = [t.token for t in tokens]

    for i in range(0, len(token_values), 2000):
        chunk = token_values[i:i + 2000]
        payload = {
            "app_id": settings.ONESIGNAL_APP_ID,
            "include_subscription_ids": chunk,
            "target_channel": "push",
            "headings": {"en": title},
            "contents": {"en": message},
            "data": {"type": notification_type},
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(ONESIGNAL_API_URL, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            logger.error("OneSignal broadcast request error: %s", exc)
            raise AppException("Failed to reach OneSignal", status_code=502)

        if response.status_code >= 400:
            logger.error("OneSignal broadcast failed status=%s body=%s", response.status_code, response.text)
            raise AppException(f"OneSignal rejected the broadcast: {response.text}", status_code=502)

        body = response.json()
        total_recipients += body.get("recipients", 0)
        all_errors.extend(body.get("errors") or [])

    if all_errors:
        logger.error("OneSignal broadcast reported errors: %s", all_errors)
        raise AppException(f"OneSignal reported errors: {all_errors}", status_code=502)
   
    if total_recipients == 0:
        logger.info(
            "OneSignal reported recipients=0 for %s registered tokens (delivery may still have succeeded "
            "-- this field is unreliable for direct subscription-id targeting)", len(token_values),
        )
    await _save_broadcast_history(user_ids, title, message, notification_type)    


async def send_broadcast(current_user: User, data: BroadcastNotificationRequest) -> None:
    if current_user.role != Role.ADMIN:
        raise AppException("Only admin can send broadcast notifications", status_code=403)
    await send_broadcast_notification(data.title, data.message, data.notification_type)


async def list_notifications(
    current_user: User, unread_only: bool, page: int, page_size: int
) -> list[NotificationResponse]:
    async with UnitOfWork() as uow:
        items = await uow.notifications.get_for_user(
            current_user.id, unread_only, page_size, (page - 1) * page_size
        )
        return [_notification_to_response(n) for n in items]


async def get_unread_count(current_user: User) -> UnreadCountResponse:
    async with UnitOfWork() as uow:
        count = await uow.notifications.count_unread(current_user.id)
        return UnreadCountResponse(unread_count=count)


async def mark_notification_read(current_user: User, notification_id: int) -> NotificationResponse:
    async with UnitOfWork() as uow:
        notification = await uow.notifications.get_owned(notification_id, current_user.id)
        if notification is None:
            raise AppException("Notification not found", status_code=404)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await uow.commit()
        return _notification_to_response(notification)


async def mark_all_read(current_user: User) -> MarkAllReadResponse:
    async with UnitOfWork() as uow:
        updated = await uow.notifications.mark_all_read(current_user.id)
        await uow.commit()
        return MarkAllReadResponse(updated_count=updated)
