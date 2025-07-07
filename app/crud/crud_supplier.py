from typing import List
from bson import ObjectId
from app.db.mongodb import get_database
from app.models.supplier import Supplier, SupplierCreate, SupplierUpdate

COLLECTION_NAME = "suppliers"

async def create_supplier(supplier: SupplierCreate) -> Supplier:
    db = await get_database()
    supplier_dict = supplier.dict()
    result = await db[COLLECTION_NAME].insert_one(supplier_dict)
    created_supplier = await db[COLLECTION_NAME].find_one({"_id": result.inserted_id})
    return Supplier(**created_supplier, id=result.inserted_id)

async def get_supplier(supplier_id: str) -> Supplier:
    db = await get_database()
    supplier = await db[COLLECTION_NAME].find_one({"_id": ObjectId(supplier_id)})
    if supplier:
        return Supplier(**supplier, id=supplier["_id"])

async def get_all_suppliers() -> List[Supplier]:
    db = await get_database()
    suppliers = []
    async for supplier in db[COLLECTION_NAME].find():
        suppliers.append(Supplier(**supplier, id=supplier["_id"]))
    return suppliers

async def update_supplier(supplier_id: str, supplier_update: SupplierUpdate) -> Supplier:
    db = await get_database()
    update_data = {k: v for k, v in supplier_update.dict().items() if v is not None}
    
    if len(update_data) >= 1:
        await db[COLLECTION_NAME].update_one(
            {"_id": ObjectId(supplier_id)}, {"$set": update_data}
        )
    
    updated_supplier = await get_supplier(supplier_id)
    return updated_supplier

async def delete_supplier(supplier_id: str):
    db = await get_database()
    await db[COLLECTION_NAME].delete_one({"_id": ObjectId(supplier_id)})

async def get_supplier_by_phone(phone: str) -> Supplier:
    db = await get_database()
    supplier = await db[COLLECTION_NAME].find_one({"phone_numbers": {"$in": [phone]}})
    if supplier:
        return Supplier(**supplier, id=supplier["_id"])
    return None 