import pytest
import asyncio
from app.services.search_orchestrator import SearchOrchestrator
from app.models import SupplierSearchRequest

@pytest.mark.asyncio
async def test_debug_search_results():
    orchestrator = SearchOrchestrator()
    
    # Создаем запрос на поиск поставщиков
    request = SupplierSearchRequest(
        search_query="laptop",
        amount="100",
        search_strategy="direct",
        target_location="United States",
        delivery_date="2025-07-25"
    )
    
    print("\n=== Starting supplier search ===")
    print(f"Search query: {request.search_query}")
    print(f"Amount: {request.amount}")
    print(f"Strategy: {request.search_strategy}")
    print(f"Date: {request.delivery_date}")
    print(f"Location: {request.target_location}")
    
    # Выполняем поиск
    response = await orchestrator.search_suppliers(request)
    
    print(f"\n=== Search Results ===")
    print(f"Session ID: {response.session_id}")
    print(f"Total suppliers found: {len(response.suppliers)}")
    print(f"Search queries used: {len(response.queries_used)}")
    
    print(f"\n=== Search Queries Used ===")
    for i, query in enumerate(response.queries_used, 1):
        print(f"{i}. {query}")
    
    print(f"\n=== Found Suppliers ===")
    for i, supplier in enumerate(response.suppliers, 1):
        print(f"\n{i}. {supplier.name}")
        print(f"   Website: {supplier.website}")
        print(f"   Type: {supplier.supplier_type}")
        print(f"   Location: {supplier.location}")
        print(f"   Contact: {supplier.contact_info}")
        print(f"   Email: {supplier.email_addresses}")
        print(f"   Rating: {supplier.rating}")
        print(f"   Verified: {supplier.verified}")
        print(f"   Source: {supplier.source}")
    
    # Проверяем, что поиск выполнился
    assert response.session_id is not None
    assert len(response.queries_used) > 0
    
    print(f"\n=== Search completed successfully ===")

@pytest.mark.asyncio
async def test_debug_product_search():
    orchestrator = SearchOrchestrator()
    
    # Создаем запрос на поиск по данным продукта
    request = SupplierSearchRequest(
        search_query="smartphone",
        amount="50",
        search_strategy="catalog",
        target_location="Germany",
        delivery_date="2024-07-15"
    )
    
    print("\n=== Starting product-based search ===")
    print(f"Product: {request.search_query}")
    print(f"Amount: {request.amount}")
    print(f"Strategy: {request.search_strategy}")
    print(f"Date: {request.delivery_date}")
    print(f"Location: {request.target_location}")
    
    # Выполняем поиск
    response = await orchestrator.search_suppliers(request)
    
    print(f"\n=== Product Search Results ===")
    print(f"Session ID: {response.session_id}")
    print(f"Total suppliers found: {len(response.suppliers)}")
    
    print(f"\n=== Search Queries Used ===")
    for i, query in enumerate(response.queries_used, 1):
        print(f"{i}. {query}")
    
    print(f"\n=== Found Suppliers ===")
    for i, supplier in enumerate(response.suppliers, 1):
        print(f"\n{i}. {supplier.name}")
        print(f"   Website: {supplier.website}")
        print(f"   Type: {supplier.supplier_type}")
        print(f"   Location: {supplier.location}")
        print(f"   Contact: {supplier.contact_info}")
        print(f"   Email: {supplier.email_addresses}")
    
    assert response.session_id is not None
    print(f"\n=== Product search completed successfully ===")

