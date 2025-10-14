#!/usr/bin/env python3
"""
Детальный анализ определения цен и маршрутов
"""
import pandas as pd
from pathlib import Path
import json

print("=" * 80)
print("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ЦЕН И МАРШРУТОВ")
print("=" * 80)

# Загружаем список валидных проектов
with open('TEMPLATE7_VALIDATION_RESULTS.json', 'r', encoding='utf-8') as f:
    validation = json.load(f)

# Берем проекты с маршрутами и без
valid_projects = validation['valid_projects'][:15]

excel_dir = Path("storage/excel_files")

route_keywords = {
    'sea': ['sea', 'море', 'морской', 'долгое жд', 'контейнер', 'container'],
    'air': ['air', 'авиа', 'авио', 'долгое авиа', 'самолет'],
    'railway': ['жд', 'railway', 'ж.д', 'железная дорога', 'поезд'],
    'contract': ['контракт', 'contract']
}

def analyze_project_routes(project_id):
    """Детально анализирует маршруты и цены"""
    
    matching_files = list(excel_dir.glob(f'project_{project_id}_*.xlsx'))
    if not matching_files:
        return None
    
    file_path = matching_files[0]
    
    try:
        df = pd.read_excel(file_path, nrows=30, header=None)
        
        result = {
            'project_id': project_id,
            'header_row': None,
            'routes_structure': {},
            'has_routes': False
        }
        
        # Ищем строку с заголовками
        for i in range(min(10, len(df))):
            row_text = " ".join([str(df.iloc[i, j]).lower() for j in range(min(25, len(df.columns))) if str(df.iloc[i, j]) != 'nan'])
            
            name_found = any(kw in row_text for kw in ['наименование', 'name', 'товар'])
            qty_found = any(kw in row_text for kw in ['тираж', 'quantity', 'qty'])
            
            if name_found and qty_found:
                result['header_row'] = i
                
                # Анализируем каждую колонку после заголовков
                for j in range(min(25, len(df.columns))):
                    header = str(df.iloc[i, j]).lower().strip()
                    
                    if header == 'nan' or not header:
                        continue
                    
                    # Ищем маршруты в заголовке
                    for route_type, keywords in route_keywords.items():
                        if any(kw in header for kw in keywords):
                            result['has_routes'] = True
                            
                            # Смотрим следующую строку (подзаголовки)
                            subheader_row = i + 1
                            if subheader_row < len(df):
                                # Проверяем следующие 3 колонки (обычно: USD, RUB, Срок)
                                price_cols = []
                                for k in range(j, min(j+5, len(df.columns))):
                                    subheader = str(df.iloc[subheader_row, k]).lower()
                                    if subheader != 'nan':
                                        price_cols.append({
                                            'col_idx': k,
                                            'label': df.iloc[subheader_row, k],
                                            'is_usd': '$' in subheader or 'usd' in subheader,
                                            'is_rub': '₽' in subheader or 'руб' in subheader or 'rub' in subheader,
                                            'is_time': 'срок' in subheader or 'период' in subheader or 'period' in subheader or 'к.д' in subheader
                                        })
                                
                                if route_type not in result['routes_structure']:
                                    result['routes_structure'][route_type] = []
                                
                                result['routes_structure'][route_type].append({
                                    'header_col': j,
                                    'header_label': df.iloc[i, j],
                                    'price_columns': price_cols
                                })
                
                break
        
        return result
        
    except Exception as e:
        return {'project_id': project_id, 'error': str(e)[:100]}

# Анализируем проекты
projects_with_routes = []
projects_without_routes = []

for project_id in valid_projects:
    result = analyze_project_routes(project_id)
    
    if result and 'error' not in result:
        if result['has_routes']:
            projects_with_routes.append(result)
        else:
            projects_without_routes.append(result)

print(f"\n📊 РЕЗУЛЬТАТЫ:")
print(f"   С маршрутами: {len(projects_with_routes)}")
print(f"   БЕЗ маршрутов: {len(projects_without_routes)}")

