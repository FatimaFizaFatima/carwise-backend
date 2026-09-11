from datetime import timedelta, datetime, timezone
from app.unit_of_work import UnitOfWork
from app.core.securtiy import hash_password, verify_password, create_access_token, create_refresh_token, create_reset_token, decode_reset_token, decode_token
from app.core.exceptions import AppException
from app.schema.auth import RegisterRequest, RegisterResponse, VerifyOtpRequest, TokenResponse, LoginRequest, ForgotPasswordRequest, ForgotPasswordResponse, VerifyResetCodeRequest, VerifyResetCodeResponse, MessageResponse, ResetPasswordRequest, ResendOtpRequest, LogoutRequest, RefreshRequest, RefreshResponse, OAuthLoginRequest
from app.models.user_models import User
from app.models.otp_code import OtpCode
from app.models.social_account import SocialAccount
from app.utils.emails import send_otp_email
from app.utils.otp import generate_otp
from app.models.refresh_token import RefreshToken
from app.utils.token_hash import hash_token
from app.core.config import settings
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60

async def register(data : RegisterRequest) -> RegisterResponse:
    async with UnitOfWork() as uow:
        if await uow.users.exist_by_user_email_or_phone(data.email, data.phone):
            raise AppException("Email or phone already exist", status_code=409)

        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password)
        )

        uow.users.add(user)

        await uow.session.flush()

        code = generate_otp()

        otp = OtpCode(
        user_id=user.id,
        code_hash=hash_password(code),
        purpose="signup_verify",
        channel="email",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
)

        uow.otp_codes.add(otp)
        await uow.commit()

        await send_otp_email(user.email, code, "signup_verify")

        return RegisterResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone
        )


async def _issue_tokens(user: User, uow: UnitOfWork) -> TokenResponse:
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    uow.refresh_tokens.add(refresh_row)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

async def verify_otp(data : VerifyOtpRequest) -> TokenResponse:
    async with UnitOfWork() as uow:

        user = await uow.users.get_user_by_email(data.email)
        if user is None:
            raise AppException("Invalid email", status_code=404)

        otp = await uow.otp_codes.get_latest_active(user.id, "signup_verify")
        if otp is None:
            raise AppException("No OTP has found. Please request a new code.", status_code=400)

        if otp.expires_at < datetime.now(timezone.utc):
            raise AppException("OTP has expired. Please request a new code.", status_code=400)

        if otp.attempt_count >= MAX_OTP_ATTEMPTS:
            raise AppException("Too much attempts. Please request a new code.", status_code=429)

        if not verify_password(data.otp, otp.code_hash):
            await uow.otp_codes.update(otp, {"attempt_count": otp.attempt_count + 1})
            await uow.commit()
            raise AppException("Invalid OTP", status_code=400)

        await uow.otp_codes.update(otp, {"consumed_at": datetime.now(timezone.utc)})
        await uow.users.update(user, {"email_verified": True})


        tokens = await _issue_tokens(user, uow)

        await uow.commit()
        return tokens


async def login(data : LoginRequest) -> TokenResponse:
    async with UnitOfWork() as uow:

        user = await uow.users.get_user_by_email(data.email)

        if user is None or user.password_hash is None or not verify_password(data.password, user.password_hash):
            raise AppException("Invalid email or password", status_code=401)

        if not user.email_verified:
            raise AppException("Please verify your email before logging in.", status_code=403)

        tokens = await _issue_tokens(user, uow)
        await uow.commit()
        return tokens


async def forgot_password(data: ForgotPasswordRequest) -> ForgotPasswordResponse:
    async with UnitOfWork() as uow:
        user = await uow.users.get_user_by_identifier(data.identifier)

        if user is not None:
            code = generate_otp()
            otp = OtpCode(
                user_id=user.id,
                code_hash=hash_password(code),
                purpose="reset_password",
                channel="email",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
            )
            uow.otp_codes.add(otp)
            await uow.commit()
            await send_otp_email(user.email, code, "reset_password")

        return ForgotPasswordResponse()    

async def verify_reset_code(data: VerifyResetCodeRequest) -> VerifyResetCodeResponse:
    async with UnitOfWork() as uow:
        user = await uow.users.get_user_by_identifier(data.identifier)
        if user is None:
            raise AppException("Invalid code", status_code=400)

        otp = await uow.otp_codes.get_latest_active(user.id, "reset_password")
        if otp is None:
            raise AppException("Invalid code", status_code=400)

        if otp.expires_at < datetime.now(timezone.utc):
            raise AppException("Code has expired. Please request a new one.", status_code=400)

        if otp.attempt_count >= MAX_OTP_ATTEMPTS:
            raise AppException("Too many attempts. Please request a new code.", status_code=429)

        if not verify_password(data.otp, otp.code_hash):
            await uow.otp_codes.update(otp, {"attempt_count": otp.attempt_count + 1})
            await uow.commit()
            raise AppException("Invalid code", status_code=400)

        await uow.otp_codes.update(otp, {"consumed_at": datetime.now(timezone.utc)})
        await uow.commit()

        reset_token = create_reset_token(user.id)
        return VerifyResetCodeResponse(reset_token=reset_token)


