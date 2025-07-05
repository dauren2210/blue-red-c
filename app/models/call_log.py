from typing import Optional
from pydantic import BaseModel
from .common import MongoBaseModel, PyObjectId

class CallLog(MongoBaseModel):
    session_id: PyObjectId
    supplier_id: PyObjectId
    twilio_sid: Optional[str] = None
    status: str  # e.g., queued, ringing, in-progress, completed, failed
    details: Optional[dict] = None

class CallLogCreate(BaseModel):
    session_id: PyObjectId
    supplier_id: PyObjectId
    twilio_sid: Optional[str] = None
    status: str
    details: Optional[dict] = None 