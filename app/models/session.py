from typing import List, Optional
from pydantic import BaseModel, Field
from .common import MongoBaseModel
from .supplier import Supplier, SupplierCreate

class Session(MongoBaseModel):
    customer_request: str
    suppliers: List[Supplier] = []
    status: str = Field(default="created")  # e.g., created, in_progress, completed

class SessionCreate(BaseModel):
    customer_request: str
    suppliers: List[SupplierCreate] = []

class SessionUpdate(BaseModel):
    status: Optional[str]
    suppliers: Optional[List[Supplier]] 