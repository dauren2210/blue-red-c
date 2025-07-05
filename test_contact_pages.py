#!/usr/bin/env python3
"""
Тест для проверки поиска контактных страниц поставщиков
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.serp_service import SerpService
from app.services.location_service import LocationService
from app.models import ProductData
from app.services.search_orchestrator import SearchOrchestrator

async def test_contact_pages_search():
    """Тестирует поиск контактных страниц поставщиков"""
    print("=== Тестирование поиска контактных страниц ===\n")
    
    serp_service = SerpService()
    
    # Тестовые сценарии для разных стран и языков
    test_cases = [
        {
            "query": "electronics supplier",
            "location": "Berlin, Germany",
            "expected_language": "de",
            "description": "Немецкие поставщики электроники"
        },
        {
            "query": "food wholesaler",
            "location": "Paris, France", 
            "expected_language": "fr",
            "description": "Французские оптовики продуктов"
        },
        {
            "query": "machinery distributor",
            "location": "Rome, Italy",
            "expected_language": "it", 
            "description": "Итальянские дистрибьюторы техники"
        },
        {
            "query": "building materials supplier",
            "location": "Madrid, Spain",
            "expected_language": "es",
            "description": "Испанские поставщики стройматериалов"
        },
        {
            "query": "chemical products supplier",
            "location": "Warsaw, Poland",
            "expected_language": "pl",
            "description": "Польские поставщики химии"
        },
        {
            "query": "электронные компоненты поставщик",
            "location": "Алматы, Казахстан",
            "expected_language": "ru",
            "description": "Казахстанские поставщики электроники"
        },
        {
            "query": "поставщики строительных материалов",
            "location": "Москва, Россия",
            "expected_language": "ru",
            "description": "Российские поставщики стройматериалов"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"Тест {i}: {case['description']}")
        print(f"Запрос: {case['query']}")
        print(f"Локация: {case['location']}")
        print(f"Ожидаемый язык: {case['expected_language']}")
        
        # Показываем сгенерированные запросы из search_query
        contact_keywords = serp_service._get_contact_keywords(case['expected_language'])
        enhanced_query = serp_service._enhance_query_for_contact_pages(case['query'], contact_keywords)
        
        print(f"Ключевые слова для контактов ({case['expected_language']}): {contact_keywords[:5]}")
        print(f"Сгенерированный запрос: {enhanced_query}")
        
        # Показываем разбор запроса
        print("Разбор запроса:")
        print(f"  Search Query: {case['query']}")
        print(f"  Контактные термины: {' OR '.join([f'\"{kw}\"' for kw in contact_keywords[:5]])}")
        print(f"  Поставщики + контакты: supplier OR vendor OR distributor OR wholesaler OR manufacturer OR phone OR email OR address")
        print(f"  Итоговый: {enhanced_query}")
        print()
        
        # Создаем тестовый продукт
        product_data = ProductData(
            product_name=case['query'],
            amount="",
            date_and_time=None,
            location=case['location']
        )
        
        try:
            # Выполняем поиск контактных страниц
            result = await serp_service.search_suppliers(
                query=case['query'],
                product_data=product_data,
                max_results=5
            )
            
            print(f"  Время поиска: {result.search_time:.2f} сек")
            print(f"  Найдено результатов: {result.total_results}")
            
            # Анализируем результаты на наличие контактной информации
            contact_results = 0
            for j, search_result in enumerate(result.results, 1):
                title_lower = search_result.title.lower()
                snippet_lower = search_result.snippet.lower()
                
                # Проверяем наличие контактных ключевых слов
                contact_indicators = [
                    "contact", "kontakt", "contatti", "contacto", "контакт",
                    "phone", "telefon", "telefono", "teléfono", "телефон",
                    "email", "e-mail", "email", "email", "email",
                    "address", "adresse", "indirizzo", "dirección", "адрес"
                ]
                
                has_contact_info = any(indicator in title_lower or indicator in snippet_lower 
                                     for indicator in contact_indicators)
                
                if has_contact_info:
                    contact_results += 1
                    print(f"    ✅ {j}. {search_result.title}")
                    print(f"       URL: {search_result.link}")
                    print(f"       Сниппет: {search_result.snippet[:150]}...")
                else:
                    print(f"    ⚠️  {j}. {search_result.title}")
                    print(f"       URL: {search_result.link}")
                    print(f"       Сниппет: {search_result.snippet[:150]}...")
            
            print(f"  Результатов с контактной информацией: {contact_results}/{result.total_results}")
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 80)

async def test_contact_keywords():
    """Тестирует генерацию ключевых слов для контактных страниц"""
    print("=== Тестирование ключевых слов для контактных страниц ===\n")
    
    serp_service = SerpService()
    
    test_languages = ["ru", "en", "de", "fr", "it", "es", "uk", "kk"]
    
    for language in test_languages:
        print(f"Язык: {language}")
        contact_keywords = serp_service._get_contact_keywords(language)
        print(f"  Ключевые слова: {contact_keywords[:5]}...")  # Показываем первые 5
        print()

async def test_enhanced_queries():
    """Тестирует улучшенные запросы для поиска контактных страниц"""
    print("=== Тестирование улучшенных запросов ===\n")
    
    serp_service = SerpService()
    
    test_queries = [
        "electronics supplier",
        "food wholesaler", 
        "machinery distributor",
        "электронные компоненты поставщик",
        "поставщики строительных материалов"
    ]
    
    for query in test_queries:
        print(f"Оригинальный запрос: {query}")
        
        # Тестируем для русского языка
        contact_keywords = serp_service._get_contact_keywords("ru")
        enhanced_query = serp_service._enhance_query_for_contact_pages(query, contact_keywords)
        print(f"Улучшенный запрос (RU): {enhanced_query}")
        
        # Тестируем для английского языка
        contact_keywords_en = serp_service._get_contact_keywords("en")
        enhanced_query_en = serp_service._enhance_query_for_contact_pages(query, contact_keywords_en)
        print(f"Улучшенный запрос (EN): {enhanced_query_en}")
        print("-" * 60)

async def test_search_query_queries():
    """Тестирует генерацию запросов из search_query"""
    print("=== Тестирование генерации запросов из search_query ===\n")
    
    from app.services.search_orchestrator import SearchOrchestrator
    
    orchestrator = SearchOrchestrator()
    
    test_queries = [
        {
            "search_query": "Электронные компоненты",
            "amount": "1000 штук",
            "location": "Алматы, Казахстан",
            "expected_language": "ru"
        },
        {
            "search_query": "electronics supplier",
            "amount": "500 units",
            "location": "Berlin, Germany",
            "expected_language": "de"
        },
        {
            "search_query": "food wholesaler",
            "amount": "200 kg",
            "location": "Paris, France",
            "expected_language": "fr"
        }
    ]
    
    for i, query_data in enumerate(test_queries, 1):
        print(f"Тест {i}: {query_data['search_query']}")
        print(f"Локация: {query_data['location']}")
        print(f"Количество: {query_data['amount']}")
        
        # Создаем ProductData для определения локации
        product_data = ProductData(
            product_name=query_data['search_query'],
            amount=query_data['amount'],
            date_and_time="2024-01-15T10:00:00",
            location=query_data['location']
        )
        
        # Определяем параметры локации
        location_service = LocationService()
        location_params = location_service.get_search_parameters(product_data)
        
        # Генерируем запросы для разных стратегий
        strategies = ["direct", "catalog", "trusted", "local"]
        
        for strategy in strategies:
            queries = await orchestrator._generate_supplier_queries(
                query_data['search_query'],
                query_data['amount'],
                location_params,
                strategy
            )
            
            print(f"  Стратегия '{strategy}':")
            for j, query in enumerate(queries, 1):
                print(f"    {j}. {query}")
            print()
        
        # Генерируем запросы на основе данных продукта
        supplier_type, keywords = orchestrator._analyze_product_for_supplier_search(product_data)
        product_queries = await orchestrator._generate_product_based_queries(
            query_data['search_query'],
            supplier_type,
            keywords,
            location_params,
            query_data['amount'],
            True  # is_urgent
        )
        
        print(f"  Запросы на основе search_query:")
        print(f"    Тип поставщика: {supplier_type}")
        print(f"    Ключевые слова: {keywords}")
        for j, query in enumerate(product_queries, 1):
            print(f"    {j}. {query}")
        
        print("-" * 80)

async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование поиска контактных страниц поставщиков\n")
    
    try:
        await test_contact_keywords()
        await test_enhanced_queries()
        await test_search_query_queries()
        await test_contact_pages_search()
        
        print("✅ Все тесты завершены!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 