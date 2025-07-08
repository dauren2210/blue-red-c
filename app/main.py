import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api.endpoints import health, streaming, voice_call, session
from app.services.knowledge_graph_processor import build_indices_and_constraints

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await build_indices_and_constraints()
    yield
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_event_handler("startup", connect_to_mongo)
# app.add_event_handler("startup", build_indices_and_constraints)
# app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(health.router, tags=["health"])
app.include_router(streaming.router, tags=["streaming"])
app.include_router(voice_call.router, tags=["voice_call"]) 
app.include_router(session.router, tags=["session"]) 