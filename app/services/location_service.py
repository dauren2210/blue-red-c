import re
from typing import Dict, Tuple, Optional
from app.models import ProductData

class LocationService:
    """Сервис для определения страны и языка на основе локации"""
    
    def __init__(self):
        # Словарь стран и их языков
        self.country_language_map = {
            # СНГ страны
            "kazakhstan": {"country_code": "kz", "language": "ru", "primary_language": "ru"},
            "казахстан": {"country_code": "kz", "language": "ru", "primary_language": "ru"},
            "almaty": {"country_code": "kz", "language": "ru", "primary_language": "ru"},
            "алматы": {"country_code": "kz", "language": "ru", "primary_language": "ru"},
            "astana": {"country_code": "kz", "language": "ru", "primary_language": "ru"},
            "астана": {"country_code": "kz", "language": "ru", "primary_language": "ru"},
            
            "russia": {"country_code": "ru", "language": "ru", "primary_language": "ru"},
            "россия": {"country_code": "ru", "language": "ru", "primary_language": "ru"},
            "moscow": {"country_code": "ru", "language": "ru", "primary_language": "ru"},
            "москва": {"country_code": "ru", "language": "ru", "primary_language": "ru"},
            "saint petersburg": {"country_code": "ru", "language": "ru", "primary_language": "ru"},
            "санкт-петербург": {"country_code": "ru", "language": "ru", "primary_language": "ru"},
            
            "ukraine": {"country_code": "ua", "language": "uk", "primary_language": "uk"},
            "украина": {"country_code": "ua", "language": "uk", "primary_language": "uk"},
            "kyiv": {"country_code": "ua", "language": "uk", "primary_language": "uk"},
            "киев": {"country_code": "ua", "language": "uk", "primary_language": "uk"},
            
            "belarus": {"country_code": "by", "language": "ru", "primary_language": "ru"},
            "беларусь": {"country_code": "by", "language": "ru", "primary_language": "ru"},
            "minsk": {"country_code": "by", "language": "ru", "primary_language": "ru"},
            "минск": {"country_code": "by", "language": "ru", "primary_language": "ru"},
            
            "uzbekistan": {"country_code": "uz", "language": "uz", "primary_language": "uz"},
            "узбекистан": {"country_code": "uz", "language": "uz", "primary_language": "uz"},
            "tashkent": {"country_code": "uz", "language": "uz", "primary_language": "uz"},
            "ташкент": {"country_code": "uz", "language": "uz", "primary_language": "uz"},
            
            "kyrgyzstan": {"country_code": "kg", "language": "ky", "primary_language": "ky"},
            "кыргызстан": {"country_code": "kg", "language": "ky", "primary_language": "ky"},
            "bishkek": {"country_code": "kg", "language": "ky", "primary_language": "ky"},
            "бишкек": {"country_code": "kg", "language": "ky", "primary_language": "ky"},
            
            "tajikistan": {"country_code": "tj", "language": "tg", "primary_language": "tg"},
            "таджикистан": {"country_code": "tj", "language": "tg", "primary_language": "tg"},
            "dushanbe": {"country_code": "tj", "language": "tg", "primary_language": "tg"},
            "душанбе": {"country_code": "tj", "language": "tg", "primary_language": "tg"},
            
            "turkmenistan": {"country_code": "tm", "language": "tk", "primary_language": "tk"},
            "туркменистан": {"country_code": "tm", "language": "tk", "primary_language": "tk"},
            "ashgabat": {"country_code": "tm", "language": "tk", "primary_language": "tk"},
            "ашхабад": {"country_code": "tm", "language": "tk", "primary_language": "tk"},
            
            "azerbaijan": {"country_code": "az", "language": "az", "primary_language": "az"},
            "азербайджан": {"country_code": "az", "language": "az", "primary_language": "az"},
            "baku": {"country_code": "az", "language": "az", "primary_language": "az"},
            "баку": {"country_code": "az", "language": "az", "primary_language": "az"},
            
            "armenia": {"country_code": "am", "language": "hy", "primary_language": "hy"},
            "армения": {"country_code": "am", "language": "hy", "primary_language": "hy"},
            "yerevan": {"country_code": "am", "language": "hy", "primary_language": "hy"},
            "ереван": {"country_code": "am", "language": "hy", "primary_language": "hy"},
            
            "georgia": {"country_code": "ge", "language": "ka", "primary_language": "ka"},
            "грузия": {"country_code": "ge", "language": "ka", "primary_language": "ka"},
            "tbilisi": {"country_code": "ge", "language": "ka", "primary_language": "ka"},
            "тбилиси": {"country_code": "ge", "language": "ka", "primary_language": "ka"},
            
            "moldova": {"country_code": "md", "language": "ro", "primary_language": "ro"},
            "молдова": {"country_code": "md", "language": "ro", "primary_language": "ro"},
            "chisinau": {"country_code": "md", "language": "ro", "primary_language": "ro"},
            "кишинев": {"country_code": "md", "language": "ro", "primary_language": "ro"},
            
            # Европа
            "germany": {"country_code": "de", "language": "de", "primary_language": "de"},
            "deutschland": {"country_code": "de", "language": "de", "primary_language": "de"},
            "berlin": {"country_code": "de", "language": "de", "primary_language": "de"},
            
            "france": {"country_code": "fr", "language": "fr", "primary_language": "fr"},
            "paris": {"country_code": "fr", "language": "fr", "primary_language": "fr"},
            
            "italy": {"country_code": "it", "language": "it", "primary_language": "it"},
            "italia": {"country_code": "it", "language": "it", "primary_language": "it"},
            "rome": {"country_code": "it", "language": "it", "primary_language": "it"},
            
            "spain": {"country_code": "es", "language": "es", "primary_language": "es"},
            "madrid": {"country_code": "es", "language": "es", "primary_language": "es"},
            
            "united kingdom": {"country_code": "gb", "language": "en", "primary_language": "en"},
            "uk": {"country_code": "gb", "language": "en", "primary_language": "en"},
            "london": {"country_code": "gb", "language": "en", "primary_language": "en"},
            
            "poland": {"country_code": "pl", "language": "pl", "primary_language": "pl"},
            "warsaw": {"country_code": "pl", "language": "pl", "primary_language": "pl"},
            
            # Азия
            "china": {"country_code": "cn", "language": "zh", "primary_language": "zh"},
            "beijing": {"country_code": "cn", "language": "zh", "primary_language": "zh"},
            "shanghai": {"country_code": "cn", "language": "zh", "primary_language": "zh"},
            
            "japan": {"country_code": "jp", "language": "ja", "primary_language": "ja"},
            "tokyo": {"country_code": "jp", "language": "ja", "primary_language": "ja"},
            
            "south korea": {"country_code": "kr", "language": "ko", "primary_language": "ko"},
            "seoul": {"country_code": "kr", "language": "ko", "primary_language": "ko"},
            
            "india": {"country_code": "in", "language": "en", "primary_language": "en"},
            "mumbai": {"country_code": "in", "language": "en", "primary_language": "en"},
            "delhi": {"country_code": "in", "language": "en", "primary_language": "en"},
            
            "turkey": {"country_code": "tr", "language": "tr", "primary_language": "tr"},
            "istanbul": {"country_code": "tr", "language": "tr", "primary_language": "tr"},
            "ankara": {"country_code": "tr", "language": "tr", "primary_language": "tr"},
            
            # Америка
            "united states": {"country_code": "us", "language": "en", "primary_language": "en"},
            "usa": {"country_code": "us", "language": "en", "primary_language": "en"},
            "new york": {"country_code": "us", "language": "en", "primary_language": "en"},
            "los angeles": {"country_code": "us", "language": "en", "primary_language": "en"},
            
            "canada": {"country_code": "ca", "language": "en", "primary_language": "en"},
            "toronto": {"country_code": "ca", "language": "en", "primary_language": "en"},
            "vancouver": {"country_code": "ca", "language": "en", "primary_language": "en"},
            
            "brazil": {"country_code": "br", "language": "pt", "primary_language": "pt"},
            "sao paulo": {"country_code": "br", "language": "pt", "primary_language": "pt"},
            "rio de janeiro": {"country_code": "br", "language": "pt", "primary_language": "pt"},
            
            "mexico": {"country_code": "mx", "language": "es", "primary_language": "es"},
            "mexico city": {"country_code": "mx", "language": "es", "primary_language": "es"},
        }
        
        # Дополнительные языки для многоязычных стран
        self.additional_languages = {
            "kz": ["kk", "en"],  # Казахстан: казахский, английский
            "ru": ["en"],        # Россия: английский
            "ua": ["ru", "en"],  # Украина: русский, английский
            "by": ["en"],        # Беларусь: английский
            "uz": ["ru", "en"],  # Узбекистан: русский, английский
            "kg": ["ru", "en"],  # Кыргызстан: русский, английский
            "tj": ["ru", "en"],  # Таджикистан: русский, английский
            "tm": ["ru", "en"],  # Туркменистан: русский, английский
            "az": ["ru", "en"],  # Азербайджан: русский, английский
            "am": ["ru", "en"],  # Армения: русский, английский
            "ge": ["ru", "en"],  # Грузия: русский, английский
            "md": ["ru", "en"],  # Молдова: русский, английский
        }
    
    def detect_country_and_language(self, location: str) -> Dict[str, str]:
        """
        Определяет страну и язык на основе локации
        """
        if not location:
            return {"country_code": "kz", "language": "ru", "primary_language": "ru"}
        
        location_lower = location.lower().strip()
        
        # Очищаем локацию от лишних символов
        location_clean = re.sub(r'[^\w\s]', ' ', location_lower)
        location_clean = re.sub(r'\s+', ' ', location_clean).strip()
        
        # Разбиваем на слова для поиска
        words = location_clean.split()
        
        # Ищем совпадения
        for word in words:
            if word in self.country_language_map:
                country_info = self.country_language_map[word]
                return {
                    "country_code": country_info["country_code"],
                    "language": country_info["language"],
                    "primary_language": country_info["primary_language"]
                }
        
        # Если не нашли точное совпадение, ищем частичные совпадения
        for key, value in self.country_language_map.items():
            if key in location_lower:
                return {
                    "country_code": value["country_code"],
                    "language": value["language"],
                    "primary_language": value["primary_language"]
                }
        
        # По умолчанию возвращаем Казахстан
        return {"country_code": "kz", "language": "ru", "primary_language": "ru"}
    
    def get_search_languages(self, country_code: str) -> list[str]:
        """
        Возвращает список языков для поиска в данной стране
        """
        languages = []
        
        # Основной язык страны
        for key, value in self.country_language_map.items():
            if value["country_code"] == country_code:
                languages.append(value["language"])
                break
        
        # Дополнительные языки
        if country_code in self.additional_languages:
            languages.extend(self.additional_languages[country_code])
        
        # Убираем дубликаты
        return list(set(languages))
    
    def get_search_parameters(self, product_data: ProductData) -> Dict[str, str]:
        """
        Получает параметры поиска на основе данных продукта
        """
        location = product_data.location or ""
        country_info = self.detect_country_and_language(location)
        
        return {
            "country_code": country_info["country_code"],
            "language": country_info["language"],
            "primary_language": country_info["primary_language"],
            "search_languages": self.get_search_languages(country_info["country_code"])
        }
    
    def get_multilingual_search_params(self, product_data: ProductData) -> list[Dict[str, str]]:
        """
        Возвращает параметры для многоязычного поиска
        """
        base_params = self.get_search_parameters(product_data)
        search_languages = base_params["search_languages"]
        
        search_params = []
        for lang in search_languages:
            search_params.append({
                "country_code": base_params["country_code"],
                "language": lang,
                "primary_language": base_params["primary_language"]
            })
        
        return search_params
    
    def is_cis_country(self, country_code: str) -> bool:
        """
        Проверяет, является ли страна частью СНГ
        """
        cis_countries = ["kz", "ru", "ua", "by", "uz", "kg", "tj", "tm", "az", "am", "ge", "md"]
        return country_code in cis_countries
    
    def get_local_sources(self, country_code: str) -> list[str]:
        """
        Возвращает локальные источники для поиска в зависимости от страны
        """
        local_sources_map = {
            "kz": ["kz.all.biz", "kz.exportpages.com", "kz.tradekey.com"],
            "ru": ["ru.all.biz", "ru.exportpages.com", "ru.tradekey.com"],
            "ua": ["ua.all.biz", "ua.exportpages.com", "ua.tradekey.com"],
            "by": ["by.all.biz", "by.exportpages.com", "by.tradekey.com"],
            "uz": ["uz.all.biz", "uz.exportpages.com", "uz.tradekey.com"],
            "kg": ["kg.all.biz", "kg.exportpages.com", "kg.tradekey.com"],
            "tj": ["tj.all.biz", "tj.exportpages.com", "tj.tradekey.com"],
            "tm": ["tm.all.biz", "tm.exportpages.com", "tm.tradekey.com"],
            "az": ["az.all.biz", "az.exportpages.com", "az.tradekey.com"],
            "am": ["am.all.biz", "am.exportpages.com", "am.tradekey.com"],
            "ge": ["ge.all.biz", "ge.exportpages.com", "ge.tradekey.com"],
            "md": ["md.all.biz", "md.exportpages.com", "md.tradekey.com"],
        }
        
        return local_sources_map.get(country_code, [])
    
    def get_trusted_sources_by_region(self, country_code: str) -> list[str]:
        """
        Возвращает доверенные источники в зависимости от региона
        """
        if self.is_cis_country(country_code):
            return ["alibaba.com", "globalsources.com", "made-in-china.com", "indiamart.com"]
        elif country_code in ["cn", "jp", "kr"]:
            return ["alibaba.com", "globalsources.com", "made-in-china.com", "tradekey.com"]
        elif country_code in ["us", "ca"]:
            return ["alibaba.com", "globalsources.com", "made-in-china.com", "exportersindia.com"]
        elif country_code in ["de", "fr", "it", "es", "gb"]:
            return ["alibaba.com", "globalsources.com", "made-in-china.com", "tradekey.com"]
        else:
            return ["alibaba.com", "globalsources.com", "made-in-china.com"] 