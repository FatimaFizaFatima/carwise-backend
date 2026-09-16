from fastapi import APIRouter, status
from app.schema.auth import (
    RegisterRequest, RegisterResponse,
    VerifyOtpRequest, ResendOtpRequest,
    LoginRequest, OAuthLoginRequest,
    ForgotPasswordRequest, ForgotPasswordResponse,
    VerifyResetCodeRequest, VerifyResetCodeResponse,
    ResetPasswordRequest,
    RefreshRequest, RefreshResponse,
    LogoutRequest,
    TokenResponse, MessageResponse,
)
from app.service import auth_service
from app.service import workshop_service
from app.schema.workshop import WorkshopStaffRegisterRequest, WorkshopStaffRegisterResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest):
    return await auth_service.register(data)


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(data: VerifyOtpRequest):
    return await auth_service.verify_otp(data)


@router.post("/resend-otp", response_model=MessageResponse)
async def resend_otp(data: ResendOtpRequest):
    return await auth_service.resend_otp(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    return await auth_service.login(data)


@router.post("/oauth/google", response_model=TokenResponse)
async def oauth_google(data: OAuthLoginRequest):
    return await auth_service.oauth_login(data)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(data: ForgotPasswordRequest):
    return await auth_service.forgot_password(data)


@router.post("/verify-reset-code", response_model=VerifyResetCodeResponse)
async def verify_reset_code(data: VerifyResetCodeRequest):
    return await auth_service.verify_reset_code(data)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest):
    return await auth_service.reset_password(data)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(data: RefreshRequest):
    return await auth_service.refresh(data)


@router.post("/logout", response_model=MessageResponse)
async def logout(data: LogoutRequest):
    return await auth_service.logout(data)


@router.post("/register-workshop", response_model=WorkshopStaffRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_workshop_staff(data: WorkshopStaffRegisterRequest):
    return await workshop_service.register_workshop_staff(data)