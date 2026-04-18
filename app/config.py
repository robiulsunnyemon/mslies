from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    GOOGLE_API_KEY: str
    ENVIRONMENT: str = "development"
    CLOUDINARY_URL: str

    # Auth Configuration
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email Configuration
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    EMAIL_FROM: str

    class Config:
        env_file = ".env"
        extra = "ignore" # Allow extra fields without crashing

settings = Settings()

import cloudinary
import cloudinary.uploader
import cloudinary.api
# cloudinary automatically configures itself if CLOUDINARY_URL is in the environment

