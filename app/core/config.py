import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "blue-red-c")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")

    # Twilio    
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER")

    # Ngrok
    PORT: int = int(os.getenv("PORT", "8080"))
    DOMAIN: str = os.getenv("NGROK_URL")
    WS_URL: str = f"wss://{DOMAIN}/ws/conversation" if DOMAIN else None

    class Config:
        case_sensitive = True

settings = Settings() 