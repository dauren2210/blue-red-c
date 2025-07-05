import asyncio
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.search_orchestrator import SearchOrchestrator
from app.models import SupplierSearchRequest, ProductData

async def test_supplier_search_with_new_format():
    """
    Тест поиска поставщиков с новым форматом запросов (минимум запросов для экономии лимита API)
    """
    print("=== Тест поиска поставщиков с новым форматом запросов ===")
    
    orchestrator = SearchOrchestrator()
    
    request = SupplierSearchRequest(
        search_query="smartphone",
        target_location="Germany",
        amount="50",
        search_strategy="direct",
        search_type="organic",
        max_results=5,
        delivery_date="25.07.2025"
    )
    
    print(f"Поисковый запрос: {request.search_query}")
    print(f"Локация: {request.target_location}")
    print(f"Количество: {request.amount}")
    print(f"Дата доставки: {request.delivery_date}")
    print()
    
    try:
        # Выполняем поиск только по первым двум запросам
        search_queries = await orchestrator._generate_supplier_queries(
            request.search_query,
            request.amount,
            {"country_code": "de", "language": "de", "location": request.target_location},
            request.search_strategy,
            request.delivery_date
        )
        # Ограничиваем до 2 запросов
        search_queries = search_queries[:2]
        print("=== Использованные запросы ===")
        for i, query in enumerate(search_queries, 1):
            print(f"{i}. {query}")
        print()
        
        # Выполняем поиск вручную по этим запросам
        supplier_results = []
        for query in search_queries:
            result = await orchestrator.serp_service.search_suppliers(
                query,
                product_data=None,
                max_results=request.max_results,
                search_type=request.search_type,
                location=request.target_location
            )
            # Анализируем и фильтруем результаты
            supplier_results.extend(
                await orchestrator._analyze_supplier_results([result], request.search_query, {"country_code": "de", "language": "de"})
            )
        # Убираем дубликаты
        unique_suppliers = {}
        for supplier in supplier_results:
            key = supplier.website or supplier.name
            if key not in unique_suppliers:
                unique_suppliers[key] = supplier
        supplier_results = list(unique_suppliers.values())
        
        print("=== Найденные поставщики ===")
        if supplier_results:
            for i, supplier in enumerate(supplier_results, 1):
                print(f"\n{i}. {supplier.name}")
                print(f"   Веб-сайт: {supplier.website}")
                print(f"   Тип: {supplier.supplier_type}")
                print(f"   Локация: {supplier.location}")
                print(f"   Контакт: {supplier.contact_info}")
                if supplier.email_addresses:
                    print(f"   Email: {supplier.email_addresses}")
        else:
            print("Поставщики не найдены")
        
        print(f"\nВсего найдено поставщиков: {len(supplier_results)}")
        
    except Exception as e:
        print(f"Ошибка при поиске: {e}")
        import traceback
        traceback.print_exc()

async def test_location_service():
    """
    Тест сервиса локации для проверки полных названий
    """
    print("\n=== Тест сервиса локации ===")
    
    from app.services.location_service import LocationService
    
    location_service = LocationService()
    
    test_locations = ["Germany", "United States", "Kazakhstan", "Russia", "France"]
    
    for location in test_locations:
        params = location_service.detect_country_and_language(location)
        full_name = location_service.get_full_location_name(location)
        print(f"Локация: {location}")
        print(f"  Полное название: {full_name}")
        print(f"  Код страны: {params['country_code']}")
        print(f"  Язык: {params['language']}")
        print()

