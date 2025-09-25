#!/usr/bin/env python3
"""
Скрипт для проверки описаний у товаров без описаний
"""
import sqlite3
import json
from pathlib import Path
from otapi_parser import OTAPIParser

def check_descriptions_for_missing_items():
    """Проверяет описания у товаров без описаний"""
    print("🔍 ПРОВЕРКА ОПИСАНИЙ У ТОВАРОВ БЕЗ ОПИСАНИЙ")
    print("=" * 60)
    
    # Подключаемся к БД
    db_path = Path("data/results/all_chunks_database.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем несколько товаров без описаний
    cursor.execute('''
        SELECT item_id, title, chunk_source, chunk_type
        FROM products
        WHERE description IS NULL OR description = '' OR description = 'Описание товара'
        LIMIT 20
    ''')
    
    items = cursor.fetchall()
    conn.close()
    
    if not items:
        print("❌ Не найдено товаров без описаний!")
        return
    
    print(f"📋 Найдено {len(items)} товаров для проверки")
    print()
    
    # Создаем парсер
    parser = OTAPIParser()
    
    # Проверяем каждый товар
    results = []
    for i, (item_id, title, chunk_source, chunk_type) in enumerate(items, 1):
        print(f"🔍 [{i}/{len(items)}] Проверка товара {item_id}...")
        print(f"    Название: {title[:80]}...")
        print(f"    Источник: {chunk_source}/{chunk_type}")
        
        try:
            # Парсим товар через OTAPI
            result = parser.parse_product(item_id)
            
            if result:
                raw_data = result.get('raw_data', {})
                item_data = raw_data.get('Item', {})
                
                description = item_data.get('Description', '')
                has_description = bool(description and description.strip())
                
                print(f"    ✅ Успешно получен ответ")
                print(f"    📝 Описание: {'ЕСТЬ' if has_description else 'НЕТ'}")
                if has_description:
                    print(f"    📏 Длина: {len(description)} символов")
                    print(f"    📋 Начало: {description[:100]}...")
                else:
                    print(f"    ❌ Описание отсутствует в API")
                
                results.append({
                    'item_id': item_id,
                    'title': title,
                    'chunk_source': chunk_source,
                    'chunk_type': chunk_type,
                    'has_description': has_description,
                    'description_length': len(description) if description else 0,
                    'description_preview': description[:100] if description else ''
                })
                
            else:
                print(f"    ❌ Не удалось получить данные")
                results.append({
                    'item_id': item_id,
                    'title': title,
                    'chunk_source': chunk_source,
                    'chunk_type': chunk_type,
                    'has_description': False,
                    'description_length': 0,
                    'description_preview': ''
                })
            
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")
            results.append({
                'item_id': item_id,
                'title': title,
                'chunk_source': chunk_source,
                'chunk_type': chunk_type,
                'has_description': False,
                'description_length': 0,
                'description_preview': '',
                'error': str(e)
            })
        
        print("-" * 60)
    
    # Анализируем результаты
    analyze_results(results)

def analyze_results(results):
    """Анализирует результаты проверки"""
    print("📊 АНАЛИЗ РЕЗУЛЬТАТОВ ПРОВЕРКИ")
    print("=" * 60)
    
    if not results:
        return
    
    total_items = len(results)
    items_with_descriptions = sum(1 for r in results if r['has_description'])
    items_without_descriptions = total_items - items_with_descriptions
    
    print(f"📋 ВСЕГО ПРОВЕРЕНО: {total_items}")
    print(f"✅ С описаниями: {items_with_descriptions} ({items_with_descriptions/total_items*100:.1f}%)")
    print(f"❌ Без описаний: {items_without_descriptions} ({items_without_descriptions/total_items*100:.1f}%)")
    
    if items_with_descriptions > 0:
        avg_length = sum(r['description_length'] for r in results if r['has_description']) / items_with_descriptions
        print(f"📏 Средняя длина описаний: {avg_length:.1f} символов")
    
    print()
    
    # Анализ по источникам
    print("📁 АНАЛИЗ ПО ИСТОЧНИКАМ:")
    source_stats = {}
    for result in results:
        source = f"{result['chunk_source']}/{result['chunk_type']}"
        if source not in source_stats:
            source_stats[source] = {'total': 0, 'with_desc': 0, 'without_desc': 0}
        
        source_stats[source]['total'] += 1
        if result['has_description']:
            source_stats[source]['with_desc'] += 1
        else:
            source_stats[source]['without_desc'] += 1
    
    for source, stats in source_stats.items():
        percentage = stats['with_desc'] / stats['total'] * 100
        print(f"   {source}: {stats['with_desc']}/{stats['total']} ({percentage:.1f}%)")
    
    print()
    
    # Примеры товаров с описаниями
    items_with_desc = [r for r in results if r['has_description']]
    if items_with_desc:
        print("📝 ПРИМЕРЫ ТОВАРОВ С ОПИСАНИЯМИ:")
        for i, item in enumerate(items_with_desc[:5], 1):
            print(f"   {i}. {item['item_id']} - {item['title'][:50]}...")
            print(f"       Длина: {item['description_length']} символов")
            print(f"       Начало: {item['description_preview']}...")
            print()
    
    # Примеры товаров без описаний
    items_without_desc = [r for r in results if not r['has_description']]
    if items_without_desc:
        print("❌ ПРИМЕРЫ ТОВАРОВ БЕЗ ОПИСАНИЙ:")
        for i, item in enumerate(items_without_desc[:5], 1):
            print(f"   {i}. {item['item_id']} - {item['title'][:50]}...")
            if 'error' in item:
                print(f"       Ошибка: {item['error']}")
            print()
    
    # Рекомендации
    print("💡 РЕКОМЕНДАЦИИ:")
    if items_with_descriptions > 0:
        print(f"   🎯 {items_with_descriptions} товаров имеют описания в API - можно допарсить")
        print(f"   🎯 Это улучшит покрытие описаниями с {items_with_descriptions/total_items*100:.1f}% до 100%")
    
    if items_without_descriptions > 0:
        print(f"   ⚠️  {items_without_descriptions} товаров действительно не имеют описаний в API")
        print(f"   💡 Это нормально - не все товары на 1688.com имеют подробные описания")
    
    # Сохраняем результаты
    save_results(results)

def save_results(results):
    """Сохраняет результаты проверки"""
    try:
        output_file = Path("data/results/description_check_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результаты сохранены в: {output_file.name}")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения результатов: {e}")

if __name__ == "__main__":
    check_descriptions_for_missing_items()
