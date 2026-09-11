import aiosmtplib
from email.message import EmailMessage
from app.core.config import settings


async def send_otp_email(to_email: str, code: str, purpose: str) -> None:
    subject = "Your CarWise verification code" if purpose == "signup_verify" else "Your CarWise password reset code"

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(
        f"Your CarWise verification code is: {code}\n\n"
        f"This code expires in 10 minutes. If you didn't request this, you can ignore this email."
    )

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )