from pydantic import BaseModel, EmailStr, field_validator
from app.schema.auth import _check_password_policy


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