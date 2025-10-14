#!/usr/bin/env python3
"""
Детальный анализ валидных проектов Template 7
Показывает как определяются столбцы
"""
import pandas as pd
from pathlib import Path
import json

print("=" * 80)
print("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ВАЛИДНЫХ ПРОЕКТОВ TEMPLATE 7")
print("=" * 80)

# Загружаем список валидных проектов
with open('TEMPLATE7_VALIDATION_RESULTS.json', 'r', encoding='utf-8') as f:
    validation = json.load(f)

valid_projects = validation['valid_projects'][:10]  # Первые 10

excel_dir = Path("storage/excel_files")

print(f"\n📋 Анализирую первые 10 валидных проектов...\n")

# Ключевые слова для поиска столбцов
column_patterns = {
    'photo': ['фото', 'photo', 'изображение', 'картинка'],
    'name': ['наименование', 'name', 'название', 'товар', 'product'],
    'description': ['характеристики', 'description', 'описание', 'spec'],
    'custom': ['кастом', 'custom', 'персонализация'],
    'quantity': ['тираж', 'quantity', 'qty', 'количество', 'circulation'],
    'price_usd': ['$', 'usd', 'dollar'],
    'price_rub': ['₽', 'руб', 'rub', 'рубл'],
    'delivery': ['доставка', 'delivery', 'срок', 'время'],
    'sample': ['образец', 'sample', 'образцы'],
    'extra_photo': ['доп', 'additional', 'extra']
}

route_keywords = {
    'sea': ['sea', 'море', 'морской', 'долгое жд', 'контейнер', 'container'],
    'air': ['air', 'авиа', 'авио', 'долгое авиа', 'самолет'],
    'railway': ['жд', 'railway', 'ж.д', 'железная дорога', 'поезд'],
    'contract': ['контракт', 'contract']
}

def analyze_project(project_id):
    """Детально анализирует структуру проекта"""
    
    matching_files = list(excel_dir.glob(f'project_{project_id}_*.xlsx'))
    if not matching_files:
        return None
    
    file_path = matching_files[0]
    
    try:
        # Читаем файл
        df = pd.read_excel(file_path, nrows=30, header=None)
        
        result = {
            'project_id': project_id,
            'file': file_path.name,
            'shape': df.shape,
            'header_row': None,
            'columns': {},
            'routes': {},
            'data_preview': []
        }
        
        # Ищем строку с заголовками
        for i in range(min(10, len(df))):
            row_values = [str(df.iloc[i, j]).lower() for j in range(min(25, len(df.columns)))]
            row_text = " ".join(row_values)
            
            # Проверяем наличие ключевых слов
            name_found = any(kw in row_text for kw in column_patterns['name'])
            qty_found = any(kw in row_text for kw in column_patterns['quantity'])
            
            if name_found and qty_found:
                result['header_row'] = i
                
                # Определяем индексы столбцов
                for j in range(min(25, len(df.columns))):
                    cell_value = str(df.iloc[i, j]).lower().strip()
                    
                    if cell_value == 'nan' or not cell_value:
                        continue
                    
                    # Проверяем каждый тип столбца
                    for col_type, keywords in column_patterns.items():
                        if any(kw in cell_value for kw in keywords):
                            if col_type not in result['columns']:
                                result['columns'][col_type] = []
                            result['columns'][col_type].append({
                                'index': j,
                                'label': df.iloc[i, j],
                                'original': cell_value[:50]
                            })
                    
                    # Проверяем маршруты
                    for route_type, keywords in route_keywords.items():
                        if any(kw in cell_value for kw in keywords):
                            if route_type not in result['routes']:
                                result['routes'][route_type] = []
                            result['routes'][route_type].append({
                                'index': j,
                                'label': df.iloc[i, j],
                                'original': cell_value[:50]
                            })
                
                # Показываем следующие 5 строк данных
                for k in range(i+1, min(i+6, len(df))):
                    row_preview = []
                    for j in range(min(10, len(df.columns))):
                        val = str(df.iloc[k, j])
                        if val == 'nan':
                            val = '---'
                        else:
                            val = val[:30]
                        row_preview.append(val)
                    result['data_preview'].append(row_preview)
                
                break
        
        return result
        
    except Exception as e:
        return {
            'project_id': project_id,
            'error': str(e)[:100]
        }

# Анализируем проекты
for idx, project_id in enumerate(valid_projects, 1):
    print(f"\n{'=' * 80}")
    print(f"📄 ПРОЕКТ #{project_id} ({idx}/10)")
    print(f"{'=' * 80}")
    
    result = analyze_project(project_id)
    
    if not result:
        print(f"   ⚠️  Файл не найден")
        continue
    
    if 'error' in result:
        print(f"   ❌ Ошибка: {result['error']}")
        continue
    
    print(f"\n📊 Размер: {result['shape'][0]} строк × {result['shape'][1]} колонок")
    print(f"📍 Строка заголовков: {result['header_row'] + 1 if result['header_row'] is not None else 'не найдена'}")
    
    # Показываем найденные столбцы
    if result['columns']:
        print(f"\n✅ НАЙДЕННЫЕ СТОЛБЦЫ:")
        for col_type, cols in sorted(result['columns'].items()):
            print(f"\n   🔹 {col_type.upper()}:")
            for col in cols:
                print(f"      • Колонка [{col['index']}]: \"{col['label']}\"")
    
    # Показываем маршруты
    if result['routes']:
        print(f"\n🚚 НАЙДЕННЫЕ МАРШРУТЫ:")
        for route_type, routes in sorted(result['routes'].items()):
            print(f"\n   🔹 {route_type.upper()}:")
            for route in routes:
                print(f"      • Колонка [{route['index']}]: \"{route['label']}\"")
    
    # Показываем превью данных
    if result['data_preview']:
        print(f"\n📋 ПРЕВЬЮ ДАННЫХ (первые 5 строк после заголовков):")
        for i, row in enumerate(result['data_preview'], 1):
            print(f"\n   Строка {i}:")
            for j, val in enumerate(row[:8]):  # Первые 8 колонок
                print(f"      [{j}]: {val}")

print(f"\n{'=' * 80}")
print(f"💡 ВЫВОДЫ:")
print(f"{'=' * 80}")

print(f"""
Валидация показала, что Template 7 имеет:

1. Четкую структуру с заголовками (обычно строка 1-2)
2. Обязательные колонки: Название, Тираж
3. Опциональные маршруты: ЖД, АВИА, Sea, Air
4. Дополнительные поля: Характеристики, Образец, Кастом

Следующий шаг: Создать парсер, который:
- Автоматически определяет строку заголовков
- Находит индексы всех колонок
- Извлекает данные для каждого товара
- Поддерживает многострочные товары (несколько тиражей)
""")

print(f"{'=' * 80}")

