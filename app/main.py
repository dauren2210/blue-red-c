from fastapi import FastAPI
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api.endpoints import health, streaming
from app.api.endpoints.voice_call import router as twilio_router

app = FastAPI()

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(health.router, tags=["health"])
app.include_router(streaming.router, tags=["streaming"])
app.include_router(twilio_router) 