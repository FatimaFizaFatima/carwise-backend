import re
from pydantic import BaseModel, EmailStr, field_validator


def _check_password_policy(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[0-9!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one number or symbol")
    return value


def _check_otp_format(value: str) -> str:
    if not value.isdigit() or len(value) != 6:
        raise ValueError("OTP must be exactly 6 digits")
    return value


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _check_password_policy(value)


class RegisterResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    message: str = "Registration successful. Please verify the OTP sent to your email."



class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        return _check_otp_format(value)


class ResendOtpRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str



class OAuthLoginRequest(BaseModel):
    provider_token: str



class ForgotPasswordRequest(BaseModel):
    identifier: str


class ForgotPasswordResponse(BaseModel):
    message: str = "If this account exists, a reset code has been sent."


class VerifyResetCodeRequest(BaseModel):
    identifier: str
    otp: str

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        return _check_otp_format(value)


class VerifyResetCodeResponse(BaseModel):
    reset_token: str


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _check_password_policy(value)


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: str



class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str