from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .common import MongoBaseModel
from .supplier import Supplier, SupplierCreate

class Session(MongoBaseModel):
    suppliers: List[Supplier] = []
    status: str = Field(default="created")  # e.g., created, in_progress, completed
    structured_request: Optional[Dict[str, Any]] = None
    full_transcript: Optional[str] = None

class SessionCreate(BaseModel):
    suppliers: List[SupplierCreate] = []

class SessionUpdate(BaseModel):
    status: Optional[str] = None
    suppliers: Optional[List[Supplier]] = None
    structured_request: Optional[Dict[str, Any]] = None
    full_transcript: Optional[str] = None 