async def test_multiple_products_and_locations():
    """
    Тест поиска поставщиков для разных товаров и локаций
    """
    print("=== Тест поиска поставщиков для разных товаров и локаций ===")
    
    orchestrator = SearchOrchestrator()
    
    # Тест 1: Laptop в США
    print("\n--- Тест 1: Laptop в США ---")
    request_us = SupplierSearchRequest(
        search_query="laptop",
        target_location="United States",
        amount="100",
        search_strategy="direct",
        search_type="organic",
        max_results=5,
        delivery_date="25.07.2025"
    )
    
    print(f"Поисковый запрос: {request_us.search_query}")
    print(f"Локация: {request_us.target_location}")
    
    try:
        search_queries = await orchestrator._generate_supplier_queries(
            request_us.search_query,
            request_us.amount,
            {"country_code": "us", "language": "en", "location": request_us.target_location},
            request_us.search_strategy,
            request_us.delivery_date
        )
        search_queries = search_queries[:2]  # Только 2 запроса
        
        print("Запросы:")
        for i, query in enumerate(search_queries, 1):
            print(f"{i}. {query}")
        
        supplier_results = []
        for query in search_queries:
            result = await orchestrator.serp_service.search_suppliers(
                query,
                product_data=None,
                max_results=request_us.max_results,
                search_type=request_us.search_type,
                location=request_us.target_location
            )
            supplier_results.extend(
                await orchestrator._analyze_supplier_results([result], request_us.search_query, {"country_code": "us", "language": "en"})
            )
        
        # Убираем дубликаты
        unique_suppliers = {}
        for supplier in supplier_results:
            key = supplier.website or supplier.name
            if key not in unique_suppliers:
                unique_suppliers[key] = supplier
        supplier_results = list(unique_suppliers.values())
        
        print(f"Найдено поставщиков: {len(supplier_results)}")
        if supplier_results:
            for i, supplier in enumerate(supplier_results[:3], 1):  # Показываем первые 3
                print(f"{i}. {supplier.name}")
                print(f"   Веб-сайт: {supplier.website}")
                if supplier.contact_info:
                    print(f"   Контакт: {supplier.contact_info}")
                if supplier.email_addresses:
                    print(f"   Email: {supplier.email_addresses}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
    
    # Тест 2: Clothing во Франции
    print("\n--- Тест 2: Clothing во Франции ---")
    request_fr = SupplierSearchRequest(
        search_query="clothing",
        target_location="France",
        amount="200",
        search_strategy="wholesale",
        search_type="organic",
        max_results=5,
        delivery_date="25.07.2025"
    )
    
    print(f"Поисковый запрос: {request_fr.search_query}")
    print(f"Локация: {request_fr.target_location}")
    
    try:
        search_queries = await orchestrator._generate_supplier_queries(
            request_fr.search_query,
            request_fr.amount,
            {"country_code": "fr", "language": "fr", "location": request_fr.target_location},
            request_fr.search_strategy,
            request_fr.delivery_date
        )
        search_queries = search_queries[:2]  # Только 2 запроса
        
        print("Запросы:")
        for i, query in enumerate(search_queries, 1):
            print(f"{i}. {query}")
        
        supplier_results = []
        for query in search_queries:
            result = await orchestrator.serp_service.search_suppliers(
                query,
                product_data=None,
                max_results=request_fr.max_results,
                search_type=request_fr.search_type,
                location=request_fr.target_location
            )
            supplier_results.extend(
                await orchestrator._analyze_supplier_results([result], request_fr.search_query, {"country_code": "fr", "language": "fr"})
            )
        
        # Убираем дубликаты
        unique_suppliers = {}
        for supplier in supplier_results:
            key = supplier.website or supplier.name
            if key not in unique_suppliers:
                unique_suppliers[key] = supplier
        supplier_results = list(unique_suppliers.values())
        
        print(f"Найдено поставщиков: {len(supplier_results)}")
        if supplier_results:
            for i, supplier in enumerate(supplier_results[:3], 1):  # Показываем первые 3
                print(f"{i}. {supplier.name}")
                print(f"   Веб-сайт: {supplier.website}")
                if supplier.contact_info:
                    print(f"   Контакт: {supplier.contact_info}")
                if supplier.email_addresses:
                    print(f"   Email: {supplier.email_addresses}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    # Запускаем тесты
    asyncio.run(test_location_service())
    asyncio.run(test_multiple_products_and_locations()) 