#!/usr/bin/env python3
"""
Загрузка данных по пошлинам для всех категорий
"""
import os
import sys
import json
from database import get_database_connection

# Данные по пошлинам для всех категорий
CUSTOMS_DATA = {
    # Основные категории с пошлинами
    "повербанки": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
    "кружки": {"duty_rate": "12%", "vat_rate": "20%", "certificates": ["EAC"]},  # Исправлено с 11.5%
    "термосы": {"duty_rate": "10%", "vat_rate": "20%", "certificates": ["EAC"]},  # Исправлено с 15%
    "термобутылки": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
    "термокружки": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
    "термостаканы": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
    "кофферы": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
    "ежедневники": {"duty_rate": "0%", "vat_rate": "20%", "certificates": []},
    "блокноты": {"duty_rate": "0%", "vat_rate": "20%", "certificates": []},
    "картхолдер": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "ланьярд": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "ретрактор": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "пакеты": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
    "флешки": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
    "ручки": {"duty_rate": "7.5%", "vat_rate": "20%", "certificates": []},  # Исправлено с 6.5%
    # Текстиль - КОМБИНИРОВАННЫЕ ПОШЛИНЫ (10% или EUR/кг, что больше)
    "футболки": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.75 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "футболка": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.75 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "толстовка": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.88 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "худи": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.88 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "плед": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.88 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "подушка": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.88 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "кепка": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.88 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "шарф": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.88 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "перчатки": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.88 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "дождевик": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.88 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "носки": {"duty_rate": "10%", "duty_type": "combined", "ad_valorem_rate": "10%", "specific_rate": "1.88 EUR/kg", "vat_rate": "20%", "certificates": ["EAC"]},
    "сумки": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "зонты": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
    "часы": {"duty_rate": "6%", "vat_rate": "20%", "certificates": ["EAC"]},
    
    # Дополнительные категории
    "бутылка": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
    "коффер": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
    "термос": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
    "ручка": {"duty_rate": "7.5%", "vat_rate": "20%", "certificates": []},  # Исправлено с 6.5%
    "лампа": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
    "игрушка": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
    "кабель": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
    "брелок": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
    "чехол": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "рюкзак": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "аккумулятор": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
    "косметичка": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "колонка": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
    "флешка": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
    # Удалены дубликаты текстильных товаров - они уже обновлены выше с комбинированными пошлинами
    "увлажнитель": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
    "зонт": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
    # Удалены дубликаты: подушка, кепка, шарф, перчатки, дождевик, толстовка, худи, носки
    # Они уже обновлены выше с комбинированными пошлинами
    "коробка": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
    "органайзер": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "пенал": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "бейдж": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "наушники": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
    "блокнот": {"duty_rate": "0%", "vat_rate": "20%", "certificates": []},
    "массажер": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
    "посуда": {"duty_rate": "12%", "vat_rate": "20%", "certificates": ["EAC"]},  # Исправлено с 11.5%
    "проектор": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
    # Удалены дубликаты текстильных товаров (кепка, шарф, перчатки, дождевик, толстовка, худи, носки)
    # Они уже обновлены выше с комбинированными пошлинами
    "фонарь": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
    "гирлянда": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
    "свеча": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
    "магнит": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
    # Удалены дубликаты: толстовка, худи, носки - уже обновлены выше
    "конструктор": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
    "таблетница": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
    "стикеры": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
    "мышь": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
    # Удален дубликат: носки - уже обновлен выше
    
    # Общая категория по умолчанию
    "общая": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]}
}

