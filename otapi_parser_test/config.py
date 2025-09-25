"""
Конфигурация для OTAPI парсера
"""
import os
from typing import Dict, Any

class OTAPIConfig:
    """Конфигурация OTAPI"""
    
    # Базовый URL API
    BASE_URL = "http://otapi.net/service-json/BatchGetItemFullInfo"
    
    # Параметры API (из примера)
    API_PARAMS = {
        "instanceKey": "5bde2d7b-250e-4a48-ad4c-ec18d4e40bed",
        "language": "ru",
        "signature": "",
        "timestamp": "",
        "sessionId": "",
        "itemParameters": "",
        "blockList": "Description"  # Исключаем описание для экономии трафика
    }
    
    # Лимиты
    MAX_REQUESTS = 300  # Общий лимит
    TEST_REQUESTS = 3   # Количество тестовых запросов
    
    # Задержки между запросами (в секундах)
    REQUEST_DELAY = 0.5
    ERROR_DELAY = 2.0
    
    # Пути к файлам
    DATA_DIR = "data"
    RESULTS_DIR = "data/results"
    TEST_URLS_FILE = "data/test_urls.json"
    
    @classmethod
    def get_api_url(cls, item_id: str) -> str:
        """Формирует URL для API запроса"""
        params = cls.API_PARAMS.copy()
        params["itemId"] = f"abb-{item_id}"
        
        # Формируем query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{cls.BASE_URL}?{query_string}"
    
    @classmethod
    def create_directories(cls):
        """Создает необходимые директории"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.RESULTS_DIR, exist_ok=True)

