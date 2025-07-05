from fastapi import FastAPI
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api.endpoints import health

app = FastAPI()

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(health.router, tags=["health"]) 