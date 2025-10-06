#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Sheets Downloader - скачивание таблиц в формате Excel
Поддерживает батчевую обработку и альтернативные методы скачивания
"""

import os
import sys
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import json
from loguru import logger

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

class GoogleSheetsDownloader:
    """Загрузчик Google Sheets в формате Excel"""
    
    def __init__(self, output_dir: str = "production_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logger
        
        # Статистика
        self.stats = {
            'total_attempts': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'skipped_existing': 0,
            'errors': []
        }
        
        # Заголовки для запросов
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Таймауты (сокращены для избежания зависаний)
        self.download_timeout = 15  # Сокращен с 30 до 15 секунд
        self.retry_delay = 1       # Сокращен с 2 до 1 секунды
        self.max_retries = 2       # Сокращен с 3 до 2 попыток
    
    def extract_sheet_id(self, url: str) -> Optional[str]:
        """Извлекает ID таблицы из Google Sheets URL"""
        try:
            if 'docs.google.com/spreadsheets' not in url:
                return None
            
            # Паттерн: /spreadsheets/d/{SHEET_ID}/
            import re
            pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            return match.group(1) if match else None
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения Sheet ID из {url}: {e}")
            return None
    
    def build_export_url(self, sheet_id: str, format: str = 'xlsx') -> str:
        """Создает URL для экспорта Google Sheets"""
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format={format}"
    
    def download_sheet_direct(self, sheet_id: str, filename: str) -> bool:
        """Прямое скачивание через export URL"""
        
        export_url = self.build_export_url(sheet_id, 'xlsx')
        output_path = self.output_dir / filename
        
        # Проверяем, не существует ли уже файл
        if output_path.exists():
            self.logger.info(f"⏭️  Файл уже существует: {filename}")
            self.stats['skipped_existing'] += 1
            return True
        
        try:
            self.logger.info(f"⬇️  Скачиваю: {filename}")
            
            response = requests.get(
                export_url, 
                headers=self.headers, 
                timeout=(5, self.download_timeout),  # (connect_timeout, read_timeout)
                stream=True
            )
            
            if response.status_code == 200:
                # Проверяем content-type
                content_type = response.headers.get('content-type', '')
                if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type or 'application/zip' in content_type:
                    
                    # Сохраняем файл
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    file_size = output_path.stat().st_size
                    self.logger.info(f"✅ Скачан: {filename} ({file_size} байт)")
                    self.stats['successful_downloads'] += 1
                    return True
                else:
                    self.logger.warning(f"⚠️  Неожиданный content-type: {content_type}")
                    return False
            
            elif response.status_code == 403:
                self.logger.error(f"❌ Доступ запрещен (403): {filename}")
                return False
            
            elif response.status_code == 404:
                self.logger.error(f"❌ Таблица не найдена (404): {filename}")  
                return False
            
            else:
                self.logger.error(f"❌ HTTP {response.status_code}: {filename}")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"❌ Таймаут при скачивании: {filename}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка скачивания {filename}: {e}")
            return False
    
    def download_with_retries(self, sheet_id: str, filename: str) -> bool:
        """Скачивание с повторными попытками"""
        
        for attempt in range(1, self.max_retries + 1):
            try:
                if self.download_sheet_direct(sheet_id, filename):
                    return True
                
                if attempt < self.max_retries:
                    self.logger.info(f"🔄 Повтор {attempt + 1}/{self.max_retries} для {filename}")
                    time.sleep(self.retry_delay * attempt)
                    
            except Exception as e:
                self.logger.error(f"❌ Попытка {attempt} не удалась для {filename}: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)
        
        self.stats['failed_downloads'] += 1
        self.stats['errors'].append({
            'filename': filename,
            'sheet_id': sheet_id,
            'error': 'Все попытки скачивания не удались'
        })
        return False
    
    def download_batch(self, sheets_data: List[Dict], batch_size: int = 20, start_from: int = 0) -> Dict:
        """Батчевое скачивание таблиц"""
        
        total_sheets = len(sheets_data)
        end_at = min(start_from + batch_size, total_sheets)
        
        self.logger.info(f"🚀 Запуск батча: таблицы {start_from + 1}-{end_at} из {total_sheets}")
        
        batch_data = sheets_data[start_from:end_at]
        
        for i, sheet_info in enumerate(batch_data, start_from + 1):
            self.logger.info(f"\\n📋 {i}/{total_sheets}: {sheet_info['filename']}")
            
            self.stats['total_attempts'] += 1
            
            # Скачиваем таблицу
            success = self.download_with_retries(
                sheet_info['sheet_id'], 
                sheet_info['filename']
            )
            
            if not success:
                self.logger.error(f"❌ Неудача: {sheet_info['filename']}")
            
            # Небольшая пауза между скачиваниями
            if i < end_at:
                time.sleep(0.5)
        
        return self.get_batch_stats()
    
    def get_batch_stats(self) -> Dict:
        """Возвращает статистику текущего батча"""
        return {
            'total_attempts': self.stats['total_attempts'],
            'successful_downloads': self.stats['successful_downloads'],
            'failed_downloads': self.stats['failed_downloads'],
            'skipped_existing': self.stats['skipped_existing'],
            'success_rate': (self.stats['successful_downloads'] / self.stats['total_attempts'] * 100) if self.stats['total_attempts'] > 0 else 0,
            'errors_count': len(self.stats['errors'])
        }
    
    def save_errors_report(self, filename: str = "download_errors.json"):
        """Сохраняет отчет об ошибках"""
        
        if not self.stats['errors']:
            return
        
        errors_file = self.output_dir / filename
        
        try:
            with open(errors_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats['errors'], f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📄 Отчет об ошибках сохранен: {errors_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения отчета: {e}")
    
    def print_summary(self):
        """Выводит итоговую статистику"""
        
        stats = self.get_batch_stats()
        
        print(f"\\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"✅ Успешно скачано: {stats['successful_downloads']}")
        print(f"⏭️  Пропущено (уже есть): {stats['skipped_existing']}")
        print(f"❌ Неудачи: {stats['failed_downloads']}")
        print(f"📈 Успешность: {stats['success_rate']:.1f}%")
        print(f"📁 Папка с файлами: {self.output_dir.absolute()}")
        
        if self.stats['errors']:
            print(f"⚠️  Ошибок: {len(self.stats['errors'])}")
            self.save_errors_report()

def main():
    """Тестовый запуск загрузчика"""
    
    # Импортируем CSV парсер
    from csv_parser import CSVMasterTableParser
    
    # Парсим CSV
    csv_path = Path(__file__).parent.parent.parent / "Копилка Презентаций - Просчеты .csv"
    
    if not csv_path.exists():
        print(f"❌ CSV файл не найден: {csv_path}")
        return
    
    try:
        # Парсим CSV
        csv_parser = CSVMasterTableParser(str(csv_path))
        sheets_data = csv_parser.parse_csv_file()
        
        print(f"📊 Найдено {len(sheets_data)} Google Sheets таблиц")
        
        # Создаем загрузчик
        downloader = GoogleSheetsDownloader()
        
        # Скачиваем первые 5 таблиц для теста
        print(f"\\n🧪 ТЕСТОВОЕ СКАЧИВАНИЕ (первые 5 таблиц):")
        stats = downloader.download_batch(sheets_data, batch_size=5, start_from=0)
        
        downloader.print_summary()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise

if __name__ == "__main__":
    main()

