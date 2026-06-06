"""
app/core/config.py — configurações centrais lidas do .env
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Twilio
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_number: str = "+19783818754"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    whisper_model: str = "whisper-1"

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # App
    app_env: str = "development"
    app_secret: str = "dev-secret"
    base_url: str = "http://localhost:8000"
    pdf_max_bytes: int = 3_145_728  # 3 MB

    # WhatsApp destino
    imatchy_whatsapp_number: str = "551151947349"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
