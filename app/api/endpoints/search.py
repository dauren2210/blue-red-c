from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.models import (
    SearchQuery, SearchResponse, 
    SupplierSearchRequest, SupplierSearchResponse,
    ProductSearchRequest, ProductSearchResponse,
    ProductData, ProductCreate, ProductUpdate
)
from app.services.search_orchestrator import SearchOrchestrator
from app.services.location_service import LocationService
from app.db.mongodb import get_database
from bson import ObjectId

router = APIRouter()
search_orchestrator = SearchOrchestrator()
location_service = LocationService()

@router.post("/search", response_model=SearchResponse)
async def search(query: SearchQuery):
    """
    Выполняет поисковый запрос с автоматическим определением локации
    """
    try:
        # Определяем параметры локации если указана
        location_params = None
        if query.location:
            location_params = location_service.detect_country_and_language(query.location)
        
        # Выполняем поиск
        result = await search_orchestrator.serp_service.search(
            query.query,
            search_type=query.search_type,
            location=query.location,
            max_results=query.max_results,
            **query.additional_params
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.post("/search/suppliers", response_model=SupplierSearchResponse)
async def search_suppliers(request: SupplierSearchRequest):
    """
    Поиск поставщиков с автоматическим определением локации из БД
    """
    try:
        result = await search_orchestrator.search_suppliers(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supplier search error: {str(e)}")

@router.post("/search/products/{product_id}", response_model=ProductSearchResponse)
async def search_by_product(product_id: str, request: ProductSearchRequest):
    """
    Поиск поставщиков на основе данных продукта из БД
    """
    try:
        # Устанавливаем product_id из URL
        request.product_id = product_id
        result = await search_orchestrator.search_by_product_data(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product search error: {str(e)}")

@router.post("/search/location", response_model=dict)
async def detect_location(location: str):
    """
    Определяет страну и язык на основе локации
    """
    try:
        location_info = location_service.detect_country_and_language(location)
        return {
            "location": location,
            "country_code": location_info["country_code"],
            "language": location_info["language"],
            "primary_language": location_info["primary_language"],
            "search_languages": location_service.get_search_languages(location_info["country_code"]),
            "is_cis_country": location_service.is_cis_country(location_info["country_code"]),
            "local_sources": location_service.get_local_sources(location_info["country_code"]),
            "trusted_sources": location_service.get_trusted_sources_by_region(location_info["country_code"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Location detection error: {str(e)}")

@router.get("/search/location/examples")
async def get_location_examples():
    """
    Возвращает примеры локаций для тестирования
    """
    examples = [
        {
            "location": "Алматы, Казахстан",
            "expected_country": "kz",
            "expected_language": "ru"
        },
        {
            "location": "Москва, Россия",
            "expected_country": "ru", 
            "expected_language": "ru"
        },
        {
            "location": "Киев, Украина",
            "expected_country": "ua",
            "expected_language": "uk"
        },
        {
            "location": "Ташкент, Узбекистан",
            "expected_country": "uz",
            "expected_language": "uz"
        },
        {
            "location": "Бишкек, Кыргызстан",
            "expected_country": "kg",
            "expected_language": "ky"
        },
        {
            "location": "Berlin, Germany",
            "expected_country": "de",
            "expected_language": "de"
        },
        {
            "location": "Paris, France",
            "expected_country": "fr",
            "expected_language": "fr"
        },
        {
            "location": "New York, USA",
            "expected_country": "us",
            "expected_language": "en"
        },
        {
            "location": "Beijing, China",
            "expected_country": "cn",
            "expected_language": "zh"
        }
    ]
    return {"examples": examples}

@router.post("/search/multilingual")
async def multilingual_search(query: str, location: str, max_results: int = 10):
    """
    Выполняет многоязычный поиск на основе локации
    """
    try:
        # Создаем временный ProductData для многоязычного поиска
        product_data = ProductData(
            product_name="test",
            amount="",
            date_time=None,
            location=location
        )
        
        results = await search_orchestrator.serp_service.multilingual_search(
            query,
            product_data,
            max_results=max_results
        )
        
        return {
            "query": query,
            "location": location,
            "results": [result.dict() for result in results],
            "total_languages": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multilingual search error: {str(e)}")

# CRUD операции для продуктов
@router.post("/products", response_model=dict)
async def create_product(product: ProductCreate):
    """
    Создает новый продукт в базе данных
    """
    try:
        db = get_database()
        collection = db.products
        
        product_data = product.dict()
        result = await collection.insert_one(product_data)
        
        return {
            "id": str(result.inserted_id),
            "message": "Product created successfully",
            "product": product_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")

@router.get("/products/{product_id}", response_model=ProductData)
async def get_product(product_id: str):
    """
    Получает продукт по ID
    """
    try:
        db = get_database()
        collection = db.products
        
        product_doc = await collection.find_one({"_id": ObjectId(product_id)})
        if not product_doc:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return ProductData(
            product_name=product_doc.get("product_name", ""),
            amount=product_doc.get("amount", ""),
            date_time=product_doc.get("date_time"),
            location=product_doc.get("location", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting product: {str(e)}")

@router.get("/products", response_model=List[ProductData])
async def get_products(skip: int = 0, limit: int = 10):
    """
    Получает список продуктов с пагинацией
    """
    try:
        db = get_database()
        collection = db.products
        
        cursor = collection.find().skip(skip).limit(limit)
        products = []
        
        async for doc in cursor:
            products.append(ProductData(
                product_name=doc.get("product_name", ""),
                amount=doc.get("amount", ""),
                date_time=doc.get("date_time"),
                location=doc.get("location", "")
            ))
        
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting products: {str(e)}")

@router.put("/products/{product_id}", response_model=dict)
async def update_product(product_id: str, product: ProductUpdate):
    """
    Обновляет продукт
    """
    try:
        db = get_database()
        collection = db.products
        
        update_data = {k: v for k, v in product.dict().items() if v is not None}
        
        result = await collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "id": product_id,
            "message": "Product updated successfully",
            "updated_fields": list(update_data.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")

@router.delete("/products/{product_id}", response_model=dict)
async def delete_product(product_id: str):
    """
    Удаляет продукт
    """
    try:
        db = get_database()
        collection = db.products
        
        result = await collection.delete_one({"_id": ObjectId(product_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "id": product_id,
            "message": "Product deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

@router.post("/products/upload", response_model=dict)
async def upload_products(products: List[ProductCreate]):
    """
    Загружает несколько продуктов одновременно
    """
    try:
        db = get_database()
        collection = db.products
        
        product_data_list = [product.dict() for product in products]
        result = await collection.insert_many(product_data_list)
        
        return {
            "message": f"Successfully uploaded {len(result.inserted_ids)} products",
            "inserted_ids": [str(id) for id in result.inserted_ids]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading products: {str(e)}")

@router.get("/search/analytics")
async def get_search_analytics():
    """
    Возвращает аналитику поисковых запросов
    """
    try:
        db = get_database()
        
        # Статистика по странам
        country_stats = await db.search_sessions.aggregate([
            {"$group": {
                "_id": "$location_params.country_code",
                "count": {"$sum": 1},
                "avg_suppliers": {"$avg": "$total_suppliers"}
            }},
            {"$sort": {"count": -1}}
        ]).to_list(length=10)
        
        # Статистика по языкам
        language_stats = await db.search_sessions.aggregate([
            {"$group": {
                "_id": "$location_params.language",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]).to_list(length=10)
        
        # Общая статистика
        total_searches = await db.search_sessions.count_documents({})
        total_products = await db.products.count_documents({})
        
        return {
            "total_searches": total_searches,
            "total_products": total_products,
            "country_statistics": country_stats,
            "language_statistics": language_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}") 