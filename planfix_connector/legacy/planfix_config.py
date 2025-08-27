"""
Единая конфигурация для Planfix API коннектора
Объединяет все доступы в одном месте
"""

import json
import os
from typing import Dict, Any, Optional


class PlanfixUnifiedConfig:
    """Единая конфигурация для всех API Planfix"""
    
    def __init__(self, config_file: str = "planfix_config.json"):
        self.config_file = config_file
        self.config_path = os.path.join(os.path.dirname(__file__), config_file)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из файла"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                return self._get_default_config()
        else:
            # Создаем конфигурацию по умолчанию
            config = self._get_default_config()
            self._save_config(config)
            return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Единая конфигурация с актуальными доступами"""
        return {
            "rest_api": {
                "base_url": "https://megamindru.planfix.ru/rest",
                "auth_token": "721aa965ab2df731fddbe2dc866cb7f4",
                "timeout": 30,
                "max_retries": 3
            },
            "xml_api": {
                "base_url": "https://apiru.planfix.ru/xml",
                "api_key": "f6d50e651c89858b9bad67a482b3ad64",
                "private_key": "41e92c92001fb0197494520a53cb3cd6",
                "token": "dd54edbc938dfb9074f0aa1b596b5a04",
                "timeout": 30,
                "max_retries": 3
            },
            "security": {
                "read_only": True,
                "allowed_methods": ["GET"],
                "rate_limit": {
                    "requests_per_second": 1,
                    "requests_per_day": 1000
                }
            },
            "logging": {
                "level": "INFO",
                "log_requests": True,
                "log_responses": False
            },
            "export": {
                "target_statuses": [
                    "Поиск и расчет товара",
                    "КП Согласование", 
                    "КП Согласовано"
                ],
                "target_fields": [
                    "Грейд клиента",
                    "% заказа", 
                    "Сроки",
                    "Постановщик",
                    "Исполнитель", 
                    "Сложность",
                    "Расчет - Приоритет просчета",
                    "Сумма просчета",
                    "Дата перехода в статус \"КП Согласование\""
                ]
            }
        }
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    # REST API свойства
    @property
    def rest_base_url(self) -> str:
        """Базовый URL REST API"""
        return self._config["rest_api"]["base_url"]
    
    @property
    def rest_auth_token(self) -> str:
        """Токен авторизации REST API"""
        return self._config["rest_api"]["auth_token"]
    
    # XML API свойства
    @property
    def xml_base_url(self) -> str:
        """Базовый URL XML API"""
        return self._config["xml_api"]["base_url"]
    
    @property
    def xml_api_key(self) -> str:
        """API ключ для XML API"""
        return self._config["xml_api"]["api_key"]
    
    @property
    def xml_private_key(self) -> str:
        """Private key для XML API"""
        return self._config["xml_api"]["private_key"]
    
    @property
    def xml_token(self) -> str:
        """Token для XML API"""
        return self._config["xml_api"]["token"]
    
    # Общие свойства
    @property
    def timeout(self) -> int:
        """Таймаут запросов в секундах"""
        return self._config["rest_api"]["timeout"]
    
    @property
    def max_retries(self) -> int:
        """Максимальное количество повторных попыток"""
        return self._config["rest_api"]["max_retries"]
    
    @property
    def is_read_only(self) -> bool:
        """Проверка режима только чтения"""
        return self._config["security"]["read_only"]
    
    @property
    def allowed_methods(self) -> list:
        """Разрешенные HTTP методы"""
        return self._config["security"]["allowed_methods"]
    
    @property
    def rate_limit(self) -> Dict[str, int]:
        """Лимиты частоты запросов"""
        return self._config["security"]["rate_limit"]
    
    # Экспорт свойства
    @property
    def target_statuses(self) -> list:
        """Целевые статусы для экспорта"""
        return self._config["export"]["target_statuses"]
    
    @property
    def target_fields(self) -> list:
        """Целевые поля для экспорта"""
        return self._config["export"]["target_fields"]
    
    def get_rest_headers(self) -> Dict[str, str]:
        """Получение заголовков для REST API запросов"""
        return {
            "Authorization": f"Bearer {self.rest_auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PlanfixConnector/3.0 (ReadOnly)"
        }
    
    def get_xml_headers(self) -> Dict[str, str]:
        """Получение заголовков для XML API запросов"""
        return {
            "Content-Type": "application/xml",
            "Accept": "application/xml",
            "User-Agent": "PlanfixConnector/3.0 (ReadOnly)"
        }
    
    def validate_security(self, method: str) -> bool:
        """Проверка безопасности запроса"""
        if not self.is_read_only:
            return True
        return method.upper() in self.allowed_methods
    
    def update_config(self, key_path: str, value: Any) -> None:
        """Обновление значения в конфигурации"""
        keys = key_path.split('.')
        config = self._config
        
        # Навигация к нужному ключу
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Установка значения
        config[keys[-1]] = value
        
        # Сохранение
        self._save_config(self._config)


# Глобальный экземпляр единой конфигурации
config = PlanfixUnifiedConfig()
