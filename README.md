# Blue-Red-C Supplier Search API

Интеллектуальная система поиска поставщиков с интеграцией LLM (OpenAI) и Serp API для генерации оптимизированных поисковых запросов.

## 🎯 Назначение

Система предназначена для автоматического поиска реальных поставщиков товаров, сырья и услуг с использованием ИИ для улучшения поисковых запросов. Специализирована на поиске поставщиков с контактной информацией, каталогами товаров и прайс-листами.

## 🚀 Возможности

- 🤖 **LLM-улучшенные запросы**: Автоматическая генерация поисковых запросов с помощью OpenAI
- 🔍 **Многостратегический поиск**: 4 различные стратегии поиска поставщиков
- 📍 **Локальный поиск**: Специализация на поставщиках в Казахстане (Алматы)
- 🏢 **Доверенные источники**: Поиск по проверенным B2B платформам
- 📊 **Аналитика результатов**: Анализ и рекомендации по улучшению поиска
- 🗄️ **MongoDB хранение**: Сохранение истории поисков и аналитики
- 📋 **Каталоги и прайс-листы**: Поиск документов с технической информацией

## 📁 Структура проекта

```
blue-red-c/
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── health.py                    # Проверка здоровья API
│   │       └── supplier_search.py           # API для поиска поставщиков
│   ├── core/
│   │   └── config.py                        # Конфигурация приложения
│   ├── db/
│   │   └── mongodb.py                       # Подключение к MongoDB
│   ├── models/                              # Pydantic модели
│   │   └── __init__.py
│   ├── services/                            # Бизнес-логика
│   │   ├── supplier_query_generator.py      # Генератор запросов для поставщиков
│   │   ├── serp_service.py                  # Сервис для работы с Serp API
│   │   └── supplier_search_orchestrator.py  # Оркестратор поиска поставщиков
│   └── main.py                              # Точка входа приложения
├── requirements.txt                         # Зависимости Python
├── env.example                              # Пример конфигурации
└── README.md                                # Документация
```

## 🛠️ Установка и настройка

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd blue-red-c
   ```

2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Настройте переменные окружения:**
   ```bash
   cp env.example .env
   # Отредактируйте .env файл с вашими API ключами
   ```

4. **Запустите MongoDB** (локально или используйте MongoDB Atlas)

5. **Запустите приложение:**
   ```bash
   uvicorn app.main:app --reload
   ```

## 🔗 API Endpoints

### Поиск поставщиков

- `POST /api/v1/supplier-search/search` - Основной поиск поставщиков с LLM
- `POST /api/v1/supplier-search/multi-strategy` - Многостратегический поиск
- `POST /api/v1/supplier-search/quick-search` - Быстрый поиск с минимальными параметрами
- `POST /api/v1/supplier-search/generate-queries` - Генерация запросов без поиска

### Аналитика и история

- `GET /api/v1/supplier-search/history` - История поисков поставщиков
- `GET /api/v1/supplier-search/analytics` - Аналитика поиска
- `GET /api/v1/supplier-search/health` - Проверка здоровья сервиса
- `GET /api/v1/supplier-search/example-request` - Пример запроса

## 📝 Примеры использования

### Основной поиск поставщиков

```python
import requests

# Запрос на поиск поставщиков
response = requests.post("http://localhost:8000/api/v1/supplier-search/search", json={
    "supplier_data": {
        "product_name": "электронные компоненты",
        "amount": "1000 штук",
        "date": "2025-01-15"
    },
    "supplier_type": "manufacturer",
    "target_location": "Almaty, Kazakhstan",
    "delivery_date": "2025-07-10",
    "required_services": [
        "catalog",
        "price_list",
        "contact_info",
        "technical_specs"
    ],
    "trusted_sources": [
        "alibaba.com",
        "globalsources.com",
        "made-in-china.com"
    ],
    "additional_keywords": [
        "wholesale",
        "bulk order"
    ]
})

print(response.json())
```

### Быстрый поиск

```python
# Быстрый поиск с минимальными параметрами
response = requests.post("http://localhost:8000/api/v1/supplier-search/quick-search", params={
    "product_name": "стальные трубы",
    "target_location": "Almaty, Kazakhstan",
    "supplier_type": "wholesaler",
    "delivery_date": "2025-07-10"
})

print(response.json())
```

### Многостратегический поиск

```python
response = requests.post("http://localhost:8000/api/v1/supplier-search/multi-strategy", json={
    "supplier_data": {
        "product_name": "пищевые ингредиенты"
    },
    "target_location": "Almaty, Kazakhstan",
    "required_services": ["catalog", "price_list", "contact_info"]
})

print(response.json())
```

## 🎯 Стратегии поиска

### 1. Прямой поиск поставщиков
- Фокус на контактную информацию
- Поиск каталогов и прайс-листов
- Географическая привязка к Алматы

### 2. Поиск по каталогам
- Поиск PDF каталогов
- Технические характеристики
- Условия поставки

### 3. Доверенные источники
- Alibaba.com
- GlobalSources.com
- Made-in-China.com
- ExportersIndia.com

### 4. Локальный поиск
- Поставщики в Казахстане
- Региональные дистрибьюторы
- Доставка в Алматы

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `MONGODB_URL` | URL подключения к MongoDB | `mongodb://localhost:27017` |
| `DB_NAME` | Название базы данных | `blue-red-c` |
| `SERP_API_KEY` | API ключ для Serp API | - |
| `SERP_ENGINE` | Поисковая система | `google` |
| `OPENAI_API_KEY` | API ключ для OpenAI | - |
| `OPENAI_MODEL` | Модель OpenAI | `gpt-3.5-turbo` |
| `MAX_SEARCH_RESULTS` | Максимальное количество результатов | `3` |
| `SEARCH_TIMEOUT` | Таймаут поиска (секунды) | `60` |

## 🏗️ Архитектура

### Сервисы

1. **SupplierQueryGenerator** - Генерация поисковых запросов с помощью LLM
2. **SerpService** - Работа с Serp API для выполнения поиска
3. **SupplierSearchOrchestrator** - Координация между сервисами

### Модели данных

- `SupplierData` - Данные о продукте/услуге
- `SupplierSearchRequest` - Запрос на поиск поставщиков
- `GeneratedSearchQuery` - Сгенерированный поисковый запрос
- `SupplierSearchResponse` - Ответ с результатами поиска

## 🔍 Типы поставщиков

- `manufacturer` - Производители
- `wholesaler` - Оптовые поставщики
- `distributor` - Дистрибьюторы
- `logistics` - Логистические компании
- `raw_materials` - Поставщики сырья
- `food` - Поставщики продуктов питания
- `goods` - Поставщики товаров

## 📊 Аналитика

Система предоставляет аналитику по:
- Общему количеству поисков
- Популярным продуктам
- Статистике по локациям
- Эффективности стратегий поиска
- Наличию контактной информации
- Количеству локальных поставщиков

## 🚀 Разработка

### Добавление новых стратегий поиска

1. Добавьте новую стратегию в `SupplierQueryGenerator`
2. Реализуйте соответствующий метод в `SupplierSearchOrchestrator`
3. Обновите API эндпоинты при необходимости

### Расширение анализа результатов

1. Добавьте новые метрики в `analyze_supplier_results`
2. Обновите модели данных
3. Расширьте рекомендации

## 📄 Лицензия

MIT License 