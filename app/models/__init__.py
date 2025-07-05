from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SupplierType(str, Enum):
    """Типы поставщиков"""
    MANUFACTURER = "manufacturer"
    WHOLESALER = "wholesaler"
    DISTRIBUTOR = "distributor"
    LOGISTICS = "logistics"
    RAW_MATERIALS = "raw_materials"
    FOOD = "food"
    GOODS = "goods"

class SearchQuery(BaseModel):
    """Модель для поискового запроса"""
    query: str
    context: Optional[str] = None
    max_results: Optional[int] = 10
    search_type: Optional[str] = "web"

class SearchResult(BaseModel):
    """Модель для результата поиска"""
    title: str
    link: str
    snippet: str
    position: int
    source: Optional[str] = None
    timestamp: Optional[datetime] = None

class SearchResponse(BaseModel):
    """Модель для ответа поиска"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float
    engine: str

class SupplierData(BaseModel):
    """Модель данных поставщика"""
    id: Optional[str] = None
    product_name: str
    amount: Optional[str] = None
    date: Optional[str] = None
    location: Optional[str] = None

# Новые модели для работы с JSON данными из БД
class ProductData(BaseModel):
    """Модель данных продукта из JSON файла"""
    product_name: str
    amount: Optional[str] = None
    date_and_time: Optional[str] = None
    location: Optional[str] = None
    
    class Config:
        validate_by_name = True

class SupplierSearchRequest(BaseModel):
    """Модель запроса поиска поставщиков"""
    search_query: str
    product_id: Optional[str] = None
    product_data: Optional[ProductData] = None
    amount: Optional[str] = None
    search_strategy: str = "direct"
    max_results: int = 10
    search_type: str = "web"
    target_location: str = "Almaty, Kazakhstan"
    delivery_date: Optional[str] = None
    required_services: List[str] = []  # catalog, price_list, contact_info, etc.
    trusted_sources: List[str] = []  # alibaba.com, globalsources.com, etc.
    additional_keywords: List[str] = []
    
    class Config:
        validate_by_name = True

class GeneratedSearchQuery(BaseModel):
    """Модель сгенерированного поискового запроса"""
    original_request: SupplierSearchRequest
    generated_query: str
    search_strategy: str
    confidence_score: float
    reasoning: str
    suggested_filters: Dict[str, Any]

class LLMPrompt(BaseModel):
    """Модель для промпта LLM"""
    system_prompt: str
    user_prompt: str
    context: Optional[str] = None
    max_tokens: Optional[int] = 1000

class LLMResponse(BaseModel):
    """Модель для ответа LLM"""
    generated_query: str
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    model_used: str

class SupplierResult(BaseModel):
    """Модель результата поиска поставщика"""
    name: str
    website: Optional[str] = None
    contact_info: Optional[str] = None
    supplier_type: str = "поставщик"
    location: str = "kz"
    rating: float = 0.0
    verified: bool = False
    source: Optional[str] = None
    
    class Config:
        validate_by_name = True

class SupplierSearchResponse(BaseModel):
    """Модель ответа поиска поставщиков"""
    session_id: str
    suppliers: List[SupplierResult]
    total_suppliers: int
    search_time: float
    queries_used: List[str]
    location_info: Dict[str, str]
    
    class Config:
        validate_by_name = True

class DatabaseProductRecord(BaseModel):
    """Модель записи продукта в базе данных"""
    id: str
    filename: str
    data: ProductData
    created_at: datetime
    updated_at: datetime
    status: str = "active"

class ProductSearchParameters(BaseModel):
    """Модель параметров поиска на основе данных продукта"""
    product_data: ProductData
    supplier_type: Optional[SupplierType] = None
    target_location: str = "Almaty, Kazakhstan"
    delivery_date: Optional[str] = None
    required_services: List[str] = ["catalog", "price_list", "contact_info"]
    trusted_sources: List[str] = ["alibaba.com", "globalsources.com", "made-in-china.com"]
    additional_keywords: List[str] = []
    
    @classmethod
    def from_product_data(cls, product_data: ProductData, **kwargs):
        """Создает параметры поиска из данных продукта"""
        # Автоматически определяем тип поставщика на основе названия продукта
        supplier_type = cls._determine_supplier_type(product_data.product_name)
        
        # Генерируем дополнительные ключевые слова
        additional_keywords = cls._generate_keywords(product_data.product_name)
        
        return cls(
            product_data=product_data,
            supplier_type=supplier_type,
            additional_keywords=additional_keywords,
            **kwargs
        )
    
    @staticmethod
    def _determine_supplier_type(product_name: str) -> Optional[SupplierType]:
        """Определяет тип поставщика на основе названия продукта"""
        product_lower = product_name.lower()
        
        # Ключевые слова для определения типа поставщика
        manufacturer_keywords = ["component", "chip", "semiconductor", "electronic", "circuit"]
        food_keywords = ["food", "ingredient", "spice", "flour", "sugar", "oil", "meat", "vegetable"]
        raw_materials_keywords = ["steel", "aluminum", "copper", "plastic", "rubber", "wood", "fabric"]
        logistics_keywords = ["transport", "shipping", "delivery", "warehouse", "storage"]
        
        if any(keyword in product_lower for keyword in manufacturer_keywords):
            return SupplierType.MANUFACTURER
        elif any(keyword in product_lower for keyword in food_keywords):
            return SupplierType.FOOD
        elif any(keyword in product_lower for keyword in raw_materials_keywords):
            return SupplierType.RAW_MATERIALS
        elif any(keyword in product_lower for keyword in logistics_keywords):
            return SupplierType.LOGISTICS
        else:
            return SupplierType.GOODS
    
    @staticmethod
    def _generate_keywords(product_name: str) -> List[str]:
        """Генерирует дополнительные ключевые слова на основе названия продукта"""
        keywords = []
        product_lower = product_name.lower()
        
        # Добавляем общие ключевые слова для поиска поставщиков
        keywords.extend(["supplier", "vendor", "wholesale"])
        
        # Добавляем специфичные ключевые слова на основе продукта
        if any(word in product_lower for word in ["electronic", "component", "chip"]):
            keywords.extend(["electronic components", "semiconductor", "PCB"])
        elif any(word in product_lower for word in ["food", "ingredient"]):
            keywords.extend(["food ingredients", "bulk food", "food supplier"])
        elif any(word in product_lower for word in ["steel", "metal", "aluminum"]):
            keywords.extend(["metal supplier", "steel manufacturer", "metal wholesaler"])
        
        return keywords

class BatchSearchRequest(BaseModel):
    """Модель для пакетного поиска на основе данных из БД"""
    product_ids: List[str]
    target_location: str = "Almaty, Kazakhstan"
    delivery_date: Optional[str] = None
    supplier_type: Optional[SupplierType] = None
    required_services: List[str] = ["catalog", "price_list", "contact_info"]
    trusted_sources: List[str] = ["alibaba.com", "globalsources.com", "made-in-china.com"]

class BatchSearchResponse(BaseModel):
    """Модель ответа пакетного поиска"""
    batch_request: BatchSearchRequest
    search_results: Dict[str, SupplierSearchResponse]  # product_id -> results
    summary: Dict[str, Any]
    total_products: int
    successful_searches: int
    failed_searches: int

class ProductSearchRequest(BaseModel):
    """Модель запроса поиска по продукту"""
    product_id: str
    max_results: int = 10
    search_type: str = "web"
    
    class Config:
        validate_by_name = True

class ProductSearchResponse(BaseModel):
    """Модель ответа поиска по продукту"""
    session_id: str
    product_data: ProductData
    suppliers: List[SupplierResult]
    total_suppliers: int
    search_time: float
    supplier_type: str
    keywords: List[str]
    location_info: Dict[str, str]
    
    class Config:
        validate_by_name = True
