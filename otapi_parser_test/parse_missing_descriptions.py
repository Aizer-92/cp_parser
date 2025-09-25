#!/usr/bin/env python3
"""
Скрипт для массового парсинга товаров без описаний
"""
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from otapi_parser import OTAPIParser

def parse_missing_descriptions():
    """Парсит товары без описаний"""
    print("🚀 МАССОВЫЙ ПАРСИНГ ТОВАРОВ БЕЗ ОПИСАНИЙ")
    print("=" * 60)
    
    # Подключаемся к БД
    db_path = Path("data/results/all_chunks_database.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем товары без описаний
    cursor.execute('''
        SELECT item_id, title, chunk_source, chunk_type
        FROM products
        WHERE description IS NULL OR description = '' OR description = 'Описание товара'
        ORDER BY item_id
        LIMIT 1000
    ''')
    
    items = cursor.fetchall()
    conn.close()
    
    if not items:
        print("❌ Не найдено товаров без описаний!")
        return
    
    print(f"📋 Найдено {len(items)} товаров без описаний")
    print(f"📊 Первые 5: {[item[0] for item in items[:5]]}")
    print()
    
    # Создаем парсер
    parser = OTAPIParser()
    
    # Парсим товары
    start_time = time.time()
    results = []
    errors = 0
    
    for i, (item_id, title, chunk_source, chunk_type) in enumerate(items, 1):
        try:
            print(f"🔍 [{i}/{len(items)}] Парсинг товара {item_id}...")
            
            # Парсим товар через OTAPI
            result = parser.parse_product(item_id)
            
            if result:
                raw_data = result.get('raw_data', {})
                item_data = raw_data.get('Item', {})
                
                description = item_data.get('Description', '')
                has_description = bool(description and description.strip())
                
                if has_description:
                    print(f"    ✅ Получено описание: {len(description)} символов")
                    results.append({
                        'item_id': item_id,
                        'title': title,
                        'description': description,
                        'chunk_source': chunk_source,
                        'chunk_type': chunk_type
                    })
                else:
                    print(f"    ❌ Описание отсутствует в API")
                    errors += 1
            else:
                print(f"    ❌ Не удалось получить данные")
                errors += 1
            
            # Небольшая задержка между запросами
            if i < len(items):
                time.sleep(0.5)
                
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")
            errors += 1
        
        # Показываем прогресс каждые 50 товаров
        if i % 50 == 0:
            print(f"\n📊 Прогресс: {i}/{len(items)} ({i/len(items)*100:.1f}%)")
            print(f"   ✅ Успешно: {len(results)}")
            print(f"   ❌ Ошибок: {errors}")
            print()
    
    end_time = time.time()
    
    # Статистика
    parsing_time = end_time - start_time
    success_rate = len(results) / len(items) * 100 if items else 0
    
    print(f"\n⏱️  ВРЕМЯ ПАРСИНГА:")
    print(f"   Общее время: {parsing_time:.1f} секунд")
    print(f"   Среднее время на товар: {parsing_time/len(items):.1f} секунд")
    print(f"   Скорость: {len(results)/parsing_time:.2f} товаров/сек")
    
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"   Всего товаров: {len(items)}")
    print(f"   Успешно спарсено: {len(results)}")
    print(f"   Ошибок: {errors}")
    print(f"   Процент успеха: {success_rate:.1f}%")
    
    if results:
        # Сохраняем результаты в chunk
        chunk_file = save_chunk(results, 3)
        
        if chunk_file:
            print(f"\n✅ ПАРСИНГ УСПЕШНО ЗАВЕРШЕН!")
            print(f"📁 Результаты сохранены в: {chunk_file.name}")
            print(f"📊 Всего спарсено: {len(results)} товаров")
            
            # Показываем что делать дальше
            show_next_steps()
        else:
            print(f"\n❌ Ошибка сохранения результатов!")
    else:
        print(f"\n❌ Парсинг завершился без результатов!")

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

def show_next_steps():
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

if __name__ == "__main__":
    parse_missing_descriptions()
