from typing import List
from bson import ObjectId
from app.db.mongodb import get_database
from app.models.call_log import CallLog, CallLogCreate

COLLECTION_NAME = "call_logs"

async def create_call_log(call_log: CallLogCreate) -> CallLog:
    db = await get_database()
    call_log_dict = call_log.dict()
    result = await db[COLLECTION_NAME].insert_one(call_log_dict)
    created_log = await db[COLLECTION_NAME].find_one({"_id": result.inserted_id})
    return CallLog(**created_log, id=result.inserted_id)

async def get_call_logs_for_session(session_id: str) -> List[CallLog]:
    db = await get_database()
    logs = []
    async for log in db[COLLECTION_NAME].find({"session_id": ObjectId(session_id)}):
        logs.append(CallLog(**log, id=log["_id"]))
    return logs 