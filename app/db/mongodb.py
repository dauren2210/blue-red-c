import motor.motor_asyncio
from app.core.config import settings

# MongoDB connection
client = None
database = None

async def connect_to_mongo():
    """Подключение к MongoDB"""
    global client, database
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DB_NAME]
    print("Connected to MongoDB")

async def close_mongo_connection():
    """Закрытие соединения с MongoDB"""
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")

def get_database():
    """Получение экземпляра базы данных"""
    return database 