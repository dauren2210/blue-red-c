#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы SerpService с официальным клиентом SerpApi
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.serp_service import SerpService
from app.services.location_service import LocationService
from app.models import ProductData

async def test_basic_search():
    """Тестирует базовый поиск"""
    print("=== Тестирование базового поиска ===\n")
    
    serp_service = SerpService()
    
    # Простой поиск
    try:
        result = await serp_service.search(
            query="поставщики электроники",
            search_type="web",
            max_results=5
        )
        
        print(f"Запрос: {result.query}")
        print(f"Время поиска: {result.search_time:.2f} сек")
        print(f"Найдено результатов: {result.total_results}")
        print(f"Движок: {result.engine}")
        
        print("\nРезультаты:")
        for i, search_result in enumerate(result.results[:3], 1):
            print(f"{i}. {search_result.title}")
            print(f"   URL: {search_result.link}")
            print(f"   Сниппет: {search_result.snippet[:100]}...")
            print()
            
    except Exception as e:
        print(f"❌ Ошибка при поиске: {e}")
        import traceback
        traceback.print_exc()

async def test_location_based_search():
    """Тестирует поиск с учетом локации"""
    print("=== Тестирование поиска с локацией ===\n")
    
    serp_service = SerpService()
    location_service = LocationService()
    
    # Создаем тестовый продукт
    product_data = ProductData(
        product_name="Электронные компоненты",
        amount="1000 штук",
        date_and_time="2024-01-15T10:00:00",
        location="Алматы, Казахстан"
    )
    
    try:
        # Поиск с автоматическим определением локации
        result = await serp_service.search_suppliers(
            query="электронные компоненты поставщик",
            product_data=product_data,
            max_results=5
        )
        
        print(f"Запрос: {result.query}")
        print(f"Время поиска: {result.search_time:.2f} сек")
        print(f"Найдено результатов: {result.total_results}")
        
        print("\nРезультаты:")
        for i, search_result in enumerate(result.results[:3], 1):
            print(f"{i}. {search_result.title}")
            print(f"   URL: {search_result.link}")
            print(f"   Источник: {search_result.source}")
            print()
            
    except Exception as e:
        print(f"❌ Ошибка при поиске с локацией: {e}")
        import traceback
        traceback.print_exc()

async def test_multilingual_search():
    """Тестирует многоязычный поиск"""
    print("=== Тестирование многоязычного поиска ===\n")
    
    serp_service = SerpService()
    
    # Создаем тестовый продукт
    product_data = ProductData(
        product_name="Строительные материалы",
        amount="50 тонн",
        date_and_time="2024-01-20T14:30:00",
        location="Москва, Россия"
    )
    
    try:
        # Многоязычный поиск
        results = await serp_service.multilingual_search(
            query="строительные материалы поставщик",
            product_data=product_data,
            max_results=3
        )
        
        print(f"Выполнено поисков на {len(results)} языках")
        
        for i, result in enumerate(results, 1):
            print(f"\nПоиск {i}:")
            print(f"  Запрос: {result.query}")
            print(f"  Время: {result.search_time:.2f} сек")
            print(f"  Результатов: {result.total_results}")
            
            if result.results:
                print(f"  Первый результат: {result.results[0].title}")
            
    except Exception as e:
        print(f"❌ Ошибка при многоязычном поиске: {e}")
        import traceback
        traceback.print_exc()

async def test_location_detection():
    """Тестирует определение локации"""
    print("=== Тестирование определения локации ===\n")
    
    location_service = LocationService()
    
    test_locations = [
        "Алматы, Казахстан",
        "Москва, Россия",
        "Киев, Украина",
        "Berlin, Germany",
        "New York, USA"
    ]
    
    for location in test_locations:
        try:
            location_info = location_service.detect_country_and_language(location)
            print(f"Локация: {location}")
            print(f"  Страна: {location_info['country_code']}")
            print(f"  Язык: {location_info['language']}")
            print(f"  Основной язык: {location_info['primary_language']}")
            
            # Получаем языки для поиска
            search_languages = location_service.get_search_languages(location_info['country_code'])
            print(f"  Языки для поиска: {search_languages}")
            print()
            
        except Exception as e:
            print(f"❌ Ошибка для локации {location}: {e}")

async def test_search_with_fallback():
    """Тестирует поиск с fallback"""
    print("=== Тестирование поиска с fallback ===\n")
    
    serp_service = SerpService()
    
    try:
        # Поиск с fallback
        result = await serp_service.search_with_fallback(
            query="очень специфичный запрос который может не найти результатов",
            search_type="web",
            max_results=5
        )
        
        print(f"Запрос: {result.query}")
        print(f"Время поиска: {result.search_time:.2f} сек")
        print(f"Найдено результатов: {result.total_results}")
        
        if result.results:
            print(f"Первый результат: {result.results[0].title}")
        else:
            print("Результатов не найдено (fallback сработал)")
            
    except Exception as e:
        print(f"❌ Ошибка при поиске с fallback: {e}")
        import traceback
        traceback.print_exc()

async def test_european_scenarios():
    """Тестирует поиск поставщиков для европейских стран"""
    print("=== Тестирование европейских сценариев ===\n")
    
    serp_service = SerpService()
    european_cases = [
        ("electronics supplier", "Berlin, Germany"),
        ("food wholesaler", "Paris, France"),
        ("machinery distributor", "Rome, Italy"),
        ("building materials supplier", "Madrid, Spain"),
        ("chemical products supplier", "Warsaw, Poland"),
    ]
    
    for query, location in european_cases:
        product_data = ProductData(
            product_name=query,
            amount="",
            date_and_time=None,
            location=location
        )
        print(f"\nСтрана/город: {location}")
        print(f"Запрос: {query}")
        try:
            result = await serp_service.search_suppliers(
                query=query,
                product_data=product_data,
                max_results=3
            )
            print(f"  Время поиска: {result.search_time:.2f} сек")
            print(f"  Найдено результатов: {result.total_results}")
            for i, search_result in enumerate(result.results, 1):
                print(f"    {i}. {search_result.title}")
                print(f"       URL: {search_result.link}")
                print(f"       Сниппет: {search_result.snippet[:100]}...")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование SerpService с официальным клиентом SerpApi\n")
    
    try:
        # Проверяем наличие API ключа
        from app.core.config import settings
        if not settings.SERP_API_KEY:
            print("⚠️  ВНИМАНИЕ: SERP_API_KEY не установлен!")
            print("Для полноценного тестирования установите переменную окружения SERP_API_KEY")
            print("Тесты будут выполняться с пустыми результатами\n")
        
        await test_location_detection()
        await test_basic_search()
        await test_location_based_search()
        await test_multilingual_search()
        await test_search_with_fallback()
        await test_european_scenarios()
        
        print("✅ Все тесты завершены!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 