def load_customs_data():
    """Загружает данные по пошлинам для всех категорий"""
    try:
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        print(f"🚛 Загружаем данные по пошлинам в {db_type}...")
        
        # Сначала получаем все существующие категории
        cursor.execute("SELECT category, data FROM categories")
        existing_categories = cursor.fetchall()
        
        print(f"📦 Найдено категорий в БД: {len(existing_categories)}")
        
        updated_count = 0
        
        for row in existing_categories:
            try:
                if db_type == 'postgres':
                    category_name = row['category'] if isinstance(row, dict) else row[0]
                    category_data = row['data'] if isinstance(row, dict) else row[1]
                else:
                    category_name = row['category'] if hasattr(row, 'keys') else row[0]
                    category_data = row['data'] if hasattr(row, 'keys') else row[1]
                
                # Парсим JSON данные категории
                if isinstance(category_data, str):
                    category_json = json.loads(category_data)
                else:
                    category_json = category_data
                
                # Ищем соответствующие данные по пошлинам
                customs_info = None
                category_lower = category_name.lower()
                
                # Точное совпадение
                if category_lower in CUSTOMS_DATA:
                    customs_info = CUSTOMS_DATA[category_lower]
                else:
                    # Поиск по частичному совпадению
                    for customs_key, customs_value in CUSTOMS_DATA.items():
                        if customs_key in category_lower or category_lower in customs_key:
                            customs_info = customs_value
                            break
                
                if customs_info:
                    # Сохраняем существующий ТН ВЭД код если он есть
                    existing_tnved = category_json.get('tnved_code', '')
                    
                    # Добавляем/обновляем данные по пошлинам
                    if existing_tnved:
                        # Если ТН ВЭД уже есть, только добавляем пошлины
                        category_json['duty_rate'] = customs_info['duty_rate']
                        category_json['vat_rate'] = customs_info['vat_rate']
                        category_json['certificates'] = customs_info['certificates']
                        print(f"✅ Обновлены пошлины для: {category_name} (ТН ВЭД: {existing_tnved})")
                    else:
                        # Если ТН ВЭД нет, используем общий код
                        category_json['tnved_code'] = "9999999999"  # Общий код для уточнения
                        category_json['duty_rate'] = customs_info['duty_rate']
                        category_json['vat_rate'] = customs_info['vat_rate']
                        category_json['certificates'] = customs_info['certificates']
                        print(f"✅ Добавлены данные для: {category_name} (общий ТН ВЭД)")
                    
                    # Обновляем в БД
                    updated_data = json.dumps(category_json, ensure_ascii=False)
                    
                    if db_type == 'postgres':
                        cursor.execute(
                            "UPDATE categories SET data = %s WHERE category = %s",
                            (updated_data, category_name)
                        )
                    else:
                        cursor.execute(
                            "UPDATE categories SET data = ? WHERE category = ?",
                            (updated_data, category_name)
                        )
                    
                    updated_count += 1
                else:
                    print(f"⚠️ Нет данных по пошлинам для: {category_name}")
                    
            except Exception as e:
                print(f"❌ Ошибка обработки категории {category_name}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        
        print(f"\n🎉 Загрузка завершена! Обновлено категорий: {updated_count}")
        
        # Проверяем результат
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category, data FROM categories")
        all_categories = cursor.fetchall()
        
        print(f"\n📋 Статус категорий:")
        for row in all_categories:
            try:
                if db_type == 'postgres':
                    category_name = row['category'] if isinstance(row, dict) else row[0]
                    category_data = row['data'] if isinstance(row, dict) else row[1]
                else:
                    category_name = row['category'] if hasattr(row, 'keys') else row[0]
                    category_data = row['data'] if hasattr(row, 'keys') else row[1]
                
                if isinstance(category_data, str):
                    category_json = json.loads(category_data)
                else:
                    category_json = category_data
                
                has_customs = 'tnved_code' in category_json and category_json['tnved_code']
                status = "✅" if has_customs else "❌"
                tnved = category_json.get('tnved_code', 'НЕТ')
                print(f"  {status} {category_name} -> {tnved}")
                
            except Exception as e:
                print(f"  ❌ {category_name} -> ОШИБКА: {e}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Критическая ошибка загрузки: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    load_customs_data()
