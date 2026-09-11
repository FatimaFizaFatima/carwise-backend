from pydantic import BaseModel, field_validator
from app.schema.auth import _check_password_policy


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _check_password_policy(value)


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    location: str | None = None


class UserProfileResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str | None
    location: str | None
    email_verified: bool
    phone_verified: bool
    avatar_url: str | None