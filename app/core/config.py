import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "blue-red-c")
    SOME_API_KEY: str = os.getenv("SOME_API_KEY", "your_api_key_here")

    class Config:
        case_sensitive = True

settings = Settings() 