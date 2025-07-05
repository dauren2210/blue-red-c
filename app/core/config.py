import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "blue-red-c")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")
    SOME_API_KEY: str = os.getenv("SOME_API_KEY", "your_api_key_here")
    
    # Serp API configuration
    SERP_API_KEY: str = os.getenv("SERP_API_KEY", "3919c67df490a0646347a57d34542846a7199acead361915c9d071523ac3f7b5")
    SERP_ENGINE: str = os.getenv("SERP_ENGINE", "google")
    
    # Search configuration
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "3"))
    SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "60"))

    class Config:
        case_sensitive = True

settings = Settings() 