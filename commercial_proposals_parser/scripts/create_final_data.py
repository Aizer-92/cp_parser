#!/usr/bin/env python3
"""
Скрипт для создания финального JSON файла с правильными данными
"""

import json

def create_final_data():
    """Создание финального JSON файла с правильными данными"""
    
    # Загружаем данные из parsed_products.json
    with open('parsed_products.json', 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    
    # Загружаем данные из merch_sense_products.json
    with open('merch_sense_products.json', 'r', encoding='utf-8') as f:
        merch_data = json.load(f)
    
    # Создаем финальный список товаров
    final_data = []
    
    # Добавляем товары из основной таблицы (только те, что есть в parsed_products.json)
    for item in parsed_data:
        final_data.append(item)
    
    # Добавляем товары из таблицы "Мерч для Sense" (только те, что есть в merch_sense_products.json)
    for item in merch_data:
        final_data.append(item)
    
    # Сохраняем финальный файл
    with open('final_products.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Создан финальный файл с {len(final_data)} товарами")
    
    # Проверяем товары без вариантов цен
    products_without_prices = [item for item in final_data if not item.get('price_offers')]
    if products_without_prices:
        print(f"⚠️  Товары без вариантов цен: {len(products_without_prices)}")
        for item in products_without_prices:
            print(f"   - {item['name']}")
    else:
        print(f"✅ Все товары имеют варианты цен!")

if __name__ == "__main__":
    create_final_data()
