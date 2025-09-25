#!/usr/bin/env python3
"""
Скрипт для массового парсинга товаров через OTAPI API
"""
import json
import time
from pathlib import Path
from datetime import datetime
from otapi_parser import OTAPIParser

def get_items_to_parse():
    """Получает список товаров для парсинга"""
    try:
        # Проверяем есть ли файл с оставшимися товарами
        remaining_file = Path("data/results/remaining_items.json")
        if remaining_file.exists():
            with open(remaining_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                print(f"📋 Найдено {len(data)} товаров для парсинга")
                return data[:500]  # Берем первые 500
        
        # Если нет файла, берем товары без изображений из БД
        print("📋 Файл remaining_items.json не найден, берем товары без изображений из БД")
        return get_items_without_images_from_db()
        
    except Exception as e:
        print(f"❌ Ошибка получения списка товаров: {e}")
        return []

def get_items_without_images_from_db():
    """Получает товары без изображений из БД"""
    try:
        import sqlite3
        
        db_path = Path("data/results/all_chunks_database.db")
        if not db_path.exists():
            print("❌ База данных не найдена")
            return []
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем товары без изображений
        cursor.execute('''
            SELECT p.item_id 
            FROM products p 
            WHERE NOT EXISTS (SELECT 1 FROM images i WHERE i.item_id = p.item_id)
            LIMIT 500
        ''')
        
        items = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"📋 Найдено {len(items)} товаров без изображений в БД")
        return items
        
    except Exception as e:
        print(f"❌ Ошибка получения товаров из БД: {e}")
        return []

def save_chunk(results, chunk_number):
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
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Chunk сохранен: {filename}")
        return filepath
        
    except Exception as e:
        print(f"❌ Ошибка сохранения chunk: {e}")
        return None

def main():
    """Основная функция"""
    print("🚀 МАССОВЫЙ ПАРСИНГ ТОВАРОВ ЧЕРЕЗ OTAPI API")
    print("=" * 60)
    
    # Получаем список товаров для парсинга
    items_to_parse = get_items_to_parse()
    
    if not items_to_parse:
        print("❌ Нет товаров для парсинга!")
        return
    
    print(f"🎯 ЦЕЛЬ: Парсинг {len(items_to_parse)} товаров")
    print(f"📊 Первые 5 товаров: {items_to_parse[:5]}")
    print()
    
    # Создаем парсер
    parser = OTAPIParser()
    
    # Парсим товары
    start_time = time.time()
    results = parser.parse_batch(items_to_parse)
    end_time = time.time()
    
    # Статистика
    parsing_time = end_time - start_time
    avg_time_per_item = parsing_time / len(items_to_parse) if items_to_parse else 0
    
    print(f"\n⏱️  ВРЕМЯ ПАРСИНГА:")
    print(f"   Общее время: {parsing_time:.1f} секунд")
    print(f"   Среднее время на товар: {avg_time_per_item:.1f} секунд")
    print(f"   Скорость: {len(results)/parsing_time:.2f} товаров/сек")
    
    if results:
        # Сохраняем результаты в chunk
        chunk_file = save_chunk(results, 1)
        
        if chunk_file:
            print(f"\n✅ ПАРСИНГ УСПЕШНО ЗАВЕРШЕН!")
            print(f"📁 Результаты сохранены в: {chunk_file.name}")
            print(f"📊 Всего спарсено: {len(results)} товаров")
            
            # Анализируем качество данных
            analyze_results_quality(results)
        else:
            print(f"\n❌ Ошибка сохранения результатов!")
    else:
        print(f"\n❌ Парсинг завершился без результатов!")

def analyze_results_quality(results):
    """Анализирует качество результатов парсинга"""
    print(f"\n🔍 АНАЛИЗ КАЧЕСТВА РЕЗУЛЬТАТОВ:")
    print("-" * 40)
    
    if not results:
        return
    
    total_items = len(results)
    items_with_title = 0
    items_with_description = 0
    items_with_images = 0
    items_with_attributes = 0
    items_with_physical = 0
    items_with_weight = 0
    
    for item in results:
        raw_data = item.get('raw_data', {})
        item_data = raw_data.get('Item', {})
        
        if item_data.get('Title'):
            items_with_title += 1
        
        if item_data.get('Description'):
            items_with_description += 1
        
        if item_data.get('Pictures'):
            items_with_images += 1
        
        if item_data.get('Attributes'):
            items_with_attributes += 1
        
        if item_data.get('PhysicalParameters'):
            items_with_physical += 1
        
        if item_data.get('ActualWeightInfo'):
            items_with_weight += 1
    
    print(f"📊 Покрытие данных:")
    print(f"   Заголовки: {items_with_title}/{total_items} ({items_with_title/total_items*100:.1f}%)")
    print(f"   Описания: {items_with_description}/{total_items} ({items_with_description/total_items*100:.1f}%)")
    print(f"   Изображения: {items_with_images}/{total_items} ({items_with_images/total_items*100:.1f}%)")
    print(f"   Характеристики: {items_with_attributes}/{total_items} ({items_with_attributes/total_items*100:.1f}%)")
    print(f"   Физические параметры: {items_with_physical}/{total_items} ({items_with_physical/total_items*100:.1f}%)")
    print(f"   Информация о весе: {items_with_weight}/{total_items} ({items_with_weight/total_items*100:.1f}%)")

if __name__ == "__main__":
    main()
