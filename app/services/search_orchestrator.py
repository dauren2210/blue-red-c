import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models import (
    SearchQuery, SearchResult, SearchResponse, 
    SupplierSearchRequest, SupplierSearchResponse, SupplierResult,
    ProductData, ProductSearchRequest, ProductSearchResponse
)
from app.services.serp_service import SerpService
from app.services.location_service import LocationService
from app.db.mongodb import get_database

class SearchOrchestrator:
    """Оркестратор для координации поисковых операций"""
    
    def __init__(self):
        self.serp_service = SerpService()
        self.location_service = LocationService()
        self.db = get_database()
    
    async def search_suppliers(self, request: SupplierSearchRequest) -> SupplierSearchResponse:
        """
        Поиск поставщиков с учетом локации из БД
        """
        start_time = datetime.now()
        
        # Получаем данные продукта из БД если указан ID
        product_data = None
        if request.product_id:
            product_data = await self._get_product_from_db(request.product_id)
        
        # Если данные продукта не найдены, используем переданные данные
        if not product_data and request.product_data:
            product_data = request.product_data
        
        # Определяем параметры локации
        location_params = self.location_service.get_search_parameters(product_data) if product_data else {
            "country_code": "kz",
            "language": "ru",
            "primary_language": "ru"
        }
        
        # Генерируем поисковые запросы
        search_queries = await self._generate_supplier_queries(
            request.search_query,
            request.amount,
            location_params,
            request.search_strategy
        )
        
        # Выполняем поиск
        search_results = []
        for query in search_queries:
            try:
                result = await self.serp_service.search_suppliers(
                    query,
                    product_data=product_data,
                    max_results=request.max_results,
                    search_type=request.search_type
                )
                search_results.append(result)
            except Exception as e:
                print(f"Error searching for query '{query}': {e}")
                continue
        
        # Анализируем и фильтруем результаты
        supplier_results = await self._analyze_supplier_results(
            search_results,
            request.product_name,
            location_params
        )
        
        # Сохраняем сессию поиска
        session_id = await self._save_search_session(
            request,
            search_results,
            supplier_results,
            location_params
        )
        
        end_time = datetime.now()
        search_time = (end_time - start_time).total_seconds()
        
        return SupplierSearchResponse(
            session_id=session_id,
            suppliers=supplier_results,
            total_suppliers=len(supplier_results),
            search_time=search_time,
            queries_used=search_queries,
            location_info=location_params
        )
    
    async def search_by_product_data(self, request: ProductSearchRequest) -> ProductSearchResponse:
        """
        Поиск поставщиков на основе данных продукта из БД
        """
        start_time = datetime.now()
        
        # Получаем данные продукта из БД
        product_data = await self._get_product_from_db(request.product_id)
        if not product_data:
            raise ValueError(f"Product with ID {request.product_id} not found")
        
        # Определяем тип поставщика и ключевые слова
        supplier_type, keywords = self._analyze_product_for_supplier_search(product_data)
        
        # Определяем параметры локации
        location_params = self.location_service.get_search_parameters(product_data)
        
        # Генерируем поисковые запросы
        search_queries = await self._generate_product_based_queries(
            product_data.product_name,
            supplier_type,
            keywords,
            location_params,
            product_data.amount,
            bool(product_data.date_and_time)
        )
        
        # Выполняем многоязычный поиск
        search_results = await self.serp_service.multilingual_search(
            search_queries[0],  # Используем первый запрос для многоязычного поиска
            product_data,
            max_results=request.max_results
        )
        
        # Анализируем результаты
        supplier_results = await self._analyze_supplier_results(
            search_results,
            product_data.product_name,
            location_params
        )
        
        # Сохраняем сессию
        session_id = await self._save_product_search_session(
            request,
            product_data,
            search_results,
            supplier_results,
            location_params
        )
        
        end_time = datetime.now()
        search_time = (end_time - start_time).total_seconds()
        
        return ProductSearchResponse(
            session_id=session_id,
            product_data=product_data,
            suppliers=supplier_results,
            total_suppliers=len(supplier_results),
            search_time=search_time,
            supplier_type=supplier_type,
            keywords=keywords,
            location_info=location_params
        )
    
    async def _generate_supplier_queries(
        self, 
        search_query: str, 
        amount: str, 
        location_params: Dict[str, str],
        strategy: str = "direct"
    ) -> List[str]:
        """
        Генерирует поисковые запросы для поиска поставщиков на основе search_query
        """
        # Базовый запрос из search_query
        base_query = f"{search_query} поставщик"
        
        # Добавляем ключевые слова в зависимости от стратегии
        if strategy == "direct":
            queries = [
                f"{base_query} {location_params['country_code']}",
                f"{search_query} купить оптом {location_params['country_code']}",
                f"{search_query} поставщики {location_params['country_code']}"
            ]
        elif strategy == "catalog":
            queries = [
                f"{search_query} каталог поставщиков {location_params['country_code']}",
                f"{search_query} прайс-лист поставщики {location_params['country_code']}",
                f"{search_query} оптовые поставщики {location_params['country_code']}"
            ]
        elif strategy == "trusted":
            queries = [
                f"{search_query} проверенные поставщики {location_params['country_code']}",
                f"{search_query} надежные поставщики {location_params['country_code']}",
                f"{search_query} официальные поставщики {location_params['country_code']}"
            ]
        elif strategy == "local":
            queries = [
                f"{search_query} местные поставщики {location_params['country_code']}",
                f"{search_query} региональные поставщики {location_params['country_code']}",
                f"{search_query} поставщики рядом {location_params['country_code']}"
            ]
        else:
            queries = [base_query]
        
        # Добавляем информацию о количестве если указана
        if amount:
            queries = [f"{q} {amount}" for q in queries]
        
        return queries
    
    async def _generate_product_based_queries(
        self,
        search_query: str,
        supplier_type: str,
        keywords: List[str],
        location_params: Dict[str, str],
        amount: str = None,
        is_urgent: bool = False
    ) -> List[str]:
        """
        Генерирует запросы на основе search_query
        """
        queries = []
        
        # Основной запрос из search_query
        main_query = f"{search_query} {supplier_type}"
        
        queries.append(f"{main_query} {location_params['country_code']}")
        
        # Запрос с количеством
        if amount:
            queries.append(f"{main_query} {amount} {location_params['country_code']}")
        
        # Запрос с датой (если срочно)
        if is_urgent:
            queries.append(f"{main_query} срочно {location_params['country_code']}")
        
        # Запрос с ключевыми словами
        if keywords:
            keywords_query = f"{search_query} {' '.join(keywords[:3])} {location_params['country_code']}"
            queries.append(keywords_query)
        
        return queries
    
    def _analyze_product_for_supplier_search(self, product_data: ProductData) -> tuple[str, List[str]]:
        """
        Анализирует данные продукта для определения типа поставщика и ключевых слов
        """
        product_name = product_data.product_name.lower()
        
        # Определяем тип поставщика
        supplier_type = "поставщик"
        if any(word in product_name for word in ["электроника", "техника", "компьютер"]):
            supplier_type = "дистрибьютор электроники"
        elif any(word in product_name for word in ["одежда", "обувь", "текстиль"]):
            supplier_type = "оптовый поставщик одежды"
        elif any(word in product_name for word in ["продукты", "еда", "питание"]):
            supplier_type = "поставщик продуктов"
        elif any(word in product_name for word in ["строительство", "материалы"]):
            supplier_type = "поставщик строительных материалов"
        
        # Извлекаем ключевые слова
        keywords = []
        words = product_name.split()
        for word in words:
            if len(word) > 3 and word not in ["для", "своих", "этот", "такой"]:
                keywords.append(word)
        
        return supplier_type, keywords[:5]  # Возвращаем до 5 ключевых слов
    
    async def _analyze_supplier_results(
        self,
        search_results: List[SearchResponse],
        product_name: str,
        location_params: Dict[str, str]
    ) -> List[SupplierResult]:
        """
        Анализирует результаты поиска и извлекает информацию о поставщиках
        """
        supplier_results = []
        
        for search_response in search_results:
            for result in search_response.results:
                # Анализируем каждый результат
                supplier_info = await self._extract_supplier_info(
                    result,
                    product_name,
                    location_params
                )
                
                if supplier_info:
                    supplier_results.append(supplier_info)
        
        # Убираем дубликаты
        unique_suppliers = {}
        for supplier in supplier_results:
            key = supplier.website or supplier.name
            if key not in unique_suppliers:
                unique_suppliers[key] = supplier
        
        return list(unique_suppliers.values())
    
    async def _extract_supplier_info(
        self,
        search_result: SearchResult,
        product_name: str,
        location_params: Dict[str, str]
    ) -> Optional[SupplierResult]:
        """
        Извлекает информацию о поставщике из результата поиска
        """
        # Простой анализ на основе заголовка и сниппета
        title = search_result.title.lower()
        snippet = search_result.snippet.lower()
        link = search_result.link
        
        # Проверяем, что это действительно поставщик
        supplier_keywords = ["поставщик", "опт", "дистрибьютор", "производитель", "купить", "продажа"]
        is_supplier = any(keyword in title or keyword in snippet for keyword in supplier_keywords)
        
        if not is_supplier:
            return None
        
        # Извлекаем название компании
        company_name = self._extract_company_name(title, snippet)
        
        # Определяем тип поставщика
        supplier_type = "поставщик"
        if any(word in title for word in ["производитель", "завод", "фабрика"]):
            supplier_type = "производитель"
        elif any(word in title for word in ["дистрибьютор", "дистрибуция"]):
            supplier_type = "дистрибьютор"
        elif any(word in title for word in ["опт", "оптовый"]):
            supplier_type = "оптовый поставщик"
        
        # Извлекаем контактную информацию
        contact_info = self._extract_contact_info(snippet)
        
        return SupplierResult(
            name=company_name,
            website=link,
            contact_info=contact_info,
            supplier_type=supplier_type,
            location=location_params.get("country_code", "kz"),
            rating=0.0,
            verified=False,
            source=search_result.source
        )
    
    def _extract_company_name(self, title: str, snippet: str) -> str:
        """
        Извлекает название компании из заголовка и сниппета
        """
        # Простая логика извлечения названия
        words = title.split()
        if len(words) >= 2:
            return " ".join(words[:3])  # Берем первые 3 слова
        return title
    
    def _extract_contact_info(self, snippet: str) -> str:
        """
        Извлекает контактную информацию из сниппета
        """
        # Ищем телефоны, email, адреса
        import re
        
        # Телефон
        phone_pattern = r'[\+]?[0-9\s\-\(\)]{10,}'
        phones = re.findall(phone_pattern, snippet)
        
        # Email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, snippet)
        
        contact_info = []
        if phones:
            contact_info.append(f"Тел: {phones[0]}")
        if emails:
            contact_info.append(f"Email: {emails[0]}")
        
        return "; ".join(contact_info) if contact_info else ""
    
    async def _get_product_from_db(self, product_id: str) -> Optional[ProductData]:
        """
        Получает данные продукта из базы данных
        """
        try:
            collection = self.db.products
            product_doc = await collection.find_one({"_id": product_id})
            
            if product_doc:
                return ProductData(
                    product_name=product_doc.get("product_name", ""),
                    amount=product_doc.get("amount", ""),
                    date_time=product_doc.get("date_time"),
                    location=product_doc.get("location", "")
                )
        except Exception as e:
            print(f"Error getting product from DB: {e}")
        
        return None
    
    async def _save_search_session(
        self,
        request: SupplierSearchRequest,
        search_results: List[SearchResponse],
        supplier_results: List[SupplierResult],
        location_params: Dict[str, str]
    ) -> str:
        """
        Сохраняет сессию поиска в базу данных
        """
        try:
            session_data = {
                "timestamp": datetime.now(),
                "request": request.dict(),
                "search_results": [result.dict() for result in search_results],
                "supplier_results": [supplier.dict() for supplier in supplier_results],
                "location_params": location_params,
                "total_suppliers": len(supplier_results)
            }
            
            collection = self.db.search_sessions
            result = await collection.insert_one(session_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving search session: {e}")
            return ""
    
    async def _save_product_search_session(
        self,
        request: ProductSearchRequest,
        product_data: ProductData,
        search_results: List[SearchResponse],
        supplier_results: List[SupplierResult],
        location_params: Dict[str, str]
    ) -> str:
        """
        Сохраняет сессию поиска по продукту в базу данных
        """
        try:
            session_data = {
                "timestamp": datetime.now(),
                "request": request.dict(),
                "product_data": product_data.dict(),
                "search_results": [result.dict() for result in search_results],
                "supplier_results": [supplier.dict() for supplier in supplier_results],
                "location_params": location_params,
                "total_suppliers": len(supplier_results)
            }
            
            collection = self.db.product_search_sessions
            result = await collection.insert_one(session_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving product search session: {e}")
            return "" 