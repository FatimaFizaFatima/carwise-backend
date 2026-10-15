from datetime import time
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator, model_validator

from app.schema.auth import _check_password_policy
from app.schema.workshop_service import WorkshopServiceResponse

WorkshopStatusLiteral = Literal["pending", "approved", "rejected", "suspended"]
WorkshopName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]


class WorkshopStaffRegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    workshop_name: WorkshopName

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
    model_config = ConfigDict(str_strip_whitespace=True)

    workshop_name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    address: str | None = Field(default=None, max_length=255)
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = Field(default=None, max_length=20)
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

    @model_validator(mode="after")
    def validate_hours(self):
        if self.opens_at is not None and self.closes_at is not None and self.opens_at >= self.closes_at:
            raise ValueError("opens_at must be earlier than closes_at")
        return self


class WorkshopUpdateRequest(WorkshopCreateRequest):
    workshop_name: str | None = Field(default=None, min_length=1, max_length=150)


class AdminWorkshopCreateRequest(WorkshopCreateRequest):
    status: WorkshopStatusLiteral = "approved"


class AdminWorkshopUpdateRequest(WorkshopUpdateRequest):
    status: WorkshopStatusLiteral | None = None


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


class WorkshopDetailResponse(WorkshopResponse):
    review_count: int
    services: list[WorkshopServiceResponse]


class WorkshopNearbyResponse(WorkshopResponse):
    distance_km: float


class PaginatedWorkshopResponse(BaseModel):
    items: list[WorkshopResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
