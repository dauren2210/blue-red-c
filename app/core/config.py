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
    SERP_API_KEY: str = os.getenv("SERP_API_KEY", "3964cda35df1b736b077e8ded6fd02b36f08ed77990e7853113ee96d26c8d962")
    SERP_ENGINE: str = os.getenv("SERP_ENGINE", "google")
    
    # Search configuration
    MAX_SEARCH_RESULTS: int = 5
    SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "60"))

    class Config:
        case_sensitive = True

settings = Settings() 