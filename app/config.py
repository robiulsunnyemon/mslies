from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    GOOGLE_API_KEY: str
    ENVIRONMENT: str = "development"
    CLOUDINARY_URL: str

    class Config:
        env_file = ".env"

settings = Settings()

import cloudinary
import cloudinary.uploader
import cloudinary.api
# cloudinary automatically configures itself if CLOUDINARY_URL is in the environment

