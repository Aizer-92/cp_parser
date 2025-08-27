#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузка Excel файла в Google Sheets
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleSheetsUploader:
    """Класс для загрузки Excel файлов в Google Sheets"""
    
    def __init__(self, credentials_file: str = "../google_sheets_connector/credentials/service_account.json"):
        """
        Инициализация загрузчика
        
        Args:
            credentials_file: Путь к файлу сервисного аккаунта
        """
        self.credentials_file = credentials_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация через сервисный аккаунт"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("✅ Аутентификация в Google Sheets API успешна")
        except Exception as e:
            logger.error(f"❌ Ошибка аутентификации: {e}")
            raise
    
    def upload_excel_to_sheets(self, excel_file: str, spreadsheet_id: str, sheet_name: str = None) -> bool:
        """
        Загружает Excel файл в Google Sheets
        
        Args:
            excel_file: Путь к Excel файлу
            spreadsheet_id: ID Google таблицы
            sheet_name: Название листа (если None, создается новое)
            
        Returns:
            bool: True если успешно
        """
        try:
            logger.info(f"📤 Загрузка файла {excel_file} в Google Sheets...")
            
            # Читаем Excel файл
            excel_data = pd.read_excel(excel_file, sheet_name=None)
            logger.info(f"📊 Прочитано {len(excel_data)} листов из Excel файла")
            
            # Загружаем каждый лист
            for sheet_name_excel, df in excel_data.items():
                # Если указано конкретное название листа, используем его
                target_sheet_name = sheet_name if sheet_name else f"{sheet_name_excel}_{datetime.now().strftime('%Y%m%d')}"
                
                logger.info(f"📝 Загрузка листа '{sheet_name_excel}' как '{target_sheet_name}'...")
                
                # Создаем или очищаем лист
                self._create_or_clear_sheet(spreadsheet_id, target_sheet_name)
                
                # Загружаем данные
                self._upload_dataframe(spreadsheet_id, target_sheet_name, df)
                
                logger.info(f"✅ Лист '{target_sheet_name}' успешно загружен")
            
            logger.info(f"🎉 Все листы успешно загружены в Google Sheets!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки: {e}")
            return False
    
    def _create_or_clear_sheet(self, spreadsheet_id: str, sheet_name: str):
        """Создает новый лист или очищает существующий"""
        try:
            # Проверяем существующие листы
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            
            if sheet_name in existing_sheets:
                # Очищаем существующий лист
                logger.info(f"🧹 Очистка существующего листа '{sheet_name}'")
                self.service.spreadsheets().values().clear(
                    spreadsheetId=spreadsheet_id,
                    range=sheet_name
                ).execute()
            else:
                # Создаем новый лист
                logger.info(f"📄 Создание нового листа '{sheet_name}'")
                request = {
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': [request]}
                ).execute()
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания/очистки листа: {e}")
            raise
    
    def _upload_dataframe(self, spreadsheet_id: str, sheet_name: str, df: pd.DataFrame):
        """Загружает DataFrame в Google Sheets"""
        try:
            # Подготавливаем данные
            data = [df.columns.tolist()] + df.values.tolist()
            
            # Загружаем данные
            range_name = f"{sheet_name}!A1"
            body = {
                'values': data
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Форматируем заголовки
            self._format_headers(spreadsheet_id, sheet_name, len(df.columns))
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки данных: {e}")
            raise
    
    def _format_headers(self, spreadsheet_id: str, sheet_name: str, num_columns: int):
        """Форматирует заголовки таблицы"""
        try:
            # Форматирование заголовков
            header_format = {
                'backgroundColor': {
                    'red': 0.2,
                    'green': 0.4,
                    'blue': 0.6
                },
                'textFormat': {
                    'bold': True,
                    'foregroundColor': {
                        'red': 1.0,
                        'green': 1.0,
                        'blue': 1.0
                    }
                },
                'horizontalAlignment': 'CENTER'
            }
            
            # Применяем форматирование к первой строке
            requests = [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': self._get_sheet_id(spreadsheet_id, sheet_name),
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': num_columns
                        },
                        'cell': {
                            'userEnteredFormat': header_format
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                    }
                }
            ]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка форматирования заголовков: {e}")
    
    def _get_sheet_id(self, spreadsheet_id: str, sheet_name: str) -> int:
        """Получает ID листа по названию"""
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            raise ValueError(f"Лист '{sheet_name}' не найден")
        except Exception as e:
            logger.error(f"❌ Ошибка получения ID листа: {e}")
            raise

def main():
    """Главная функция"""
    try:
        # Параметры
        excel_file = "output/unified_task_comparison_20250827_121620.xlsx"
        spreadsheet_id = "1qcWRIw1sGqrzfVGPBylKF0hubeczmIWQ9uVbmLQpYKs"
        sheet_name = "Единый_список_задач_Июль_Август_2025"
        
        # Проверяем существование файла
        if not os.path.exists(excel_file):
            logger.error(f"❌ Файл {excel_file} не найден")
            return False
        
        # Создаем загрузчик
        uploader = GoogleSheetsUploader()
        
        # Загружаем файл
        success = uploader.upload_excel_to_sheets(excel_file, spreadsheet_id, sheet_name)
        
        if success:
            logger.info(f"🎉 Файл успешно загружен в Google Sheets!")
            logger.info(f"📊 Ссылка: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
            logger.info(f"📋 Лист: {sheet_name}")
        else:
            logger.error("❌ Ошибка загрузки файла")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
