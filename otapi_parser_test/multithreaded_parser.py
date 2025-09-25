#!/usr/bin/env python3
"""
Многопоточный парсер для быстрого допарсинга оставшихся товаров
"""
import sqlite3
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from otapi_parser import OTAPIParser
import queue

class MultithreadedParser:
    """Многопоточный парсер"""
    
    def __init__(self, max_workers=8):
        self.max_workers = max_workers
        self.results = []
        self.errors = 0
        self.lock = threading.Lock()
        self.progress_queue = queue.Queue()
        
    def parse_missing_data_multithreaded(self):
        """Парсит товары без описаний и характеристик в многопоточном режиме"""
        print(f"🚀 МНОГОПОТОЧНЫЙ ПАРСИНГ ТОВАРОВ (потоков: {self.max_workers})")
        print("=" * 60)
        
        # Подключаемся к БД
        db_path = Path("data/results/all_chunks_database.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем товары без описаний ИЛИ без характеристик
        cursor.execute('''
            SELECT DISTINCT p.item_id, p.title, p.chunk_source, p.chunk_type
            FROM products p
            WHERE (p.description IS NULL OR p.description = '' OR p.description = 'Описание товара')
               OR NOT EXISTS (SELECT 1 FROM specifications s WHERE s.item_id = p.item_id)
            ORDER BY p.item_id
            LIMIT 2000
        ''')
        
        items = cursor.fetchall()
        conn.close()
        
        if not items:
            print("❌ Не найдено товаров для допарсинга!")
            return
        
        print(f"📋 Найдено {len(items)} товаров для допарсинга")
        print(f"📊 Первые 5: {[item[0] for item in items[:5]]}")
        print()
        
        # Запускаем многопоточный парсинг
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Создаем задачи
            future_to_item = {
                executor.submit(self.parse_single_item, item): item 
                for item in items
            }
            
            # Обрабатываем результаты
            completed = 0
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                completed += 1
                
                try:
                    result = future.result()
                    if result:
                        with self.lock:
                            self.results.append(result)
                    else:
                        with self.lock:
                            self.errors += 1
                except Exception as e:
                    with self.lock:
                        self.errors += 1
                    print(f"❌ Ошибка парсинга {item[0]}: {e}")
                
                # Показываем прогресс
                if completed % 100 == 0:
                    success_rate = len(self.results) / completed * 100
                    print(f"📊 Прогресс: {completed}/{len(items)} ({completed/len(items)*100:.1f}%)")
                    print(f"   ✅ Успешно: {len(self.results)}")
                    print(f"   ❌ Ошибок: {self.errors}")
                    print(f"   📈 Процент успеха: {success_rate:.1f}%")
                    print()
        
        end_time = time.time()
        
        # Статистика
        parsing_time = end_time - start_time
        success_rate = len(self.results) / len(items) * 100 if items else 0
        
        print(f"\n⏱️  ВРЕМЯ ПАРСИНГА:")
        print(f"   Общее время: {parsing_time:.1f} секунд")
        print(f"   Среднее время на товар: {parsing_time/len(items):.1f} секунд")
        print(f"   Скорость: {len(self.results)/parsing_time:.2f} товаров/сек")
        print(f"   Ускорение: {len(items)/parsing_time:.2f}x (vs 0.26 товаров/сек в однопоточном)")
        
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        print(f"   Всего товаров: {len(items)}")
        print(f"   Успешно спарсено: {len(self.results)}")
        print(f"   Ошибок: {self.errors}")
        print(f"   Процент успеха: {success_rate:.1f}%")
        
        if self.results:
            # Анализируем качество данных
            self.analyze_data_quality()
            
            # Сохраняем результаты в chunk
            chunk_file = self.save_chunk(4)
            
            if chunk_file:
                print(f"\n✅ ПАРСИНГ УСПЕШНО ЗАВЕРШЕН!")
                print(f"📁 Результаты сохранены в: {chunk_file.name}")
                print(f"📊 Всего спарсено: {len(self.results)} товаров")
                
                # Показываем что делать дальше
                self.show_next_steps()
            else:
                print(f"\n❌ Ошибка сохранения результатов!")
        else:
            print(f"\n❌ Парсинг завершился без результатов!")
    
    def parse_single_item(self, item):
        """Парсит один товар"""
        item_id, title, chunk_source, chunk_type = item
        
        try:
            # Создаем парсер для каждого потока
            parser = OTAPIParser()
            
            # Парсим товар через OTAPI
            result = parser.parse_product(item_id)
            
            if result:
                raw_data = result.get('raw_data', {})
                item_data = raw_data.get('Item', {})
                
                # Проверяем что получили
                description = item_data.get('Description', '')
                attributes = item_data.get('Attributes', [])
                physical = item_data.get('PhysicalParameters', {})
                weight_info = item_data.get('ActualWeightInfo', {})
                pictures = item_data.get('Pictures', [])
                main_image = item_data.get('MainPictureUrl', '')
                
                has_description = bool(description and description.strip())
                has_attributes = bool(attributes and len(attributes) > 0)
                has_physical = bool(physical and len(physical) > 0)
                has_weight = bool(weight_info and len(weight_info) > 0)
                has_images = bool((pictures and len(pictures) > 0) or main_image)
                
                # Формируем результат
                parsed_item = {
                    'id': f'abb-{item_id}',
                    'item_id': item_id,
                    'url': f'https://detail.1688.com/offer/{item_id}.html',
                    'title': title,
                    'status': 'success',
                    'raw_data': {
                        'Item': item_data
                    }
                }
                
                # Показываем прогресс в очереди
                self.progress_queue.put({
                    'item_id': item_id,
                    'has_description': has_description,
                    'has_attributes': has_attributes,
                    'description_length': len(description),
                    'attributes_count': len(attributes)
                })
                
                return parsed_item
            else:
                return None
                
        except Exception as e:
            return None
    
    def analyze_data_quality(self):
        """Анализирует качество полученных данных"""
        print(f"\n🔍 АНАЛИЗ КАЧЕСТВА ДАННЫХ:")
        print("-" * 40)
        
        if not self.results:
            return
        
        total_items = len(self.results)
        items_with_description = 0
        items_with_attributes = 0
        items_with_physical = 0
        items_with_weight = 0
        items_with_images = 0
        
        total_attributes = 0
        total_physical_params = 0
        total_weight_params = 0
        total_images = 0
        total_description_length = 0
        
        for item in self.results:
            raw_data = item.get('raw_data', {})
            item_data = raw_data.get('Item', {})
            
            # Описания
            description = item_data.get('Description', '')
            if description and description.strip():
                items_with_description += 1
                total_description_length += len(description)
            
            # Характеристики
            attributes = item_data.get('Attributes', [])
            if attributes and len(attributes) > 0:
                items_with_attributes += 1
                total_attributes += len(attributes)
            
            # Физические параметры
            physical = item_data.get('PhysicalParameters', {})
            if physical and len(physical) > 0:
                items_with_physical += 1
                total_physical_params += len(physical)
            
            # Информация о весе
            weight_info = item_data.get('ActualWeightInfo', {})
            if weight_info and len(weight_info) > 0:
                items_with_weight += 1
                total_weight_params += len(weight_info)
            
            # Изображения
            pictures = item_data.get('Pictures', [])
            main_image = item_data.get('MainPictureUrl', '')
            if (pictures and len(pictures) > 0) or main_image:
                items_with_images += 1
                total_images += len(pictures) + (1 if main_image else 0)
        
        print(f"📝 Описания: {items_with_description}/{total_items} ({items_with_description/total_items*100:.1f}%)")
        if items_with_description > 0:
            avg_desc_length = total_description_length / items_with_description
            print(f"   Средняя длина: {avg_desc_length:.1f} символов")
        
        print(f"📋 Характеристики: {items_with_attributes}/{total_items} ({items_with_attributes/total_items*100:.1f}%)")
        if items_with_attributes > 0:
            avg_attrs = total_attributes / items_with_attributes
            print(f"   Среднее количество: {avg_attrs:.1f} шт")
        
        print(f"📏 Физические параметры: {items_with_physical}/{total_items} ({items_with_physical/total_items*100:.1f}%)")
        if items_with_physical > 0:
            avg_physical = total_physical_params / items_with_physical
            print(f"   Среднее количество: {avg_physical:.1f} шт")
        
        print(f"⚖️ Информация о весе: {items_with_weight}/{total_items} ({items_with_weight/total_items*100:.1f}%)")
        if items_with_weight > 0:
            avg_weight = total_weight_params / items_with_weight
            print(f"   Среднее количество: {avg_weight:.1f} шт")
        
        print(f"🖼️ Изображения: {items_with_images}/{total_items} ({items_with_images/total_items*100:.1f}%)")
        if items_with_images > 0:
            avg_images = total_images / items_with_images
            print(f"   Среднее количество: {avg_images:.1f} шт")
    
    def save_chunk(self, chunk_number):
        """Сохраняет chunk с результатами"""
        try:
            # Создаем директорию если нет
            chunks_dir = Path("data/results/chunks")
            chunks_dir.mkdir(parents=True, exist_ok=True)
            
            # Формируем имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"otapi_chunk_{chunk_number:03d}_{timestamp}.json"
            filepath = chunks_dir / filename
            
            # Сохраняем данные
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Chunk сохранен: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ Ошибка сохранения chunk: {e}")
            return None
    
    def show_next_steps(self):
        """Показывает что делать дальше"""
        print(f"\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
        print(f"   1. Объединить новый chunk в БД")
        print(f"   2. Проверить качество данных после объединения")
        print(f"   3. Если нужно - продолжить парсинг остальных товаров")
        print(f"   4. Финальная проверка полной БД")
        
        print(f"\n💡 КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ:")
        print(f"   # Объединить chunk в БД:")
        print(f"   python3 merge_otapi_chunk.py")
        print(f"   ")
        print(f"   # Проверить финальное состояние БД:")
        print(f"   python3 check_final_database.py")

def main():
    """Основная функция"""
    # Создаем парсер с 8 потоками
    parser = MultithreadedParser(max_workers=8)
    parser.parse_missing_data_multithreaded()

if __name__ == "__main__":
    main()
