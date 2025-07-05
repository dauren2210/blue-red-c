#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации работы LocationService
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.location_service import LocationService
from app.models import ProductData

def test_location_detection():
    """Тестирует определение локации"""
    print("=== Тестирование определения локации ===\n")
    
    location_service = LocationService()
    
    test_locations = [
        "Алматы, Казахстан",
        "Москва, Россия", 
        "Киев, Украина",
        "Ташкент, Узбекистан",
        "Бишкек, Кыргызстан",
        "Berlin, Germany",
        "Paris, France",
        "New York, USA",
        "Beijing, China",
        "Tokyo, Japan",
        "Просто Алматы",
        "Улица Абая, 150, Алматы",
        "Невский проспект, Санкт-Петербург",
        "Крещатик, Киев",
        "Просто город без страны"
    ]
    
    for location in test_locations:
        result = location_service.detect_country_and_language(location)
        print(f"Локация: {location}")
        print(f"  Страна: {result['country_code']}")
        print(f"  Язык: {result['language']}")
        print(f"  Основной язык: {result['primary_language']}")
        
        # Получаем дополнительные языки
        search_languages = location_service.get_search_languages(result['country_code'])
        print(f"  Языки для поиска: {search_languages}")
        
        # Проверяем, является ли страна СНГ
        is_cis = location_service.is_cis_country(result['country_code'])
        print(f"  СНГ страна: {is_cis}")
        
        # Получаем локальные источники
        local_sources = location_service.get_local_sources(result['country_code'])
        print(f"  Локальные источники: {local_sources[:3]}...")  # Показываем первые 3
        
        print()

def test_product_data():
    """Тестирует работу с данными продуктов"""
    print("=== Тестирование работы с данными продуктов ===\n")
    
    location_service = LocationService()
    
    # Создаем тестовые продукты
    test_products = [
        ProductData(
            product_name="Электронные компоненты",
            amount="1000 штук",
            date_and_time="2024-01-15T10:00:00",
            location="Алматы, Казахстан"
        ),
        ProductData(
            product_name="Строительные материалы",
            amount="50 тонн",
            date_and_time="2024-01-20T14:30:00", 
            location="Москва, Россия"
        ),
        ProductData(
            product_name="Одежда оптом",
            amount="500 единиц",
            date_and_time="2024-01-25T09:15:00",
            location="Киев, Украина"
        ),
        ProductData(
            product_name="Продукты питания",
            amount="200 кг",
            date_and_time="2024-01-30T16:45:00",
            location="Ташкент, Узбекистан"
        )
    ]
    
    for i, product in enumerate(test_products, 1):
        print(f"Продукт {i}: {product.product_name}")
        print(f"  Количество: {product.amount}")
        print(f"  Дата: {product.date_and_time}")
        print(f"  Локация: {product.location}")
        
        # Получаем параметры поиска
        search_params = location_service.get_search_parameters(product)
        print(f"  Параметры поиска:")
        print(f"    Страна: {search_params['country_code']}")
        print(f"    Язык: {search_params['language']}")
        print(f"    Основной язык: {search_params['primary_language']}")
        print(f"    Языки для поиска: {search_params['search_languages']}")
        
        # Получаем параметры для многоязычного поиска
        multilingual_params = location_service.get_multilingual_search_params(product)
        print(f"  Многоязычный поиск ({len(multilingual_params)} языков):")
        for j, params in enumerate(multilingual_params, 1):
            print(f"    {j}. {params['language']} ({params['country_code']})")
        
        print()

def test_regional_sources():
    """Тестирует региональные источники"""
    print("=== Тестирование региональных источников ===\n")
    
    location_service = LocationService()
    
    test_countries = ["kz", "ru", "ua", "by", "uz", "kg", "de", "fr", "us", "cn"]
    
    for country in test_countries:
        print(f"Страна: {country}")
        
        # Локальные источники
        local_sources = location_service.get_local_sources(country)
        print(f"  Локальные источники: {local_sources}")
        
        # Доверенные источники по региону
        trusted_sources = location_service.get_trusted_sources_by_region(country)
        print(f"  Доверенные источники: {trusted_sources}")
        
        # Проверяем СНГ
        is_cis = location_service.is_cis_country(country)
        print(f"  СНГ: {is_cis}")
        
        print()

def main():
    """Основная функция"""
    print("🚀 Тестирование LocationService\n")
    
    try:
        test_location_detection()
        test_product_data() 
        test_regional_sources()
        
        print("✅ Все тесты завершены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 