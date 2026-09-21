from datetime import datetime, time, date
from pydantic import BaseModel, field_validator


class BookingCreateRequest(BaseModel):

    car_id : int
    workshop_id : int
    workshop_service_ids: list[int]
    service_type : str
    pickup_address : str | None = None
    delivery_address : str | None = None
    note: str | None = None
    scheduled_date: date
    scheduled_time: time

    @field_validator("workshop_service_ids")
    @classmethod
    def validate_services(cls, value : list[int])-> list[int]:
        if not value:
            raise ValueError("At least one service must be selected")
        return value

    @field_validator("scheduled_date")
    @classmethod
    def validate_future_date(cls, value : date)-> date:
        if value < date.today():
            raise ValueError("Scheduled date cannot be in the past")

        return value

    @field_validator("scheduled_time")
    @classmethod
    def strip_timezone(cls, value: time) -> time:
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)
        return value


class BookingItemResponse(BaseModel):
    workshop_service_id: int
    price_snapshot: float


class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    user_id: int
    car_id: int
    workshop_id: int
    service_type: str
    pickup_address: str | None
    delivery_address: str | None
    note: str | None
    scheduled_date: date
    scheduled_time: time
    status: str
    total_price: float
    items: list[BookingItemResponse]
    created_at: datetime


class RescheduleRequest(BaseModel):
    scheduled_date: date
    scheduled_time: time

    @field_validator("scheduled_time")
    @classmethod
    def strip_timezone(cls, value: time) -> time:
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)
        return value


class BookingStatusUpdateRequest(BaseModel):
    status: str