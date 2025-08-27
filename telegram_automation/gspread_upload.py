#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузка CSV файлов в Google Sheets через gspread
"""

import os
import sys
import logging
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GSpreadUploader:
    """Класс для загрузки данных в Google Sheets через gspread"""
    
    def __init__(self, credentials_file: str = "../google_sheets_connector/credentials/service_account.json"):
        """
        Инициализация загрузчика
        
        Args:
            credentials_file: Путь к файлу сервисного аккаунта
        """
        self.credentials_file = credentials_file
        self.client = None
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация через сервисный аккаунт"""
        try:
            # Настройка области доступа
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Загружаем учетные данные
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scope
            )
            
            # Создаем клиент
            self.client = gspread.authorize(credentials)
            logger.info("✅ Аутентификация в Google Sheets API успешна")
            
        except Exception as e:
            logger.error(f"❌ Ошибка аутентификации: {e}")
            raise
    
    def upload_csv_to_sheet(self, csv_file: str, spreadsheet_id: str, sheet_name: str) -> bool:
        """
        Загружает CSV файл в Google Sheets
        
        Args:
            csv_file: Путь к CSV файлу
            spreadsheet_id: ID Google таблицы
            sheet_name: Название листа
            
        Returns:
            bool: True если успешно
        """
        try:
            logger.info(f"📤 Загрузка файла {csv_file} в лист '{sheet_name}'...")
            
            # Открываем таблицу
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Проверяем существование листа
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                logger.info(f"🧹 Очистка существующего листа '{sheet_name}'")
                worksheet.clear()
            except gspread.WorksheetNotFound:
                logger.info(f"📄 Создание нового листа '{sheet_name}'")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            
            # Читаем CSV файл
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            logger.info(f"📊 Прочитано {len(df)} строк из CSV файла")
            
            # Подготавливаем данные
            data = [df.columns.tolist()] + df.values.tolist()
            
            # Загружаем данные
            worksheet.update('A1', data)
            logger.info(f"✅ Данные успешно загружены в лист '{sheet_name}'")
            
            # Форматируем заголовки
            self._format_headers(worksheet, len(df.columns))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки: {e}")
            return False
    
    def _format_headers(self, worksheet, num_columns: int):
        """Форматирует заголовки таблицы"""
        try:
            # Форматирование заголовков (жирный шрифт, фон)
            worksheet.format('A1:{}1'.format(chr(65 + num_columns - 1)), {
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
            })
            logger.info("✅ Заголовки отформатированы")
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка форматирования заголовков: {e}")

def main():
    """Главная функция"""
    try:
        # Параметры
        spreadsheet_id = "1qcWRIw1sGqrzfVGPBylKF0hubeczmIWQ9uVbmLQpYKs"
        
        # Создаем загрузчик
        uploader = GSpreadUploader()
        
        # Список файлов для загрузки
        files_to_upload = [
            ("temp_Единый_список_задач.csv", "Единый_список_задач_Июль_Август_2025"),
            ("temp_Сводка.csv", "Сводка_Июль_Август_2025"),
            ("temp_По_руководителям.csv", "По_руководителям_Июль_Август_2025")
        ]
        
        success_count = 0
        
        for csv_file, sheet_name in files_to_upload:
            if os.path.exists(csv_file):
                success = uploader.upload_csv_to_sheet(csv_file, spreadsheet_id, sheet_name)
                if success:
                    success_count += 1
                    logger.info(f"✅ {csv_file} -> {sheet_name}")
                else:
                    logger.error(f"❌ Ошибка загрузки {csv_file}")
            else:
                logger.error(f"❌ Файл {csv_file} не найден")
        
        if success_count > 0:
            logger.info(f"🎉 Успешно загружено {success_count} из {len(files_to_upload)} файлов!")
            logger.info(f"📊 Ссылка: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        else:
            logger.error("❌ Не удалось загрузить ни одного файла")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
