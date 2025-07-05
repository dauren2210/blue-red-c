from typing import Optional
from pydantic import BaseModel, Field
from .common import MongoBaseModel

class Supplier(MongoBaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    call_status: str = Field(default="pending")  # e.g., pending, in_progress, completed, failed
    response_data: Optional[dict] = None

class SupplierCreate(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None

class SupplierUpdate(BaseModel):
    call_status: Optional[str]
    response_data: Optional[dict] 