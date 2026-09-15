from datetime import date, datetime
from pydantic import BaseModel, field_validator


class CarCreateRequest(BaseModel):
    user_id: int | None = None 
    registration_no: str
    owner_name: str
    make: str
    vehicle_model: str
    model_year: int
    registration_date: date
    provision: str | None = None
    body_type: str | None = None
    class_of_vehicle: str | None = None
    engine_number: str | None = None
    engine_capacity_cc: int | None = None
    seating_capacity: int | None = None

    @field_validator("model_year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        if value < 1980 or value > datetime.now().year + 1:
            raise ValueError("Enter a realistic model year")
        return value

    @field_validator("registration_date")
    @classmethod
    def validate_registration_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Registration date cannot be in the future")
        return value


class CarUpdateRequest(BaseModel):
    owner_name: str | None = None
    make: str | None = None
    vehicle_model: str | None = None
    model_year: int | None = None
    provision: str | None = None
    body_type: str | None = None
    class_of_vehicle: str | None = None
    engine_capacity_cc: int | None = None
    seating_capacity: int | None = None


class CarResponse(BaseModel):
    id: int
    user_id: int | None
    registration_no: str
    owner_name: str
    make: str
    vehicle_model: str
    model_year: int
    registration_date: date
    provision: str | None
    body_type: str | None
    class_of_vehicle: str | None
    engine_number: str | None
    engine_capacity_cc: int | None
    seating_capacity: int | None
    created_at: datetime


class AssociateCarRequest(BaseModel):
    user_id: int