import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.db.mongodb import get_database
from app.models import ProductData, DatabaseProductRecord, ProductSearchParameters

class DatabaseService:
    """Сервис для работы с данными продуктов из базы данных"""
    
    def __init__(self):
        self.db = get_database()
    
    async def get_product_by_id(self, product_id: str) -> Optional[DatabaseProductRecord]:
        """Получает продукт по ID из базы данных"""
        try:
            document = await self.db.products.find_one({"_id": product_id})
            if document:
                return DatabaseProductRecord(**document)
            return None
        except Exception as e:
            print(f"Error getting product by ID {product_id}: {e}")
            return None
    
    async def get_products_by_ids(self, product_ids: List[str]) -> List[DatabaseProductRecord]:
        """Получает несколько продуктов по ID"""
        try:
            cursor = self.db.products.find({"_id": {"$in": product_ids}})
            documents = await cursor.to_list(length=len(product_ids))
            
            products = []
            for doc in documents:
                try:
                    products.append(DatabaseProductRecord(**doc))
                except Exception as e:
                    print(f"Error parsing product document: {e}")
                    continue
            
            return products
        except Exception as e:
            print(f"Error getting products by IDs: {e}")
            return []
    
    async def get_all_active_products(self, limit: int = 100) -> List[DatabaseProductRecord]:
        """Получает все активные продукты"""
        try:
            cursor = self.db.products.find({"status": "active"}).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            products = []
            for doc in documents:
                try:
                    products.append(DatabaseProductRecord(**doc))
                except Exception as e:
                    print(f"Error parsing product document: {e}")
                    continue
            
            return products
        except Exception as e:
            print(f"Error getting all active products: {e}")
            return []
    
    async def search_products_by_name(self, product_name: str, limit: int = 20) -> List[DatabaseProductRecord]:
        """Поиск продуктов по названию"""
        try:
            # Используем текстовый поиск MongoDB
            cursor = self.db.products.find({
                "$text": {"$search": product_name},
                "status": "active"
            }).limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            products = []
            for doc in documents:
                try:
                    products.append(DatabaseProductRecord(**doc))
                except Exception as e:
                    print(f"Error parsing product document: {e}")
                    continue
            
            return products
        except Exception as e:
            print(f"Error searching products by name: {e}")
            return []
    
    async def parse_json_file(self, json_content: str) -> Optional[ProductData]:
        """Парсит JSON файл и извлекает данные продукта"""
        try:
            data = json.loads(json_content)
            
            # Поддерживаем различные форматы JSON
            if isinstance(data, dict):
                # Прямой формат
                if "product name" in data or "product_name" in data:
                    return ProductData(
                        product_name=data.get("product name") or data.get("product_name"),
                        amount=data.get("amount"),
                        date_and_time=data.get("date and time") or data.get("date_and_time"),
                        location=data.get("location")
                    )
                
                # Формат с вложенностью
                elif "data" in data:
                    data_inner = data["data"]
                    return ProductData(
                        product_name=data_inner.get("product name") or data_inner.get("product_name"),
                        amount=data_inner.get("amount"),
                        date_and_time=data_inner.get("date and time") or data_inner.get("date_and_time"),
                        location=data_inner.get("location")
                    )
                
                # Формат массива
                elif isinstance(data.get("products"), list) and len(data["products"]) > 0:
                    first_product = data["products"][0]
                    return ProductData(
                        product_name=first_product.get("product name") or first_product.get("product_name"),
                        amount=first_product.get("amount"),
                        date_and_time=first_product.get("date and time") or first_product.get("date_and_time"),
                        location=first_product.get("location")
                    )
            
            return None
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None
        except Exception as e:
            print(f"Error extracting product data: {e}")
            return None
    
    async def create_product_from_json(
        self, 
        filename: str, 
        json_content: str
    ) -> Optional[DatabaseProductRecord]:
        """Создает запись продукта из JSON файла"""
        try:
            product_data = await self.parse_json_file(json_content)
            if not product_data:
                return None
            
            # Генерируем ID
            import uuid
            product_id = str(uuid.uuid4())
            
            # Создаем запись
            record = DatabaseProductRecord(
                id=product_id,
                filename=filename,
                data=product_data,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                status="active"
            )
            
            # Сохраняем в базу данных
            await self.db.products.insert_one(record.dict())
            
            return record
            
        except Exception as e:
            print(f"Error creating product from JSON: {e}")
            return None
    
    async def update_product_data(
        self, 
        product_id: str, 
        product_data: ProductData
    ) -> bool:
        """Обновляет данные продукта"""
        try:
            result = await self.db.products.update_one(
                {"_id": product_id},
                {
                    "$set": {
                        "data": product_data.dict(),
                        "updated_at": datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating product data: {e}")
            return False
    
    async def delete_product(self, product_id: str) -> bool:
        """Удаляет продукт (мягкое удаление)"""
        try:
            result = await self.db.products.update_one(
                {"_id": product_id},
                {
                    "$set": {
                        "status": "deleted",
                        "updated_at": datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error deleting product: {e}")
            return False
    
    async def get_products_by_location(self, location: str, limit: int = 20) -> List[DatabaseProductRecord]:
        """Получает продукты по локации"""
        try:
            cursor = self.db.products.find({
                "data.location": {"$regex": location, "$options": "i"},
                "status": "active"
            }).limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            products = []
            for doc in documents:
                try:
                    products.append(DatabaseProductRecord(**doc))
                except Exception as e:
                    print(f"Error parsing product document: {e}")
                    continue
            
            return products
        except Exception as e:
            print(f"Error getting products by location: {e}")
            return []
    
    async def get_products_by_date_range(
        self, 
        start_date: str, 
        end_date: str, 
        limit: int = 20
    ) -> List[DatabaseProductRecord]:
        """Получает продукты по диапазону дат"""
        try:
            cursor = self.db.products.find({
                "data.date_and_time": {
                    "$gte": start_date,
                    "$lte": end_date
                },
                "status": "active"
            }).limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            products = []
            for doc in documents:
                try:
                    products.append(DatabaseProductRecord(**doc))
                except Exception as e:
                    print(f"Error parsing product document: {e}")
                    continue
            
            return products
        except Exception as e:
            print(f"Error getting products by date range: {e}")
            return []
    
    async def get_product_statistics(self) -> Dict[str, Any]:
        """Получает статистику по продуктам"""
        try:
            # Общее количество продуктов
            total_products = await self.db.products.count_documents({"status": "active"})
            
            # Количество по локациям
            pipeline = [
                {"$match": {"status": "active"}},
                {"$group": {"_id": "$data.location", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            location_stats = await self.db.products.aggregate(pipeline).to_list(10)
            
            # Популярные названия продуктов
            pipeline = [
                {"$match": {"status": "active"}},
                {"$group": {"_id": "$data.product_name", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            product_name_stats = await self.db.products.aggregate(pipeline).to_list(10)
            
            return {
                "total_products": total_products,
                "location_statistics": location_stats,
                "product_name_statistics": product_name_stats
            }
            
        except Exception as e:
            print(f"Error getting product statistics: {e}")
            return {
                "total_products": 0,
                "location_statistics": [],
                "product_name_statistics": []
            } 