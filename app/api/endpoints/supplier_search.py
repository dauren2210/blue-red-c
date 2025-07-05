from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional
from app.models import (
    SupplierSearchRequest, 
    SupplierSearchResponse
)
from app.services.search_orchestrator import SearchOrchestrator
from app.services.database_service import DatabaseService
from app.core.config import settings

router = APIRouter(prefix="/supplier-search", tags=["supplier-search"])

# Создаем экземпляры сервисов
orchestrator = SearchOrchestrator()
db_service = DatabaseService()

@router.post("/search", response_model=SupplierSearchResponse)
async def search_suppliers(request: SupplierSearchRequest):
    """
    Поиск поставщиков с использованием search_query для генерации запросов
    """
    try:
        result = await orchestrator.search_suppliers(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supplier search failed: {str(e)}")

@router.post("/search-from-db/{product_id}", response_model=SupplierSearchResponse)
async def search_suppliers_from_db(
    product_id: str,
    target_location: str = "Almaty, Kazakhstan",
    delivery_date: Optional[str] = None,
    supplier_type: Optional[str] = None
):
    """
    Поиск поставщиков на основе данных продукта из базы данных
    """
    try:
        # Создаем ProductSearchRequest
        from app.models import ProductSearchRequest
        
        request = ProductSearchRequest(
            product_id=product_id,
            max_results=10
        )
        
        result = await orchestrator.search_by_product_data(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search from DB failed: {str(e)}")

# Эндпоинты для работы с продуктами в БД
@router.get("/products", response_model=List[dict])
async def get_products(limit: int = 20):
    """
    Получает список всех активных продуктов из БД
    """
    try:
        products = await db_service.get_all_active_products(limit)
        return [product.dict() for product in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get products: {str(e)}")

@router.get("/products/{product_id}", response_model=dict)
async def get_product(product_id: str):
    """
    Получает продукт по ID из БД
    """
    try:
        product = await db_service.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")

@router.post("/products/upload", response_model=dict)
async def upload_product_json(
    file: UploadFile = File(...)
):
    """
    Загружает JSON файл с данными продукта в БД
    """
    try:
        # Читаем содержимое файла
        json_content = await file.read()
        json_content_str = json_content.decode('utf-8')
        
        # Создаем запись в БД
        product_record = await db_service.create_product_from_json(
            file.filename, 
            json_content_str
        )
        
        if not product_record:
            raise HTTPException(status_code=400, detail="Failed to parse JSON file")
        
        return {
            "message": "Product uploaded successfully",
            "product_id": product_record.id,
            "product_data": product_record.data.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/products/search/{product_name}", response_model=List[dict])
async def search_products_by_name(product_name: str, limit: int = 20):
    """
    Поиск продуктов по названию в БД
    """
    try:
        products = await db_service.search_products_by_name(product_name, limit)
        return [product.dict() for product in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product search failed: {str(e)}")

@router.get("/products/location/{location}", response_model=List[dict])
async def get_products_by_location(location: str, limit: int = 20):
    """
    Получает продукты по локации
    """
    try:
        products = await db_service.get_products_by_location(location, limit)
        return [product.dict() for product in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get products by location: {str(e)}")

@router.get("/products/date-range", response_model=List[dict])
async def get_products_by_date_range(
    start_date: str,
    end_date: str,
    limit: int = 20
):
    """
    Получает продукты по диапазону дат
    """
    try:
        products = await db_service.get_products_by_date_range(start_date, end_date, limit)
        return [product.dict() for product in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get products by date range: {str(e)}")

@router.get("/products/statistics", response_model=dict)
async def get_product_statistics():
    """
    Получает статистику по продуктам
    """
    try:
        stats = await db_service.get_product_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/health")
async def supplier_search_health():
    """
    Проверка состояния сервиса поиска поставщиков
    """
    try:
        return {
            "status": "healthy",
            "service": "supplier_search",
            "orchestrator": "SearchOrchestrator",
            "timestamp": "2024-01-15T10:00:00Z",
            "version": "1.0.0",
            "features": [
                "search_query_based_generation",
                "location_aware_search",
                "contact_page_focus",
                "multilingual_support"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/example-request")
async def get_example_request():
    """
    Возвращает пример запроса для поиска поставщиков
    """
    return {
        "search_query": "electronics supplier",
        "amount": "1000 units",
        "search_strategy": "direct",
        "max_results": 10,
        "search_type": "web",
        "target_location": "Almaty, Kazakhstan",
        "delivery_date": "2024-02-15",
        "required_services": ["catalog", "price_list", "contact_info"],
        "trusted_sources": ["alibaba.com", "globalsources.com"],
        "additional_keywords": ["wholesale", "manufacturer"]
    } 