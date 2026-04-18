from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from app.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASS,
    MAIL_FROM=settings.EMAIL_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_otp_email(email: EmailStr, otp: str):
    message = MessageSchema(
        subject="Your OTP Verification Code",
        recipients=[email],
        body=f"Your verification code is: {otp}. It will expire in 5 minutes.",
        subtype=MessageType.plain
    )

    fm = FastMail(conf)
    await fm.send_message(message)

async def send_reset_password_email(email: EmailStr, otp: str):
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=f"Your password reset code is: {otp}. It will expire in 5 minutes.",
        subtype=MessageType.plain
    )

    fm = FastMail(conf)
    await fm.send_message(message)
