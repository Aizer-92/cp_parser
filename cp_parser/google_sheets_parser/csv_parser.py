#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Парсер мастер-таблицы CSV для извлечения Google Sheets ссылок
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from loguru import logger

class CSVMasterTableParser:
    """Парсер мастер-таблицы с Google Sheets ссылками"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = Path(csv_file_path)
        self.logger = logger
        
        # Индексы колонок в CSV (начиная с 0)
        self.COLUMNS = {
            'min_quantity': 0,        # Тираж MIN
            'max_quantity': 1,        # Тираж MAX  
            'products': 2,            # Товары
            'min_price_usd': 3,       # Минимальная стоимость в $
            'max_price_usd': 4,       # Максимальная стоимость в $
            'min_price_rub': 5,       # Минимальная в рублях
            'max_price_rub': 6,       # Максимальная в рублях 
            'description': 7,         # Описание
            'project_name': 8,        # Название (техническое)
            'empty_col': 9,           # Пустая колонка
            'managers': 10,           # Исполнители
            'google_sheets_url': 11,  # Ссылка на GoogleSheets
            'created_date': 12,       # Дата создания
            'client_name': 13,        # Контрагент  
            'region': 14              # Регион
        }
    
    def extract_sheet_id_from_url(self, url: str) -> Optional[str]:
        """Извлекает ID таблицы из Google Sheets URL"""
        if not url or 'docs.google.com/spreadsheets' not in url:
            return None
            
        try:
            # Паттерн для извлечения ID из URL
            pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            self.logger.error(f"Ошибка извлечения ID из URL {url}: {e}")
            return None
    
    def clean_project_name(self, name: str) -> str:
        """Очищает техническое название проекта для использования как имя файла"""
        if not name:
            return "untitled"
            
        # Убираем спецсимволы и лишние пробелы
        cleaned = re.sub(r'[<>:"/\\|?*]', '', name.strip())
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Ограничиваем длину
        if len(cleaned) > 100:
            cleaned = cleaned[:100]
            
        return cleaned or "untitled"
    
    def parse_csv_file(self) -> List[Dict]:
        """Парсит CSV файл и извлекает все Google Sheets ссылки с метаданными"""
        
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"CSV файл не найден: {self.csv_file_path}")
        
        sheets_data = []
        
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                
                # Пропускаем заголовок
                header = next(csv_reader, None)
                if not header:
                    raise ValueError("CSV файл пустой или поврежден")
                
                self.logger.info(f"📊 Найден заголовок с {len(header)} колонками")
                
                row_count = 0
                valid_sheets = 0
                
                for row_num, row in enumerate(csv_reader, start=2):  # Начинаем с 2-й строки
                    row_count += 1
                    
                    try:
                        # Проверяем, что в строке достаточно колонок
                        if len(row) < max(self.COLUMNS.values()) + 1:
                            self.logger.warning(f"Строка {row_num}: недостаточно колонок ({len(row)})")
                            continue
                        
                        # Извлекаем Google Sheets URL
                        sheets_url = row[self.COLUMNS['google_sheets_url']].strip()
                        if not sheets_url or 'docs.google.com/spreadsheets' not in sheets_url:
                            continue
                        
                        # Извлекаем Sheet ID
                        sheet_id = self.extract_sheet_id_from_url(sheets_url)
                        if not sheet_id:
                            self.logger.warning(f"Строка {row_num}: не удалось извлечь Sheet ID из {sheets_url}")
                            continue
                        
                        # Извлекаем метаданные
                        project_name = row[self.COLUMNS['project_name']].strip()
                        client_name = row[self.COLUMNS['client_name']].strip()
                        region = row[self.COLUMNS['region']].strip()
                        created_date = row[self.COLUMNS['created_date']].strip()
                        managers = row[self.COLUMNS['managers']].strip()
                        
                        # Создаем имя файла по Google Sheets ID для поиска в мастер-таблице
                        filename = f"{sheet_id}.xlsx"
                        
                        # Формируем запись
                        sheet_data = {
                            'row_number': row_num,
                            'sheet_id': sheet_id,
                            'google_sheets_url': sheets_url,
                            'project_name': project_name,
                            'filename': filename,
                            'client_name': client_name,
                            'region': region,
                            'created_date': created_date,
                            'managers': managers,
                            'min_quantity': self._safe_int(row[self.COLUMNS['min_quantity']]),
                            'max_quantity': self._safe_int(row[self.COLUMNS['max_quantity']]),
                            'min_price_usd': self._safe_float(row[self.COLUMNS['min_price_usd']]),
                            'max_price_usd': self._safe_float(row[self.COLUMNS['max_price_usd']]),
                            'products': row[self.COLUMNS['products']].strip()
                        }
                        
                        sheets_data.append(sheet_data)
                        valid_sheets += 1
                        
                    except Exception as e:
                        self.logger.error(f"Ошибка в строке {row_num}: {e}")
                        continue
                
                self.logger.info(f"✅ Обработано строк: {row_count}")
                self.logger.info(f"✅ Найдено валидных Google Sheets: {valid_sheets}")
                
        except Exception as e:
            self.logger.error(f"Ошибка чтения CSV файла: {e}")
            raise
        
        return sheets_data
    
    def _safe_int(self, value: str) -> Optional[int]:
        """Безопасное преобразование в int"""
        try:
            if not value or value.strip() == '-':
                return None
            return int(float(value.replace(',', '').replace(' ', '')))
        except:
            return None
    
    def _safe_float(self, value: str) -> Optional[float]:
        """Безопасное преобразование в float"""
        try:
            if not value or value.strip() == '-':
                return None
            return float(value.replace(',', '.').replace(' ', ''))
        except:
            return None
    
    def get_statistics(self, sheets_data: List[Dict]) -> Dict:
        """Получает статистику по парсингу"""
        
        if not sheets_data:
            return {'total': 0}
        
        stats = {
            'total': len(sheets_data),
            'regions': {},
            'clients_count': len(set(item['client_name'] for item in sheets_data if item['client_name'])),
            'date_range': {
                'earliest': None,
                'latest': None
            }
        }
        
        # Статистика по регионам
        for item in sheets_data:
            region = item['region'] or 'Не указан'
            stats['regions'][region] = stats['regions'].get(region, 0) + 1
        
        # Диапазон дат
        dates = [item['created_date'] for item in sheets_data if item['created_date']]
        if dates:
            stats['date_range']['earliest'] = min(dates)
            stats['date_range']['latest'] = max(dates)
        
        return stats

def main():
    """Тестовый запуск парсера"""
    
    # Путь к CSV файлу
    csv_path = Path(__file__).parent.parent.parent / "Копилка Презентаций - Просчеты .csv"
    
    if not csv_path.exists():
        print(f"❌ CSV файл не найден: {csv_path}")
        return
    
    try:
        parser = CSVMasterTableParser(str(csv_path))
        sheets_data = parser.parse_csv_file()
        stats = parser.get_statistics(sheets_data)
        
        print(f"\\n📊 СТАТИСТИКА ПАРСИНГА CSV:")
        print(f"✅ Всего Google Sheets: {stats['total']}")
        print(f"✅ Уникальных клиентов: {stats['clients_count']}")
        print(f"✅ Диапазон дат: {stats['date_range']['earliest']} - {stats['date_range']['latest']}")
        print(f"\\n🌍 По регионам:")
        for region, count in stats['regions'].items():
            print(f"  {region}: {count}")
        
        # Показываем первые 5 записей
        print(f"\\n📋 ПЕРВЫЕ 5 ЗАПИСЕЙ:")
        for i, item in enumerate(sheets_data[:5], 1):
            print(f"{i}. {item['filename']}")
            print(f"   Проект: {item['project_name']}")
            print(f"   Клиент: {item['client_name']}")
            print(f"   URL: {item['google_sheets_url'][:60]}...")
            print()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
