from datetime import datetime
from pydantic import BaseModel, field_validator
from app.core.roles import NotificationType


class DeviceTokenRegisterRequest(BaseModel):

    token: str
    device_type: str

    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, value: str) -> str:
        allowed = ("ios", "android", "web")
        if value not in allowed:
            raise ValueError(f"device_type must be one of {allowed}")
        return value


class DeviceTokenResponse(BaseModel):

    id: int
    device_type: str
    is_active: bool
    created_at: datetime


class BroadcastNotificationRequest(BaseModel):

    title: str
    message: str
    notification_type: str

    @field_validator("notification_type")
    @classmethod
    def validate_notification_type(cls, value: str) -> str:
        
        allowed = (NotificationType.PROMOTIONAL_OFFER, NotificationType.SYSTEM_MAINTENANCE)
        if value not in allowed:
            raise ValueError(f"notification_type must be one of {allowed}")
        return value