from fastapi import APIRouter, Depends, Path, Query, status
from app.core.dependencies import get_current_user
from app.service import notification_service
from app.schema.notification import DeviceTokenRegisterRequest, DeviceTokenResponse, BroadcastNotificationRequest, NotificationResponse, UnreadCountResponse, MarkAllReadResponse
from app.models.user_models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/device-token", response_model=DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_device_token(data: DeviceTokenRegisterRequest, current_user: User = Depends(get_current_user)):
    return await notification_service.register_device_token(current_user.id, data)


@router.delete("/device-token/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device_token(token: str, current_user: User = Depends(get_current_user)):
    await notification_service.unregister_device_token(current_user.id, token)


@router.post("/broadcast", status_code=status.HTTP_200_OK)
async def send_broadcast(data: BroadcastNotificationRequest, current_user: User = Depends(get_current_user)):
    await notification_service.send_broadcast(current_user, data)
    return {"message": "Broadcast sent."}



@router.get("", response_model=list[NotificationResponse], summary="My notification history, newest first")
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    return await notification_service.list_notifications(current_user, unread_only, page, page_size)


@router.get("/unread-count", response_model=UnreadCountResponse, summary="Number of unread notifications")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    return await notification_service.get_unread_count(current_user)


@router.post("/read-all", response_model=MarkAllReadResponse, summary="Mark all my notifications as read")
async def mark_all_read(current_user: User = Depends(get_current_user)):
    return await notification_service.mark_all_read(current_user)


@router.post("/{notification_id}/read", response_model=NotificationResponse, summary="Mark one notification as read")
async def mark_notification_read(
    notification_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
):
    return await notification_service.mark_notification_read(current_user, notification_id)