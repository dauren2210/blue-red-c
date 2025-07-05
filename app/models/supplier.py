from typing import Optional, List
from pydantic import BaseModel, Field
from .common import MongoBaseModel

class Supplier(MongoBaseModel):
    name: str
    phone_numbers: List[str]
    emails: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    call_status: str = Field(default="pending")  # e.g., pending, in_progress, completed, failed
    response_data: Optional[dict] = None

class SupplierCreate(BaseModel):
    name: str
    phone_numbers: List[str]
    emails: Optional[List[str]] = None
    locations: Optional[List[str]] = None

class SupplierUpdate(BaseModel):
    phone_numbers: Optional[List[str]] = None
    emails: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    call_status: Optional[str] = None
    response_data: Optional[dict] = None 