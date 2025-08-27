"""
Основной коннектор для работы с Google Sheets API
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth import GoogleSheetsAuth

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleSheetsConnector:
    """Основной класс для работы с Google Sheets"""
    
    def __init__(self, credentials_dir: str = "credentials"):
        """
        Инициализация коннектора
        
        Args:
            credentials_dir: Директория с файлами аутентификации
        """
        self.auth = GoogleSheetsAuth(credentials_dir)
        self.service = None
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """Загружает конфигурацию из config.json"""
        config_path = "config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("Конфигурация загружена")
            except Exception as e:
                logger.warning(f"Ошибка загрузки конфигурации: {e}")
    
    def authenticate_service_account(self, service_account_file: str) -> bool:
        """
        Аутентификация через Service Account
        
        Args:
            service_account_file: Путь к JSON файлу Service Account
            
        Returns:
            bool: True если успешно
        """
        if self.auth.authenticate_service_account(service_account_file):
            try:
                self.service = build('sheets', 'v4', credentials=self.auth.get_credentials())
                logger.info("Google Sheets API сервис инициализирован")
                return True
            except Exception as e:
                logger.error(f"Ошибка инициализации API сервиса: {e}")
                return False
        return False
    
    def authenticate_oauth(self, client_secrets_file: str) -> bool:
        """
        Аутентификация через OAuth2
        
        Args:
            client_secrets_file: Путь к JSON файлу с OAuth2 credentials
            
        Returns:
            bool: True если успешно
        """
        if self.auth.authenticate_oauth(client_secrets_file):
            try:
                self.service = build('sheets', 'v4', credentials=self.auth.get_credentials())
                logger.info("Google Sheets API сервис инициализирован")
                return True
            except Exception as e:
                logger.error(f"Ошибка инициализации API сервиса: {e}")
                return False
        return False
    
    def is_connected(self) -> bool:
        """
        Проверяет подключение к API
        
        Returns:
            bool: True если подключен
        """
        return self.service is not None and self.auth.is_authenticated()
    
    def _ensure_connected(self):
        """Проверяет подключение и выбрасывает исключение если не подключен"""
        if not self.is_connected():
            raise ConnectionError("Не подключен к Google Sheets API. Выполните аутентификацию.")
    
    def get_spreadsheet_info(self, spreadsheet_id: str) -> Dict[str, Any]:
        """
        Получает информацию о таблице
        
        Args:
            spreadsheet_id: ID таблицы
            
        Returns:
            Dict с информацией о таблице
        """
        if self.service is None:
            raise ConnectionError("Не подключен к Google Sheets API. Выполните аутентификацию.")
        
        try:
            result = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            
            info = {
                'title': result.get('properties', {}).get('title', ''),
                'sheets': [],
                'url': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            }
            
            for sheet in result.get('sheets', []):
                sheet_props = sheet.get('properties', {})
                info['sheets'].append({
                    'title': sheet_props.get('title', ''),
                    'id': sheet_props.get('sheetId', 0),
                    'rows': sheet_props.get('gridProperties', {}).get('rowCount', 0),
                    'columns': sheet_props.get('gridProperties', {}).get('columnCount', 0)
                })
            
            return info
            
        except HttpError as e:
            logger.error(f"Ошибка получения информации о таблице: {e}")
            raise
    
    def read_range(self, spreadsheet_id: str, range_name: str, 
                   value_render_option: str = 'FORMATTED_VALUE') -> List[List[str]]:
        """
        Читает данные из указанного диапазона
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон в формате 'Sheet1!A1:C10'
            value_render_option: Как отображать значения (FORMATTED_VALUE, UNFORMATTED_VALUE, FORMULA)
            
        Returns:
            List[List[str]]: Данные из диапазона
        """
        if self.service is None:
            raise ConnectionError("Не подключен к Google Sheets API. Выполните аутентификацию.")
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueRenderOption=value_render_option
            ).execute()
            
            values = result.get('values', [])
            logger.info(f"Прочитано {len(values)} строк из {range_name}")
            return values
            
        except HttpError as e:
            logger.error(f"Ошибка чтения данных: {e}")
            raise
    
    def read_to_dataframe(self, spreadsheet_id: str, range_name: str, 
                         header_row: bool = True) -> pd.DataFrame:
        """
        Читает данные в pandas DataFrame
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон для чтения
            header_row: Использовать первую строку как заголовки
            
        Returns:
            pd.DataFrame: Данные в формате DataFrame
        """
        data = self.read_range(spreadsheet_id, range_name)
        
        if not data:
            return pd.DataFrame()
        
        if header_row and len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
        else:
            df = pd.DataFrame(data)
        
        return df
    
    def write_range(self, spreadsheet_id: str, range_name: str, values: List[List[Any]], 
                   value_input_option: str = 'RAW') -> bool:
        """
        Записывает данные в указанный диапазон
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон для записи
            values: Данные для записи
            value_input_option: Как интерпретировать данные (RAW, USER_ENTERED)
            
        Returns:
            bool: True если успешно
        """
        self._ensure_connected()
        
        try:
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            logger.info(f"Обновлено {updated_cells} ячеек в {range_name}")
            return True
            
        except HttpError as e:
            logger.error(f"Ошибка записи данных: {e}")
            return False
    
    def write_dataframe(self, spreadsheet_id: str, range_name: str, df: pd.DataFrame, 
                       include_header: bool = True) -> bool:
        """
        Записывает pandas DataFrame в таблицу
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон для записи
            df: DataFrame для записи
            include_header: Включать заголовки колонок
            
        Returns:
            bool: True если успешно
        """
        # Конвертируем DataFrame в список списков
        values = []
        
        if include_header:
            values.append(df.columns.tolist())
        
        # Конвертируем все значения в строки, заменяем NaN на пустые строки
        for _, row in df.iterrows():
            row_values = []
            for value in row:
                if pd.isna(value):
                    row_values.append('')
                else:
                    row_values.append(str(value))
            values.append(row_values)
        
        return self.write_range(spreadsheet_id, range_name, values, 'USER_ENTERED')
    
    def append_rows(self, spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> bool:
        """
        Добавляет строки в конец таблицы
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон (обычно название листа)
            values: Данные для добавления
            
        Returns:
            bool: True если успешно
        """
        self._ensure_connected()
        
        try:
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updated_cells = result.get('updates', {}).get('updatedCells', 0)
            logger.info(f"Добавлено {len(values)} строк, обновлено {updated_cells} ячеек")
            return True
            
        except HttpError as e:
            logger.error(f"Ошибка добавления строк: {e}")
            return False
    
    def clear_range(self, spreadsheet_id: str, range_name: str) -> bool:
        """
        Очищает данные в указанном диапазоне
        
        Args:
            spreadsheet_id: ID таблицы
            range_name: Диапазон для очистки
            
        Returns:
            bool: True если успешно
        """
        self._ensure_connected()
        
        try:
            result = self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            logger.info(f"Диапазон {range_name} очищен")
            return True
            
        except HttpError as e:
            logger.error(f"Ошибка очистки диапазона: {e}")
            return False
    
    def create_sheet(self, spreadsheet_id: str, sheet_title: str, 
                    rows: int = 1000, columns: int = 26) -> Optional[int]:
        """
        Создает новый лист в таблице
        
        Args:
            spreadsheet_id: ID таблицы
            sheet_title: Название нового листа
            rows: Количество строк
            columns: Количество колонок
            
        Returns:
            int: ID созданного листа или None при ошибке
        """
        self._ensure_connected()
        
        try:
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_title,
                            'gridProperties': {
                                'rowCount': rows,
                                'columnCount': columns
                            }
                        }
                    }
                }]
            }
            
            result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']
            logger.info(f"Создан лист '{sheet_title}' с ID {sheet_id}")
            return sheet_id
            
        except HttpError as e:
            logger.error(f"Ошибка создания листа: {e}")
            return None
    
    def get_config_spreadsheet(self, key: str) -> Optional[str]:
        """
        Получает ID таблицы из конфигурации
        
        Args:
            key: Ключ в конфигурации
            
        Returns:
            str: ID таблицы или None
        """
        return self.config.get(key)
    
    def save_config(self, config: Dict[str, str]):
        """
        Сохраняет конфигурацию в файл
        
        Args:
            config: Словарь с конфигурацией
        """
        self.config.update(config)
        
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("Конфигурация сохранена")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")

# Утилитарные функции

def create_example_config() -> Dict[str, str]:
    """Создает пример конфигурации"""
    return {
        "health_tracking": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        "finance_tracking": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms", 
        "learning_progress": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        "project_management": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    }

def save_example_config():
    """Сохраняет пример конфигурации"""
    config = create_example_config()
    
    with open("config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("📋 Пример конфигурации создан: config.json")
    print("🔧 Замените ID таблиц на ваши реальные ID")
