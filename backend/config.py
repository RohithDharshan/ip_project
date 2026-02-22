import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "Agentic AI Workflow Automation"
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite+aiosqlite:///./workflow.db"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@psgai.edu.in"

    OPENAI_API_KEY: str = ""
    ERP_BASE_URL: str = "https://erp.iics.ac.in/api"
    ERP_API_KEY: str = ""

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
