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
        
        # Получаем параметры локации
        if product_data:
            location_params = self.location_service.get_search_parameters(product_data)
        else:
            location_params = self.location_service.detect_country_and_language(request.target_location)
        
        # Добавляем локацию в параметры для использования в запросах
        location_params["location"] = request.target_location
        
        # Генерируем поисковые запросы
        search_queries = await self._generate_supplier_queries(
            request.search_query,
            request.amount,
            location_params,
            request.search_strategy,
            request.delivery_date
        )
        
        # Выполняем поиск
        search_results = []
        for query in search_queries:
            try:
                result = await self.serp_service.search_suppliers(
                    query,
                    product_data=product_data,
                    max_results=request.max_results,
                    search_type=request.search_type,
                    location=request.target_location
                )
                search_results.append(result)
            except Exception as e:
                print(f"Error searching for query '{query}': {e}")
                continue
        
        # Анализируем и фильтруем результаты
        supplier_results = await self._analyze_supplier_results(
            search_results,
            request.search_query,
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
        
        # Добавляем локацию в параметры для использования в запросах
        location_params["location"] = request.target_location
        
        # Генерируем поисковые запросы
        search_queries = await self._generate_product_based_queries(
            product_data.product_name,
            supplier_type,
            keywords,
            location_params,
            product_data.amount,
            bool(product_data.date_and_time),
            product_data.date_and_time
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
        strategy: str = "direct",
        date_and_time: str = None
    ) -> List[str]:
        """
        Генерирует поисковые запросы для поиска поставщиков на основе search_query
        """
        # Получаем полное название локации
        location_service = LocationService()
        full_location = location_service.get_full_location_name(location_params.get("location", ""))
        
        # Базовый запрос из search_query
        base_query = f"{search_query} supplier"
        
        # Добавляем ключевые слова в зависимости от стратегии
        if strategy == "direct":
            queries = [
                f"{base_query} in {full_location}",
                f"{search_query} wholesale in {full_location}",
                f"{search_query} suppliers in {full_location}"
            ]
            
            # Добавляем новый шаблон "buy {product} in {location} deliver {date}"
            if date_and_time:
                queries.append(f"buy {search_query} in {full_location} deliver {date_and_time}")
            
        elif strategy == "catalog":
            queries = [
                f"{search_query} supplier catalog in {full_location}",
                f"{search_query} price list suppliers in {full_location}",
                f"{search_query} wholesale suppliers in {full_location}"
            ]
            
            if date_and_time:
                queries.append(f"buy {search_query} in {full_location} deliver {date_and_time} catalog")
                
        elif strategy == "trusted":
            queries = [
                f"{search_query} verified suppliers in {full_location}",
                f"{search_query} reliable suppliers in {full_location}",
                f"{search_query} official suppliers in {full_location}"
            ]
            
            if date_and_time:
                queries.append(f"buy {search_query} in {full_location} deliver {date_and_time} trusted supplier")
                
        elif strategy == "local":
            queries = [
                f"{search_query} local suppliers in {full_location}",
                f"{search_query} regional suppliers in {full_location}",
                f"{search_query} nearby suppliers in {full_location}"
            ]
            
            if date_and_time:
                queries.append(f"buy {search_query} in {full_location} deliver {date_and_time} local")
        else:
            queries = [base_query]
            if date_and_time:
                queries.append(f"buy {search_query} in {full_location} deliver {date_and_time}")
        
        # Добавляем информацию о количестве если указана
        if amount:
            # Добавляем количество к запросам с датой
            enhanced_queries = []
            for query in queries:
                enhanced_queries.append(query)
                if "buy" in query and date_and_time:
                    enhanced_queries.append(f"{query} {amount}")
            
            # Добавляем количество к обычным запросам
            for query in queries:
                if "buy" not in query:
                    enhanced_queries.append(f"{query} {amount}")
            
            queries = enhanced_queries
        
        return queries
    
    async def _generate_product_based_queries(
        self,
        search_query: str,
        supplier_type: str,
        keywords: List[str],
        location_params: Dict[str, str],
        amount: str = None,
        is_urgent: bool = False,
        date_and_time: str = None
    ) -> List[str]:
        """
        Генерирует запросы на основе search_query
        """
        # Получаем полное название локации
        location_service = LocationService()
        full_location = location_service.get_full_location_name(location_params.get("location", ""))
        
        queries = []
        
        # Основной запрос из search_query
        main_query = f"{search_query} {supplier_type}"
        
        queries.append(f"{main_query} in {full_location}")
        
        # Запрос с количеством
        if amount:
            queries.append(f"{main_query} {amount} in {full_location}")
        
        # Запрос с датой (если срочно)
        if is_urgent:
            queries.append(f"{main_query} urgent in {full_location}")
        
        # Запрос с ключевыми словами
        if keywords:
            keywords_query = f"{search_query} {' '.join(keywords[:3])} in {full_location}"
            queries.append(keywords_query)
        
        # Добавляем новый шаблон "buy {product} in {location} deliver {date}"
        if date_and_time:
            queries.append(f"buy {search_query} in {full_location} deliver {date_and_time}")
            
            # Комбинируем с количеством
            if amount:
                queries.append(f"buy {search_query} in {full_location} deliver {date_and_time} {amount}")
        
        return queries
    
    def _analyze_product_for_supplier_search(self, product_data: ProductData) -> tuple[str, List[str]]:
        """
        Анализирует данные продукта для определения типа поставщика и ключевых слов
        """
        product_name = product_data.product_name.lower()
        
        # Определяем тип поставщика
        supplier_type = "supplier"
        if any(word in product_name for word in ["electronics", "computer", "laptop", "smartphone"]):
            supplier_type = "electronics distributor"
        elif any(word in product_name for word in ["clothing", "shoes", "textile"]):
            supplier_type = "wholesale clothing supplier"
        elif any(word in product_name for word in ["food", "products", "nutrition"]):
            supplier_type = "food supplier"
        elif any(word in product_name for word in ["construction", "materials"]):
            supplier_type = "construction materials supplier"
        
        # Извлекаем ключевые слова
        keywords = []
        words = product_name.split()
        for word in words:
            if len(word) > 3 and word not in ["for", "the", "this", "that"]:
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
        Показывает только те результаты, где есть телефон или email
        """
        title = search_result.title
        snippet = search_result.snippet
        link = search_result.link
        
        # Извлекаем контактную информацию (телефоны и адреса)
        contact_info = self._extract_contact_info(snippet)
        email_addresses = self._extract_email_addresses(snippet)
        has_phone = self._has_phone_number(contact_info, snippet)
        has_email = len(email_addresses) > 0
        
        if not has_phone and not has_email:
            return None
        
        company_name = self._extract_company_name(title, snippet)
        supplier_type = "supplier"
        
        return SupplierResult(
            name=company_name,
            website=link,
            contact_info=contact_info,
            email_addresses=email_addresses if email_addresses else None,
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
        Извлекает контактную информацию из сниппета (только телефоны и адреса)
        Собирает все найденные номера телефонов в список
        """
        import re
        
        contact_info = []
        
        # Телефоны - улучшенные паттерны
        phone_patterns = [
            r'\+7\s?\(?[0-9]{3}\)?\s?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}',  # Российский формат
            r'8\s?\(?[0-9]{3}\)?\s?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}',  # Российский формат с 8
            r'\+[0-9]{1,3}\s?[0-9]{3,4}\s?[0-9]{3,4}\s?[0-9]{3,4}',  # Международный формат
            r'[0-9]{3}[\s\-]?[0-9]{3}[\s\-]?[0-9]{4}',  # Американский формат
            r'[\+]?[0-9\s\-\(\)]{10,}',  # Общий паттерн
        ]
        
        all_phones = []
        for pattern in phone_patterns:
            phones = re.findall(pattern, snippet)
            for phone in phones:
                # Очищаем от лишних пробелов
                clean_phone = re.sub(r'\s+', ' ', phone.strip())
                # Проверяем, что это действительно телефон (минимум 10 цифр)
                digits_only = re.sub(r'[^\d]', '', clean_phone)
                if len(digits_only) >= 10 and clean_phone not in all_phones:
                    all_phones.append(clean_phone)
        
        # Добавляем все найденные телефоны
        if all_phones:
            phones_str = "; ".join([f"Тел: {phone}" for phone in all_phones])
            contact_info.append(phones_str)
        
        # Адрес (если есть)
        address_patterns = [
            r'г\.\s*[А-Яа-я\s]+,\s*[А-Яа-я\s]+',  # "г. Москва, ул. Примерная"
            r'[А-Яа-я\s]+,\s*[0-9]+',  # "Москва, 123"
            r'[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[0-9]+',  # "New York, NY, 12345"
        ]
        
        for pattern in address_patterns:
            addresses = re.findall(pattern, snippet)
            if addresses:
                address = addresses[0].strip()
                contact_info.append(f"Адрес: {address}")
                break
        
        return "; ".join(contact_info) if contact_info else ""
    
    def _extract_email_addresses(self, snippet: str) -> List[str]:
        """
        Извлекает все email адреса из сниппета
        """
        import re
        
        # Паттерн для поиска email адресов
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, snippet)
        
        # Убираем дубликаты и возвращаем список
        unique_emails = list(set(emails))
        return unique_emails
    
    def _has_phone_number(self, contact_info: str, snippet: str) -> bool:
        """
        Проверяет наличие номера телефона в контактной информации или сниппете
        """
        import re
        
        # Паттерны для поиска телефонов - более гибкие
        phone_patterns = [
            r'[\+]?[0-9\s\-\(\)]{10,}',  # Общий паттерн
            r'\+7\s?\(?[0-9]{3}\)?\s?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}',  # Российский формат
            r'8\s?\(?[0-9]{3}\)?\s?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}',  # Российский формат с 8
            r'\+[0-9]{1,3}\s?[0-9]{3,4}\s?[0-9]{3,4}\s?[0-9]{3,4}',  # Международный формат
            r'[0-9]{3}[\s\-]?[0-9]{3}[\s\-]?[0-9]{4}',  # Американский формат
            r'тел[а-я]*[:\s]*[0-9\+\-\(\)\s]+',  # "тел: номер"
            r'phone[:\s]*[0-9\+\-\(\)\s]+',  # "phone: номер"
            r'телефон[:\s]*[0-9\+\-\(\)\s]+',  # "телефон: номер"
            r'call[:\s]*[0-9\+\-\(\)\s]+',  # "call: номер"
            r'contact[:\s]*[0-9\+\-\(\)\s]+',  # "contact: номер"
        ]
        
        # Проверяем в контактной информации
        for pattern in phone_patterns:
            matches = re.findall(pattern, contact_info, re.IGNORECASE)
            for match in matches:
                # Проверяем, что это действительно телефон (минимум 7 цифр для более гибкой проверки)
                digits_only = re.sub(r'[^\d]', '', match)
                if len(digits_only) >= 7:  # Снижаем требования с 10 до 7 цифр
                    return True
        
        # Проверяем в сниппете
        for pattern in phone_patterns:
            matches = re.findall(pattern, snippet, re.IGNORECASE)
            for match in matches:
                # Проверяем, что это действительно телефон (минимум 7 цифр для более гибкой проверки)
                digits_only = re.sub(r'[^\d]', '', match)
                if len(digits_only) >= 7:  # Снижаем требования с 10 до 7 цифр
                    return True
        
        return False
    
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