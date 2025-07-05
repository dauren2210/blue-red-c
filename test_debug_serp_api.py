import pytest
import asyncio
from app.services.serp_service import SerpService
from app.core.config import settings

@pytest.mark.asyncio
async def test_debug_serp_api():
    """Тест для отладки SerpAPI напрямую"""
    serp_service = SerpService()
    
    # Тестовые запросы
    test_queries = [
        "smartphone suppliers Germany",
        "smartphone поставщики Германия",
        "buy smartphone delivery 2024-07-15",
        "smartphone оптовые поставщики de"
    ]
    
    print("\n=== Testing SerpAPI Directly ===")
    print(f"API Key: {settings.SERP_API_KEY[:10]}...")
    print(f"Engine: {settings.SERP_ENGINE}")
    print(f"Max Results: {settings.MAX_SEARCH_RESULTS}")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query}")
        
        try:
            # Выполняем поиск с правильными параметрами
            results = await serp_service.search(query, country_code="de", language="de")
            
            print(f"Results count: {len(results.results) if results else 0}")
            
            if results and results.results:
                print("First 3 results:")
                for j, result in enumerate(results.results[:3], 1):
                    print(f"  {j}. {result.title}")
                    print(f"     Link: {result.link}")
                    print(f"     Snippet: {result.snippet[:100]}...")
            else:
                print("No results found")
                
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n=== SerpAPI test completed ===")

@pytest.mark.asyncio
async def test_debug_serp_api_simple():
    """Простой тест SerpAPI с базовым запросом"""
    serp_service = SerpService()
    
    print("\n=== Simple SerpAPI Test ===")
    print(f"API Key: {settings.SERP_API_KEY[:10]}...")
    
    try:
        # Простой запрос с правильными параметрами
        results = await serp_service.search("laptop suppliers", country_code="us", language="en")
        
        print(f"Results count: {len(results.results) if results else 0}")
        
        if results and results.results:
            print("First result:")
            result = results.results[0]
            print(f"  Title: {result.title}")
            print(f"  Link: {result.link}")
            print(f"  Snippet: {result.snippet}")
        else:
            print("No results found")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print(f"\n=== Simple test completed ===")

@pytest.mark.asyncio
async def test_debug_serp_api_raw():
    """Тест с прямым вызовом SerpAPI для отладки"""
    from serpapi import GoogleSearch
    
    print("\n=== Raw SerpAPI Test ===")
    print(f"API Key: {settings.SERP_API_KEY[:10]}...")
    
    try:
        # Прямой вызов SerpAPI
        params = {
            "api_key": settings.SERP_API_KEY,
            "engine": "google",
            "q": "laptop suppliers",
            "num": 3,
            "gl": "us",
            "hl": "en"
        }
        
        print(f"Search params: {params}")
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        print(f"Raw results keys: {list(results.keys())}")
        
        if "organic_results" in results:
            organic_results = results["organic_results"]
            print(f"Organic results count: {len(organic_results)}")
            
            if organic_results:
                print("First result:")
                result = organic_results[0]
                print(f"  Title: {result.get('title', 'N/A')}")
                print(f"  Link: {result.get('link', 'N/A')}")
                print(f"  Snippet: {result.get('snippet', 'N/A')}")
        else:
            print("No organic_results in response")
            print(f"Available keys: {list(results.keys())}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print(f"\n=== Raw test completed ===") 