# Детальный анализ проектов С маршрутами
print(f"\n" + "=" * 80)
print(f"✅ ПРОЕКТЫ С МАРШРУТАМИ (детальный анализ):")
print(f"=" * 80)

for result in projects_with_routes:
    print(f"\n{'─' * 80}")
    print(f"📄 ПРОЕКТ #{result['project_id']}")
    print(f"{'─' * 80}")
    
    print(f"\n📍 Строка заголовков: {result['header_row'] + 1}")
    
    if result['routes_structure']:
        print(f"\n🚚 НАЙДЕННЫЕ МАРШРУТЫ И ИХ СТРУКТУРА:\n")
        
        for route_type, route_data_list in result['routes_structure'].items():
            for route_data in route_data_list:
                print(f"   🔹 {route_type.upper()}:")
                print(f"      Заголовок: [{route_data['header_col']}] \"{route_data['header_label']}\"")
                
                if route_data['price_columns']:
                    print(f"      Структура цен:")
                    for pc in route_data['price_columns']:
                        types = []
                        if pc['is_usd']:
                            types.append('USD')
                        if pc['is_rub']:
                            types.append('RUB')
                        if pc['is_time']:
                            types.append('СРОК')
                        
                        type_str = ', '.join(types) if types else 'неизвестно'
                        print(f"         [{pc['col_idx']}] \"{pc['label']}\" → {type_str}")
                else:
                    print(f"      ⚠️  Структура цен не определена!")
                
                print()

# Анализ проектов БЕЗ маршрутов
if projects_without_routes:
    print(f"\n" + "=" * 80)
    print(f"⚠️  ПРОЕКТЫ БЕЗ МАРШРУТОВ (нужна проверка):")
    print(f"=" * 80)
    
    for result in projects_without_routes:
        print(f"\n📄 ПРОЕКТ #{result['project_id']}")
        print(f"   Строка заголовков: {result['header_row'] + 1 if result['header_row'] is not None else 'не найдена'}")
        
        # Показываем строку заголовков
        matching_files = list(excel_dir.glob(f"project_{result['project_id']}_*.xlsx"))
        if matching_files:
            try:
                df = pd.read_excel(matching_files[0], nrows=15, header=None)
                if result['header_row'] is not None:
                    print(f"   Заголовки:")
                    for j in range(min(15, len(df.columns))):
                        val = df.iloc[result['header_row'], j]
                        if pd.notna(val):
                            print(f"      [{j}] {val}")
            except:
                pass

print(f"\n" + "=" * 80)
print(f"💡 ВЫВОДЫ:")
print(f"=" * 80)

print(f"""
1. ОПРЕДЕЛЕНИЕ ЦЕН И СРОКОВ:
   {'✅' if projects_with_routes else '❌'} Для проектов с маршрутами структура определяется
   • Находится колонка маршрута (например, "Доставка ЖД")
   • Ищутся следующие колонки с ценами (USD, RUB)
   • Определяется колонка со сроком
   
2. ПРОЕКТЫ БЕЗ МАРШРУТОВ:
   Их {len(projects_without_routes)} из {len(valid_projects)} проверенных
   
   Варианты:
   a) Это проекты с ОДНИМ маршрутом (не указан явно)
   b) Цены указаны без разделения на маршруты
   c) Это другой подтип шаблона
   
   РЕКОМЕНДАЦИЯ: Нужно решить - парсить их как Template 7 
   или создать отдельный шаблон для проектов без маршрутов

3. КАЧЕСТВО ОПРЕДЕЛЕНИЯ:
   Из {len(projects_with_routes)} проектов с маршрутами:
""")

routes_with_prices = 0
routes_without_prices = 0

for result in projects_with_routes:
    for route_type, route_data_list in result['routes_structure'].items():
        for route_data in route_data_list:
            if route_data['price_columns']:
                routes_with_prices += 1
            else:
                routes_without_prices += 1

print(f"   ✅ Маршрутов с определенными ценами: {routes_with_prices}")
print(f"   ⚠️  Маршрутов БЕЗ определенных цен: {routes_without_prices}")

print(f"\n" + "=" * 80)

