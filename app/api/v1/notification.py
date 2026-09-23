from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user
from app.service import notification_service
from app.schema.notification import DeviceTokenRegisterRequest, DeviceTokenResponse, BroadcastNotificationRequest
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