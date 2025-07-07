from typing import List
from bson import ObjectId
from app.db.mongodb import get_database
from app.models.session import Session, SessionCreate, SessionUpdate
from app.models.supplier import Supplier

COLLECTION_NAME = "sessions"

async def create_session(session: SessionCreate) -> Session:
    db = await get_database()
    
    suppliers = [Supplier(**s.dict()) for s in session.suppliers]
    session_to_insert = Session(
        suppliers=suppliers
    )
    
    session_dict = session_to_insert.dict(by_alias=True)
    session_dict.pop("id", None) # Remove id before insertion

    for i, supp in enumerate(session_dict["suppliers"]):
        session_dict["suppliers"][i].pop("id", None)


    result = await db[COLLECTION_NAME].insert_one(session_dict)
    created_session = await db[COLLECTION_NAME].find_one({"_id": result.inserted_id})
    return Session(**created_session, id=result.inserted_id)

async def get_session(session_id: str) -> Session:
    db = await get_database()
    session = await db[COLLECTION_NAME].find_one({"_id": ObjectId(session_id)})
    if session:
        return Session(**session, id=session["_id"])

async def get_all_sessions() -> List[Session]:
    db = await get_database()
    sessions = []
    async for session in db[COLLECTION_NAME].find():
        sessions.append(Session(**session, id=session["_id"]))
    return sessions

async def update_session(session_id: str, session_update: SessionUpdate) -> Session:
    db = await get_database()
    update_data = {k: v for k, v in session_update.dict(by_alias=True).items() if v is not None}
    
    if "suppliers" in update_data:
        update_data["suppliers"] = [s.dict(by_alias=True) for s in session_update.suppliers]

    if len(update_data) >= 1:
        await db[COLLECTION_NAME].update_one(
            {"_id": ObjectId(session_id)}, {"$set": update_data}
        )
    
    updated_session = await get_session(session_id)
    return updated_session 

async def get_last_session() -> Session:
    db = await get_database()
    session = await db[COLLECTION_NAME].find_one(sort=[("_id", -1)])
    if session:
        return Session(**session, id=session["_id"]) 
