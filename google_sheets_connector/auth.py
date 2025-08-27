"""
Модуль аутентификации для Google Sheets API
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
import pickle

logger = logging.getLogger(__name__)

class GoogleSheetsAuth:
    """Класс для управления аутентификацией Google Sheets API"""
    
    # Область доступа для Google Sheets API
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]
    
    def __init__(self, credentials_dir: str = "credentials"):
        """
        Инициализация модуля аутентификации
        
        Args:
            credentials_dir: Директория для хранения файлов аутентификации
        """
        self.credentials_dir = credentials_dir
        self.credentials = None
        self._ensure_credentials_dir()
    
    def _ensure_credentials_dir(self):
        """Создает директорию для credentials если её нет"""
        if not os.path.exists(self.credentials_dir):
            os.makedirs(self.credentials_dir)
            logger.info(f"Создана директория для credentials: {self.credentials_dir}")
    
    def authenticate_service_account(self, service_account_file: str) -> bool:
        """
        Аутентификация через Service Account (рекомендуется для автоматизации)
        
        Args:
            service_account_file: Путь к JSON файлу с ключами Service Account
            
        Returns:
            bool: True если аутентификация успешна
        """
        try:
            if not os.path.exists(service_account_file):
                logger.error(f"Файл Service Account не найден: {service_account_file}")
                return False
            
            self.credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=self.SCOPES
            )
            
            logger.info("Успешная аутентификация через Service Account")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации Service Account: {e}")
            return False
    
    def authenticate_oauth(self, client_secrets_file: str, token_file: str = None) -> bool:
        """
        Аутентификация через OAuth2 (для пользовательского доступа)
        
        Args:
            client_secrets_file: Путь к JSON файлу с OAuth2 credentials
            token_file: Путь к файлу с сохраненными токенами
            
        Returns:
            bool: True если аутентификация успешна
        """
        try:
            if token_file is None:
                token_file = os.path.join(self.credentials_dir, "token.pickle")
            
            # Проверяем существующие токены
            if os.path.exists(token_file):
                with open(token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # Если токены недействительны или отсутствуют
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Обновляем токены
                    self.credentials.refresh(Request())
                    logger.info("Токены обновлены")
                else:
                    # Запускаем OAuth2 flow
                    if not os.path.exists(client_secrets_file):
                        logger.error(f"Файл client secrets не найден: {client_secrets_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secrets_file, self.SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                    logger.info("Получены новые токены через OAuth2")
                
                # Сохраняем токены
                with open(token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
                    logger.info(f"Токены сохранены в {token_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка OAuth2 аутентификации: {e}")
            return False
    
    def get_credentials(self) -> Optional[Credentials]:
        """
        Возвращает объект credentials для использования в API
        
        Returns:
            Credentials объект или None если аутентификация не выполнена
        """
        return self.credentials
    
    def is_authenticated(self) -> bool:
        """
        Проверяет, выполнена ли аутентификация
        
        Returns:
            bool: True если аутентификация активна
        """
        return self.credentials is not None and self.credentials.valid
    
    def revoke_credentials(self, token_file: str = None):
        """
        Отзывает credentials и удаляет сохраненные токены
        
        Args:
            token_file: Путь к файлу с токенами
        """
        try:
            if self.credentials:
                # Отзываем токены на сервере Google
                self.credentials.revoke(Request())
                self.credentials = None
                logger.info("Credentials отозваны")
            
            # Удаляем локальный файл с токенами
            if token_file is None:
                token_file = os.path.join(self.credentials_dir, "token.pickle")
            
            if os.path.exists(token_file):
                os.remove(token_file)
                logger.info(f"Файл токенов удален: {token_file}")
                
        except Exception as e:
            logger.error(f"Ошибка при отзыве credentials: {e}")

def create_service_account_info() -> Dict[str, Any]:
    """
    Возвращает пример структуры для Service Account JSON файла
    
    Returns:
        Dict с примером структуры Service Account
    """
    return {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
        "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
    }

def save_example_service_account(filepath: str):
    """
    Сохраняет пример Service Account файла для настройки
    
    Args:
        filepath: Путь для сохранения примера
    """
    example_data = create_service_account_info()
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(example_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Пример Service Account сохранен: {filepath}")
    print(f"\n📋 Пример Service Account файла создан: {filepath}")
    print("🔧 Замените значения на реальные данные из Google Cloud Console")
