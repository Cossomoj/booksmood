from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    app_name: str = "AudioFlow"
    debug: bool = True
    
    # Telegram
    bot_token: str = "8045700099:AAGCARHl1gc2sO5cCvoC3LlIHFC5hC04znY"
    telegram_bot_username: str = "AudioFlowBot"
    
    # Security
    secret_key: str = "audioflow-secret-key-2024-very-secure-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days
    
    # Database
    database_url: str = "sqlite:///./audioflow.db"
    
    # CORS
    cors_origins: List[str] = ["https://web.telegram.org", "http://localhost:3000"]
    
    # Files
    upload_dir: str = "./app/static/uploads"
    max_file_size: int = 104857600  # 100MB
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Игнорируем лишние переменные

settings = Settings() 