async def reset_password(data: ResetPasswordRequest) -> MessageResponse:
    async with UnitOfWork() as uow:
        user_id = decode_reset_token(data.reset_token)
        user = await uow.users.get_by_id(user_id)
        if user is None:
            raise AppException("Invalid reset token", status_code=401)

        await uow.users.update(user, {"password_hash": hash_password(data.new_password)})

        tokens = await uow.refresh_tokens.get_by_active_user(user.id)
        for token in tokens:
            token.revoked_at = datetime.now(timezone.utc)

        await uow.commit()
        return MessageResponse(message="Password updated successfully. Please log in again.")



async def resend_otp(data: ResendOtpRequest) -> MessageResponse:
    async with UnitOfWork() as uow:
        user = await uow.users.get_user_by_email(data.email)
        if user is None:
            raise AppException("Invalid phone number", status_code=404)

        last_otp = await uow.otp_codes.get_latest_active(user.id, "signup_verify")
        if last_otp is not None:
            seconds_since = (datetime.now(timezone.utc) - last_otp.created_at).total_seconds()
            if seconds_since < OTP_RESEND_COOLDOWN_SECONDS:
                wait = int(OTP_RESEND_COOLDOWN_SECONDS - seconds_since)
                raise AppException(f"Please wait {wait} seconds before requesting a new code.", status_code=429)

        code = generate_otp()
        new_otp = OtpCode(
            user_id=user.id,
            code_hash=hash_password(code),
            purpose="signup_verify",
            channel="email",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
        )
        uow.otp_codes.add(new_otp)
        await uow.commit()

        await send_otp_email(user.email, code, "signup_verify")
        return MessageResponse(message="A new OTP has been sent.")


async def refresh(data: RefreshRequest) -> RefreshResponse:
    async with UnitOfWork() as uow:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise AppException("Invalid token type", status_code=401)
        user_id = int(payload["sub"])

        token_hash = hash_token(data.refresh_token)
        token_row = await uow.refresh_tokens.get_by_token_hash(token_hash)

        if token_row is None or token_row.revoked_at is not None:
            raise AppException("Invalid or revoked refresh token", status_code=401)

        if token_row.expires_at < datetime.now(timezone.utc):
            raise AppException("Refresh token has expired", status_code=401)

        access_token = create_access_token({"sub": str(user_id)})
        return RefreshResponse(access_token=access_token)


async def logout(data: LogoutRequest) -> MessageResponse:
    async with UnitOfWork() as uow:
        token_hash = hash_token(data.refresh_token)
        token_row = await uow.refresh_tokens.get_by_token_hash(token_hash)

        if token_row is None or token_row.revoked_at is not None:
            raise AppException("Invalid refresh token", status_code=401)

        await uow.refresh_tokens.update(token_row, {"revoked_at": datetime.now(timezone.utc)})
        await uow.commit()
        return MessageResponse(message="Logged out successfully.")    


async def verify_google_token(provider_token: str) -> dict:
    try:
        payload = google_id_token.verify_oauth2_token(
            provider_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise AppException("Invalid Google token", status_code=401)

    return {
        "provider_user_id": payload["sub"],
        "email": payload["email"],
        "full_name": payload.get("name", ""),
    }


async def oauth_login(data: OAuthLoginRequest) -> TokenResponse:
    google_data = await verify_google_token(data.provider_token)

    async with UnitOfWork() as uow:
        social = await uow.social_accounts.get_by_provider("google", google_data["provider_user_id"])

        if social is not None:
            user = await uow.users.get_by_id(social.user_id)
            tokens = await _issue_tokens(user, uow)
            await uow.commit()
            return tokens

        existing_user = await uow.users.get_user_by_email(google_data["email"])
        if existing_user is not None:
            raise AppException(
                "This email is already registered. Please log in with your password.",
                status_code=409,
            )

        new_user = User(
            full_name=google_data["full_name"],
            email=google_data["email"],
            phone=None,
            password_hash=None,
            email_verified=True,
        )
        uow.users.add(new_user)
        await uow.session.flush()

        social_row = SocialAccount(
            user_id=new_user.id,
            provider="google",
            provider_user_id=google_data["provider_user_id"],
        )
        uow.social_accounts.add(social_row)

        tokens = await _issue_tokens(new_user, uow)
        await uow.commit()
        return tokens    
    
    