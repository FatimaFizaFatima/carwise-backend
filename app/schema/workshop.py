from pydantic import BaseModel, EmailStr, field_validator
from app.schema.auth import _check_password_policy
from datetime import time

class WorkshopStaffRegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    workshop_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _check_password_policy(value)


class WorkshopStaffRegisterResponse(BaseModel):
    id: int
    full_name: str
    email: str
    workshop_id: int
    status: str
    message: str = "Registration submitted. Your account is pending admin approval."

class WorkshopCreateRequest(BaseModel):
    workshop_name: str
    description: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    opens_at: time | None = None
    closes_at: time | None = None

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, value: float | None) -> float | None:
        if value is not None and not (-90 <= value <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_lng(cls, value: float | None) -> float | None:
        if value is not None and not (-180 <= value <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return value


class WorkshopUpdateRequest(WorkshopCreateRequest):
    workshop_name: str | None = None


class WorkshopResponse(BaseModel):
    id: int
    workshop_name: str
    status: str
    description: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    phone: str | None
    image_url: str | None
    avg_rating: float
    opens_at: time | None
    closes_at: time | None


class WorkshopNearbyResponse(WorkshopResponse):
    distance_km: float


class PaginatedWorkshopResponse(BaseModel):
    items: list[WorkshopResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
