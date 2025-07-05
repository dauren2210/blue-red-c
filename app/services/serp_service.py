from serpapi import GoogleSearch
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from app.core.config import settings
from app.models import SearchQuery, SearchResult, SearchResponse, ProductData
from app.services.location_service import LocationService

class SerpService:
    """Сервис для работы с Serp API через официальный клиент"""
    
    def __init__(self):
        self.api_key = settings.SERP_API_KEY
        self.engine = settings.SERP_ENGINE
        self.max_results = settings.MAX_SEARCH_RESULTS
        self.timeout = settings.SEARCH_TIMEOUT
        self.location_service = LocationService()
    
    async def search(self, query: str, search_type: str = "web", **kwargs) -> SearchResponse:
        """
        Выполняет поисковый запрос через Serp API (официальный клиент, асинхронно)
        """
        start_time = datetime.now()
        
        # Определяем параметры локации на основе данных из БД
        location_params = self._get_location_params(kwargs)
        
        # Параметры запроса
        params = {
            "api_key": self.api_key,
            "engine": self.engine,
            "q": query,
            "num": min(kwargs.get("max_results", self.max_results), self.max_results),
            "gl": location_params["country_code"],
            "hl": location_params["language"]
        }
        
        # Добавляем специфичные параметры для разных типов поиска
        if search_type == "news":
            params["tbm"] = "nws"
        elif search_type == "images":
            params["tbm"] = "isch"
        elif search_type == "videos":
            params["tbm"] = "vid"
        
        # Добавляем дополнительные параметры
        if "site" in kwargs:
            params["as_sitesearch"] = kwargs["site"]
        if "date_range" in kwargs:
            params["tbs"] = kwargs["date_range"]
        if "filetype" in kwargs:
            params["as_filetype"] = kwargs["filetype"]
        
        try:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(
                None,  # default executor
                lambda: GoogleSearch(params).get_dict()
            )
            
            # Обрабатываем результаты
            results = self._parse_search_results(data, search_type)
            
            end_time = datetime.now()
            search_time = (end_time - start_time).total_seconds()
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=search_time,
                engine=self.engine
            )
            
        except Exception as e:
            # В случае ошибки возвращаем пустой результат
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_time=0.0,
                engine=self.engine
            )
    
    def _get_location_params(self, kwargs: Dict[str, Any]) -> Dict[str, str]:
        """
        Определяет параметры локации на основе данных из БД или переданных параметров
        """
        # Если передана локация из БД, используем её
        if "location" in kwargs and kwargs["location"]:
            location_info = self.location_service.detect_country_and_language(kwargs["location"])
            return {
                "country_code": location_info["country_code"],
                "language": location_info["language"]
            }
        
        # Если передан ProductData, извлекаем локацию
        if "product_data" in kwargs and kwargs["product_data"]:
            product_data = kwargs["product_data"]
            if isinstance(product_data, ProductData) and product_data.location:
                location_info = self.location_service.detect_country_and_language(product_data.location)
                return {
                    "country_code": location_info["country_code"],
                    "language": location_info["language"]
                }
        
        # Если переданы явные параметры локации
        if "country_code" in kwargs and "language" in kwargs:
            return {
                "country_code": kwargs["country_code"],
                "language": kwargs["language"]
            }
        
        # По умолчанию используем Казахстан
        return {
            "country_code": "kz",
            "language": "ru"
        }
    
    async def search_with_location(self, query: str, location: str, **kwargs) -> SearchResponse:
        """
        Выполняет поиск с автоматическим определением локации
        """
        location_info = self.location_service.detect_country_and_language(location)
        
        search_params = {
            **kwargs,
            "country_code": location_info["country_code"],
            "language": location_info["language"]
        }
        
        return await self.search(query, **search_params)
    
    async def multilingual_search(self, query: str, product_data: ProductData, **kwargs) -> List[SearchResponse]:
        """
        Выполняет многоязычный поиск на основе локации продукта
        """
        # Получаем параметры для многоязычного поиска
        search_params_list = self.location_service.get_multilingual_search_params(product_data)
        
        results = []
        for params in search_params_list:
            try:
                search_result = await self.search(
                    query,
                    country_code=params["country_code"],
                    language=params["language"],
                    **kwargs
                )
                results.append(search_result)
            except Exception as e:
                print(f"Error in multilingual search for {params}: {e}")
                continue
        
        return results
    
    def _parse_search_results(self, data: Dict[str, Any], search_type: str) -> List[SearchResult]:
        """
        Парсит результаты поиска из ответа Serp API
        """
        results = []
        
        try:
            if search_type == "web":
                organic_results = data.get("organic_results", [])
                for i, result in enumerate(organic_results[:self.max_results]):
                    results.append(SearchResult(
                        title=result.get("title", ""),
                        link=result.get("link", ""),
                        snippet=result.get("snippet", ""),
                        position=i + 1,
                        source=result.get("source", ""),
                        timestamp=datetime.now()
                    ))
            
            elif search_type == "news":
                news_results = data.get("news_results", [])
                for i, result in enumerate(news_results[:self.max_results]):
                    results.append(SearchResult(
                        title=result.get("title", ""),
                        link=result.get("link", ""),
                        snippet=result.get("snippet", ""),
                        position=i + 1,
                        source=result.get("source", ""),
                        timestamp=datetime.now()
                    ))
            
            elif search_type == "images":
                image_results = data.get("images_results", [])
                for i, result in enumerate(image_results[:self.max_results]):
                    results.append(SearchResult(
                        title=result.get("title", ""),
                        link=result.get("link", ""),
                        snippet=result.get("snippet", ""),
                        position=i + 1,
                        source=result.get("source", ""),
                        timestamp=datetime.now()
                    ))
            
        except Exception as e:
            # Логируем ошибку парсинга
            print(f"Error parsing search results: {e}")
        
        return results
    
    async def search_with_fallback(self, query: str, search_type: str = "web", **kwargs) -> SearchResponse:
        """
        Выполняет поиск с fallback на другие поисковые системы
        """
        # Основной поиск
        result = await self.search(query, search_type, **kwargs)
        
        # Если результатов нет, пробуем альтернативные параметры
        if not result.results:
            # Пробуем без дополнительных фильтров
            fallback_kwargs = dict(kwargs)
            fallback_kwargs["max_results"] = self.max_results
            result = await self.search(query, search_type, **fallback_kwargs)
        
        return result
    
    async def batch_search(self, queries: List[str], search_type: str = "web", **kwargs) -> List[SearchResponse]:
        """
        Выполняет пакетный поиск по нескольким запросам
        """
        tasks = [
            self.search(query, search_type, **kwargs) 
            for query in queries
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем исключения
        valid_results = []
        for result in results:
            if isinstance(result, SearchResponse):
                valid_results.append(result)
            else:
                # Создаем пустой результат для неудачных запросов
                valid_results.append(SearchResponse(
                    query="",
                    results=[],
                    total_results=0,
                    search_time=0.0,
                    engine=self.engine
                ))
        
        return valid_results
    
    async def search_suppliers(self, query: str, product_data: Optional[ProductData] = None, **kwargs) -> SearchResponse:
        """
        Специализированный поиск для поставщиков с учетом локации, нацеленный на контактные страницы
        """
        # Определяем параметры локации
        if product_data and product_data.location:
            location_info = self.location_service.detect_country_and_language(product_data.location)
            country_code = location_info["country_code"]
            language = location_info["language"]
            
            # Получаем локальные источники для данной страны
            local_sources = self.location_service.get_local_sources(country_code)
            trusted_sources = self.location_service.get_trusted_sources_by_region(country_code)
            
            # Добавляем локальные источники к запросу
            if local_sources and "site_restrictions" not in kwargs:
                kwargs["site_restrictions"] = local_sources[:3]  # Берем первые 3
            
        else:
            # Используем переданные параметры или значения по умолчанию
            country_code = kwargs.get("country_code", "kz")
            language = kwargs.get("language", "ru")
        
        # Модифицируем запрос для поиска контактных страниц
        contact_keywords = self._get_contact_keywords(language)
        enhanced_query = self._enhance_query_for_contact_pages(query, contact_keywords)
        
        # Добавляем специфичные параметры для поиска поставщиков
        supplier_params = {
            "gl": country_code,
            "hl": language,
        }
        # Объединяем supplier_params и kwargs
        all_kwargs = {**kwargs, **supplier_params}
        
        # Добавляем ограничения по сайтам если указаны
        if "site_restrictions" in all_kwargs:
            site_filter = " OR ".join([f"site:{site}" for site in all_kwargs["site_restrictions"]])
            enhanced_query = f"({enhanced_query}) ({site_filter})"
        
        return await self.search_with_fallback(enhanced_query, **all_kwargs)
    
    def _get_contact_keywords(self, language: str) -> List[str]:
        """
        Возвращает ключевые слова для поиска контактных страниц на разных языках
        """
        contact_keywords = {
            "ru": [
                "контакты", "связаться с нами", "контактная информация", 
                "телефон", "email", "адрес", "обратная связь",
                "контактные данные", "связаться", "написать нам"
            ],
            "en": [
                "contact", "contact us", "contact information", 
                "phone", "email", "address", "get in touch",
                "contact details", "reach us", "write to us"
            ],
            "de": [
                "kontakt", "kontaktieren sie uns", "kontaktinformationen",
                "telefon", "e-mail", "adresse", "erreichen sie uns"
            ],
            "fr": [
                "contact", "nous contacter", "informations de contact",
                "téléphone", "email", "adresse", "nous joindre"
            ],
            "it": [
                "contatti", "contattaci", "informazioni di contatto",
                "telefono", "email", "indirizzo", "raggiungici"
            ],
            "es": [
                "contacto", "contáctenos", "información de contacto",
                "teléfono", "email", "dirección", "póngase en contacto"
            ],
            "uk": [
                "контакти", "зв'язатися з нами", "контактна інформація",
                "телефон", "email", "адреса", "зворотній зв'язок"
            ],
            "kk": [
                "байланыс", "бізбен хабарласыңыз", "байланыс ақпараты",
                "телефон", "email", "мекенжай", "кері байланыс"
            ],
            "uz": [
                "aloqa", "biz bilan bog'laning", "aloqa ma'lumotlari",
                "telefon", "email", "manzil", "teskari aloqa"
            ],
            "ky": [
                "байланыш", "биз менен байланышыңыз", "байланыш маалыматы",
                "телефон", "email", "дарек", "тескери байланыш"
            ],
            "tg": [
                "тамос", "бо мо тамос гиред", "маълумоти тамос",
                "телефон", "email", "суроға", "тамоси барқарор"
            ],
            "tk": [
                "baglanyşyk", "biz bilen baglanyşyň", "baglanyşyk maglumatlary",
                "telefon", "email", "adres", "ters baglanyşyk"
            ],
            "az": [
                "əlaqə", "bizimlə əlaqə saxlayın", "əlaqə məlumatları",
                "telefon", "email", "ünvan", "tərs əlaqə"
            ],
            "hy": [
                "կապ", "կապվեք մեզ հետ", "կապի տվյալներ",
                "հեռախոս", "email", "հասցե", "հետադարձ կապ"
            ],
            "ka": [
                "კონტაქტი", "დაგვიკავშირდით", "საკონტაქტო ინფორმაცია",
                "ტელეფონი", "email", "მისამართი", "უკუკავშირი"
            ],
            "ro": [
                "contact", "contactați-ne", "informații de contact",
                "telefon", "email", "adresă", "luați legătura cu noi"
            ],
            "pl": [
                "kontakt", "skontaktuj się z nami", "informacje kontaktowe",
                "telefon", "email", "adres", "skontaktuj się"
            ],
            "zh": [
                "联系", "联系我们", "联系信息",
                "电话", "邮箱", "地址", "取得联系"
            ],
            "ja": [
                "お問い合わせ", "お問い合わせください", "連絡先情報",
                "電話", "メール", "住所", "お問い合わせ"
            ],
            "ko": [
                "연락처", "문의하기", "연락처 정보",
                "전화", "이메일", "주소", "연락하기"
            ],
            "tr": [
                "iletişim", "bizimle iletişime geçin", "iletişim bilgileri",
                "telefon", "email", "adres", "bize ulaşın"
            ],
            "pt": [
                "contato", "entre em contato", "informações de contato",
                "telefone", "email", "endereço", "fale conosco"
            ]
        }
        
        return contact_keywords.get(language, contact_keywords["en"])
    
    def _enhance_query_for_contact_pages(self, original_query: str, contact_keywords: List[str]) -> str:
        """
        Улучшает запрос для поиска контактных страниц
        """
        # Добавляем ключевые слова для контактных страниц
        contact_terms = " OR ".join([f'"{keyword}"' for keyword in contact_keywords[:5]])  # Берем первые 5
        
        # Формируем улучшенный запрос
        enhanced_query = f'({original_query}) AND ({contact_terms})'
        
        # Добавляем специфичные термины для поставщиков
        supplier_terms = [
            "supplier", "vendor", "distributor", "wholesaler", "manufacturer",
            "поставщик", "дистрибьютор", "оптовик", "производитель"
        ]
        
        # Добавляем термины для контактной информации
        contact_info_terms = [
            "phone", "email", "address", "contact form", "get quote",
            "телефон", "email", "адрес", "форма обратной связи", "получить предложение"
        ]
        
        # Объединяем все термины
        all_terms = supplier_terms + contact_info_terms
        terms_query = " OR ".join([f'"{term}"' for term in all_terms[:8]])  # Берем первые 8
        
        final_query = f'({enhanced_query}) AND ({terms_query})'
        
        return final_query 