@pytest.mark.asyncio
async def test_debug_filtering():
    """Тест для отладки фильтрации результатов"""
    orchestrator = SearchOrchestrator()
    
    # Тестовые сниппеты
    test_snippets = [
        "Best Buy - Shop all new laptops at Best Buy. Compare and read reviews on the vast selection of laptop computers, notebooks and new PC and Mac laptops. Contact us at 1-800-123-4567 or email info@bestbuy.com",
        "Amazon.com: Laptops - Free shipping on qualified orders. Buy laptops online. Contact: support@amazon.com, Phone: 1-888-280-4331",
        "Dell Official Site - Buy laptops, desktops, and more. Contact Dell sales at sales@dell.com or call 1-800-999-3355",
        "HP Store - Shop HP laptops and computers. Contact HP support at support@hp.com, Phone: 1-800-474-6836",
        "Lenovo Official Store - Buy Lenovo laptops and computers. Contact: contact@lenovo.com, Tel: 1-855-253-6686"
    ]
    
    print("\n=== Testing Result Filtering ===")
    
    for i, snippet in enumerate(test_snippets, 1):
        print(f"\nTest {i}: {snippet[:100]}...")
        
        # Проверяем фильтр поставщиков
        supplier_keywords = ["поставщик", "опт", "дистрибьютор", "производитель", "купить", "продажа"]
        is_supplier = any(keyword in snippet.lower() for keyword in supplier_keywords)
        print(f"Is supplier: {is_supplier}")
        
        # Проверяем контактную информацию
        contact_info = orchestrator._extract_contact_info(snippet)
        email_addresses = orchestrator._extract_email_addresses(snippet)
        has_phone = orchestrator._has_phone_number(contact_info, snippet)
        has_email = len(email_addresses) > 0
        
        print(f"Contact info: {contact_info}")
        print(f"Emails: {email_addresses}")
        print(f"Has phone: {has_phone}")
        print(f"Has email: {has_email}")
        print(f"Would pass filter: {has_phone or has_email}")
    
    print(f"\n=== Filtering test completed ===")

@pytest.mark.asyncio
async def test_phone_extraction():
    """Тест для проверки извлечения всех номеров телефонов"""
    orchestrator = SearchOrchestrator()
    
    # Тестовые сниппеты с несколькими телефонами
    test_snippets = [
        "Контакты: +7 (495) 123-45-67, 8-800-555-35-35, тел: +7-999-888-77-66",
        "Phone: +1-555-123-4567, +1-555-987-6543, contact: 555-111-2222",
        "Телефон: 8-800-700-65-89, моб: +7-903-123-45-67, факс: 8-495-123-45-67"
    ]
    
    print("\n=== Testing Phone Number Extraction ===")
    
    for i, snippet in enumerate(test_snippets, 1):
        print(f"\nTest {i}: {snippet}")
        
        # Извлекаем контактную информацию
        contact_info = orchestrator._extract_contact_info(snippet)
        print(f"Extracted contacts: {contact_info}")
        
        # Проверяем наличие телефонов
        has_phones = orchestrator._has_phone_number(contact_info, snippet)
        print(f"Has phone numbers: {has_phones}")
        
        # Проверяем, что найдены телефоны
        assert has_phones, f"Should find phone numbers in snippet {i}"
        assert "Тел:" in contact_info, f"Should extract phone numbers in snippet {i}"
    
    print(f"\n=== Phone extraction tests completed successfully ===")

@pytest.mark.asyncio
async def test_email_extraction():
    """Тест для проверки извлечения email адресов"""
    orchestrator = SearchOrchestrator()
    
    # Тестовые сниппеты с email адресами
    test_snippets = [
        "Контакты: info@company.com, sales@company.com, тел: +7 (495) 123-45-67",
        "Email: contact@supplier.com, support@supplier.com, phone: +1-555-123-4567",
        "Связаться: info@example.ru, manager@example.ru, директор: director@example.ru"
    ]
    
    print("\n=== Testing Email Address Extraction ===")
    
    for i, snippet in enumerate(test_snippets, 1):
        print(f"\nTest {i}: {snippet}")
        
        # Извлекаем email адреса
        email_addresses = orchestrator._extract_email_addresses(snippet)
        print(f"Extracted emails: {email_addresses}")
        
        # Проверяем, что найдены email адреса
        assert len(email_addresses) > 0, f"Should find email addresses in snippet {i}"
        assert all('@' in email for email in email_addresses), f"All extracted items should be valid emails in snippet {i}"
    
    print(f"\n=== Email extraction tests completed successfully ===") 