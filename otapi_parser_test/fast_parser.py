#!/usr/bin/env python3
"""
Быстрый многопоточный парсер с оптимизированными настройками
"""
import json
import time
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import signal
import sys
import requests

from enhanced_parser import EnhancedOTAPIParser
from config import OTAPIConfig

# Настройка логирования только в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fast_parser.log', encoding='utf-8')
    ]
)

class FastParser:
    """Быстрый многопоточный парсер с оптимизированными настройками"""
    
    def __init__(self, max_workers: int = 12):
        self.config = OTAPIConfig()
        self.max_workers = max_workers
        
        # Создаем отдельный парсер для каждого потока
        self.parsers = {}
        
        # Пути к файлам
        self.main_project_path = Path("../promo_calculator")
        self.existing_data_path = self.main_project_path / "database" / "full-clear-database-09_07_2025.xlsx"
        self.offer_ids_path = self.main_project_path / "parsing_project" / "data" / "unique_offer_ids.json"
        
        # Директории для результатов
        self.data_dir = Path("data")
        self.results_dir = self.data_dir / "results"
        self.chunk_dir = self.results_dir / "chunks"
        
        # Создаем директории
        self.data_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        self.chunk_dir.mkdir(exist_ok=True)
        
        # Файлы прогресса и статистики
        self.progress_file = self.results_dir / "fast_parsing_progress.json"
        self.stats_file = self.results_dir / "fast_parsing_stats.json"
        
        # Загружаем данные
        self.existing_data = {}
        self.offer_ids = []
        self.load_existing_data()
        self.load_offer_ids()
        
        # Инициализируем прогресс
        self.progress_data = self.load_progress()
        self.processed_ids = set(self.progress_data.get('processed_ids', []))
        
        # Статистика
        self.stats = self.progress_data.get('stats', {
            'successful': 0,
            'failed': 0,
            'errors': []
        })
        
        # Текущий чанк
        self.current_chunk = []
        self.chunk_size = 100  # Увеличиваем размер чанка
        self.chunk_counter = len(list(self.chunk_dir.glob("fast_chunk_*.json"))) + 1
        
        # Потокобезопасные объекты
        self.lock = threading.Lock()
        self.running = True
        
        # Настройка обработчика сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"🚀 Быстрый парсер инициализирован:")
        print(f"   - Потоков: {max_workers}")
        print(f"   - Уже обработано: {len(self.processed_ids)} товаров")
        print("=" * 60)
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        print("\n🛑 Получен сигнал прерывания, завершаем работу...")
        self.running = False
        self.save_progress()
        sys.exit(0)
    
    def get_parser_for_thread(self, thread_id: int) -> EnhancedOTAPIParser:
        """Получает парсер для конкретного потока"""
        if thread_id not in self.parsers:
            self.parsers[thread_id] = EnhancedOTAPIParser()
        return self.parsers[thread_id]
    
    def load_existing_data(self):
        """Загружает существующие данные из основной базы"""
        try:
            if self.existing_data_path.exists():
                df = pd.read_excel(self.existing_data_path)
                for _, row in df.iterrows():
                    item_id = str(row.get('item_id', ''))
                    if item_id:
                        self.existing_data[item_id] = {
                            'title': row.get('title', ''),
                            'price': row.get('price', ''),
                            'vendor': row.get('vendor', ''),
                            'brand': row.get('brand', ''),
                            'url': row.get('url', '')
                        }
                logging.info(f"Загружено {len(self.existing_data)} товаров из основной базы")
            else:
                logging.warning(f"Файл основной базы не найден: {self.existing_data_path}")
        except Exception as e:
            logging.error(f"Ошибка загрузки основной базы: {e}")
    
    def load_offer_ids(self):
        """Загружает ID товаров для парсинга"""
        try:
            if self.offer_ids_path.exists():
                with open(self.offer_ids_path, 'r', encoding='utf-8') as f:
                    self.offer_ids = json.load(f)
                logging.info(f"Загружено {len(self.offer_ids)} ID для парсинга")
            else:
                logging.error(f"Файл с ID не найден: {self.offer_ids_path}")
        except Exception as e:
            logging.error(f"Ошибка загрузки ID: {e}")
    
    def load_progress(self):
        """Загружает прогресс парсинга"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logging.info(f"Загружен прогресс: {len(data.get('processed_ids', []))} уже обработанных товаров")
                return data
            except Exception as e:
                logging.error(f"Ошибка загрузки прогресса: {e}")
        
        return {
            'processed_ids': [],
            'stats': {
                'successful': 0,
                'failed': 0,
                'errors': []
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def save_progress(self):
        """Сохраняет прогресс парсинга"""
        try:
            with self.lock:
                progress_data = {
                    'processed_ids': list(self.processed_ids),
                    'stats': self.stats,
                    'last_updated': datetime.now().isoformat()
                }
                
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress_data, f, ensure_ascii=False, indent=2)
                
                logging.info(f"Прогресс сохранен: {len(self.processed_ids)} обработанных товаров")
        except Exception as e:
            logging.error(f"Ошибка сохранения прогресса: {e}")
    
    def save_chunk(self):
        """Сохраняет текущий чанк"""
        try:
            if not self.current_chunk:
                return
            
            chunk_filename = f"fast_chunk_{self.chunk_counter:03d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            chunk_path = self.chunk_dir / chunk_filename
            
            with open(chunk_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_chunk, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Сохранен чанк {self.chunk_counter}: {len(self.current_chunk)} товаров")
            
            self.current_chunk = []
            self.chunk_counter += 1
            
        except Exception as e:
            logging.error(f"Ошибка сохранения чанка: {e}")
    
    def parse_single_product(self, item_id: str, thread_id: int) -> Optional[Dict[str, Any]]:
        """Парсит один товар с оптимизированными настройками"""
        parser = self.get_parser_for_thread(thread_id)
        
        try:
            # Быстрый парсинг без лишних проверок
            result = parser.parse_product(item_id)
            
            if result:
                with self.lock:
                    self.stats['successful'] += 1
                title = result.get('title', '')[:30] if result.get('title') else 'Unknown'
                print(f"✓ {item_id}: {title}...")
                return result
            else:
                with self.lock:
                    self.stats['failed'] += 1
                    self.stats['errors'].append({
                        'item_id': item_id,
                        'error': 'No data received',
                        'timestamp': datetime.now().isoformat()
                    })
                print(f"✗ {item_id}: No data received")
                return None
                
        except Exception as e:
            with self.lock:
                self.stats['failed'] += 1
                self.stats['errors'].append({
                    'item_id': item_id,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            print(f"❌ {item_id}: {str(e)[:50]}")
            return None
    
    def parse_products_batch(self, limit: int = 1000, start_from: int = 0) -> bool:
        """Парсит батч товаров с оптимизированными настройками"""
        try:
            print(f"🎯 Запускаем быстрый парсинг {limit} товаров с {self.max_workers} потоками...")
            
            # Получаем список ID для парсинга
            remaining_ids = [id for id in self.offer_ids if id not in self.processed_ids]
            ids_to_parse = remaining_ids[start_from:start_from + limit]
            
            if not ids_to_parse:
                print("ℹ️ Нет товаров для парсинга")
                return True
            
            print(f"📋 Будем парсить {len(ids_to_parse)} товаров")
            print("=" * 60)
            
            # Запускаем многопоточный парсинг
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Создаем задачи
                future_to_id = {
                    executor.submit(self.parse_single_product, item_id, i % self.max_workers): item_id
                    for i, item_id in enumerate(ids_to_parse)
                }
                
                completed = 0
                start_time = time.time()
                
                for future in as_completed(future_to_id):
                    if not self.running:
                        print("\n🛑 Получен сигнал остановки, завершаем парсинг...")
                        break
                    
                    item_id = future_to_id[future]
                    
                    try:
                        result = future.result()
                        
                        if result:
                            self.current_chunk.append(result)
                            
                            # Сохраняем чанк если он заполнен
                            if len(self.current_chunk) >= self.chunk_size:
                                self.save_chunk()
                        
                        # Добавляем ID в обработанные
                        with self.lock:
                            self.processed_ids.add(item_id)
                        
                        completed += 1
                        
                        # Показываем прогресс каждые 50 товаров
                        if completed % 50 == 0:
                            elapsed = time.time() - start_time
                            rate = completed / elapsed if elapsed > 0 else 0
                            remaining = len(ids_to_parse) - completed
                            eta = remaining / rate if rate > 0 else 0
                            
                            print(f"\n📈 ПРОГРЕСС: {completed}/{len(ids_to_parse)} ({(completed/len(ids_to_parse)*100):.1f}%)")
                            print(f"   Скорость: {rate:.1f} товаров/сек")
                            print(f"   Осталось времени: {eta/60:.1f} минут")
                            print(f"   Успешно: {self.stats['successful']}, Ошибок: {self.stats['failed']}")
                            
                            # Сохраняем прогресс
                            self.save_progress()
                        
                    except Exception as e:
                        print(f"❌ Ошибка обработки {item_id}: {e}")
                        with self.lock:
                            self.stats['failed'] += 1
                            self.stats['errors'].append({
                                'item_id': item_id,
                                'error': str(e),
                                'timestamp': datetime.now().isoformat()
                            })
            
            # Сохраняем последний чанк
            if self.current_chunk:
                self.save_chunk()
            
            # Финальная статистика
            total_time = time.time() - start_time
            total_rate = completed / total_time if total_time > 0 else 0
            
            print(f"\n🎉 Парсинг завершен!")
            print(f"   Обработано: {completed}/{len(ids_to_parse)} товаров")
            print(f"   Время: {total_time/60:.1f} минут")
            print(f"   Скорость: {total_rate:.1f} товаров/сек")
            print(f"   Успешно: {self.stats['successful']} товаров")
            print(f"   Ошибок: {self.stats['failed']} товаров")
            
            # Сохраняем финальный прогресс
            self.save_progress()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            logging.error(f"Ошибка парсинга: {e}")
            return False
    
    def merge_chunks_to_sqlite(self):
        """Объединяет все чанки в SQLite базу данных"""
        try:
            print("🔄 Объединяем чанки в SQLite базу данных...")
            
            # Создаем базу данных
            db_path = self.results_dir / "fast_products_database.db"
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Создаем таблицу
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    item_id TEXT PRIMARY KEY,
                    title TEXT,
                    price TEXT,
                    vendor TEXT,
                    brand TEXT,
                    url TEXT,
                    description TEXT,
                    specifications TEXT,
                    images TEXT
                )
            ''')
            
            # Находим все чанки
            chunk_files = list(self.chunk_dir.glob("fast_chunk_*.json"))
            total_products = 0
            
            for chunk_file in chunk_files:
                print(f"Обрабатываем {chunk_file.name}...")
                
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                for product in chunk_data:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO products 
                            (item_id, title, price, vendor, brand, url, description, specifications, images)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            product.get('item_id'),
                            product.get('title'),
                            product.get('price'),
                            json.dumps(product.get('vendor', {})) if isinstance(product.get('vendor'), dict) else str(product.get('vendor', '')),
                            json.dumps(product.get('brand', {})) if isinstance(product.get('brand'), dict) else str(product.get('brand', '')),
                            product.get('url'),
                            json.dumps(product.get('description', '')),
                            json.dumps(product.get('specifications', {})),
                            json.dumps(product.get('images', []))
                        ))
                        total_products += 1
                    except Exception as e:
                        print(f"Ошибка вставки товара {product.get('item_id')}: {e}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ База данных создана: {db_path}")
            print(f"   Товаров в базе: {total_products}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания базы данных: {e}")
            return False
