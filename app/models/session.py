from typing import List, Optional
from pydantic import BaseModel, Field
from .common import MongoBaseModel
from .supplier import Supplier, SupplierCreate

class Session(MongoBaseModel):
    customer_request: str
    product_name: str
    suppliers: List[Supplier] = []
    status: str = Field(default="created")  # e.g., created, in_progress, completed

class SessionCreate(BaseModel):
    customer_request: str
    product_name: str
    suppliers: List[SupplierCreate] = []

class SessionUpdate(BaseModel):
    customer_request: Optional[str] = None
    product_name: Optional[str] = None
    status: Optional[str] = None
    suppliers: Optional[List[Supplier]] = None 