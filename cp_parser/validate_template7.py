#!/usr/bin/env python3
"""
Валидатор для Template 7 (Multiple Routes)

Проверяет, сколько проектов реально соответствуют Template 7:
- Есть 2+ маршрута доставки
- Есть основные колонки (название, тираж, цена)
- Структура позволяет извлечь данные
"""
import pandas as pd
from pathlib import Path
from collections import defaultdict
import json

print("=" * 80)
print("🔍 ВАЛИДАЦИЯ TEMPLATE 7 (MULTIPLE ROUTES)")
print("=" * 80)

excel_dir = Path("storage/excel_files")
excel_files = sorted([f for f in excel_dir.glob("*.xlsx") if f.name.startswith("project_")])

# Критерии валидации
validation_results = {
    'valid': [],           # Полностью валидные
    'warning': [],         # С предупреждениями, но парсятся
    'invalid': [],         # Не проходят валидацию
    'errors': []           # Ошибки чтения
}

# Детальная статистика
stats = {
    'total_checked': 0,
    'has_routes': 0,
    'has_header_row': 0,
    'has_product_name': 0,
    'has_quantity': 0,
    'has_prices': 0,
    'multirow_products': 0
}

# Ключевые слова для поиска
route_keywords = ['жд', 'railway', 'ж.д', 'авиа', 'air', 'sea', 'море', 'контракт', 'contract', 'контейнер', 'container']
name_keywords = ['наименование', 'name', 'название', 'товар', 'product']
quantity_keywords = ['тираж', 'quantity', 'qty', 'количество']
price_keywords = ['цена', 'price', 'стоимость', 'cost', '$', '₽', 'руб']

print(f"\n📁 Проверяю {len(excel_files)} файлов...")
print(f"   (Это займет 2-3 минуты)\n")

def validate_project(file_path):
    """Валидирует один проект"""
    try:
        project_id = file_path.stem.split("_")[1]
        
        # Читаем файл
        df = pd.read_excel(file_path, nrows=50, header=None)
        
        if df.empty:
            return {'status': 'invalid', 'reason': 'Empty file'}
        
        # Собираем весь текст
        all_text = ""
        for i in range(min(15, len(df))):
            for j in range(min(20, len(df.columns))):
                val = str(df.iloc[i, j]).strip().lower()
                if val and val != 'nan':
                    all_text += val + " "
        
        validation = {
            'project_id': project_id,
            'file': file_path.name,
            'checks': {},
            'warnings': [],
            'score': 0,
            'max_score': 6
        }
        
        # Проверка 1: Есть ли 2+ маршрута
        found_routes = []
        for keyword in route_keywords:
            if keyword in all_text:
                found_routes.append(keyword)
        found_routes = list(set(found_routes))
        
        validation['checks']['routes'] = {
            'passed': len(found_routes) >= 2,
            'count': len(found_routes),
            'found': found_routes[:4]  # Первые 4
        }
        if validation['checks']['routes']['passed']:
            validation['score'] += 1
        
        # Проверка 2: Есть ли строка с заголовками
        header_row = None
        for i in range(min(10, len(df))):
            row_text = " ".join([str(df.iloc[i, j]).lower() for j in range(min(20, len(df.columns))) if str(df.iloc[i, j]) != 'nan'])
            
            # Ищем строку с ключевыми словами
            name_found = any(kw in row_text for kw in name_keywords)
            qty_found = any(kw in row_text for kw in quantity_keywords)
            
            if name_found and qty_found:
                header_row = i
                break
        
        validation['checks']['header_row'] = {
            'passed': header_row is not None,
            'row': header_row
        }
        if validation['checks']['header_row']['passed']:
            validation['score'] += 1
        
        # Проверка 3: Есть ли колонка с названием товара
        has_name_col = any(kw in all_text for kw in name_keywords)
        validation['checks']['product_name'] = {'passed': has_name_col}
        if has_name_col:
            validation['score'] += 1
        
        # Проверка 4: Есть ли колонка с тиражом
        has_qty_col = any(kw in all_text for kw in quantity_keywords)
        validation['checks']['quantity'] = {'passed': has_qty_col}
        if has_qty_col:
            validation['score'] += 1
        
        # Проверка 5: Есть ли цены
        price_count = sum(1 for kw in price_keywords if kw in all_text)
        validation['checks']['prices'] = {
            'passed': price_count >= 2,
            'count': price_count
        }
        if validation['checks']['prices']['passed']:
            validation['score'] += 1
        
        # Проверка 6: Есть ли данные после заголовков
        has_data = False
        if header_row is not None and header_row + 1 < len(df):
            # Проверяем есть ли данные в следующих 5 строках
            for i in range(header_row + 1, min(header_row + 6, len(df))):
                row_text = " ".join([str(df.iloc[i, j]) for j in range(min(5, len(df.columns))) if str(df.iloc[i, j]) != 'nan'])
                if len(row_text) > 10:  # Есть какие-то данные
                    has_data = True
                    break
        
        validation['checks']['has_data'] = {'passed': has_data}
        if has_data:
            validation['score'] += 1
        
        # Предупреждения
        if len(found_routes) == 1:
            validation['warnings'].append('Только 1 маршрут (нужно 2+)')
        
        if price_count < len(found_routes) * 2:
            validation['warnings'].append(f'Мало цен ({price_count}) для {len(found_routes)} маршрутов')
        
        if header_row and header_row > 5:
            validation['warnings'].append(f'Заголовки далеко (строка {header_row+1})')
        
        return validation
        
    except Exception as e:
        return {
            'status': 'error',
            'project_id': file_path.stem.split("_")[1],
            'file': file_path.name,
            'error': str(e)[:100]
        }

# Валидируем все файлы
for idx, file_path in enumerate(excel_files, 1):
    result = validate_project(file_path)
    
    stats['total_checked'] += 1
    
    if 'error' in result:
        validation_results['errors'].append(result)
    else:
        # Обновляем статистику
        if result['checks']['routes']['passed']:
            stats['has_routes'] += 1
        if result['checks']['header_row']['passed']:
            stats['has_header_row'] += 1
        if result['checks']['product_name']['passed']:
            stats['has_product_name'] += 1
        if result['checks']['quantity']['passed']:
            stats['has_quantity'] += 1
        if result['checks']['prices']['passed']:
            stats['has_prices'] += 1
        
        # Классифицируем
        if result['score'] >= 5:  # 5-6 из 6
            validation_results['valid'].append(result)
        elif result['score'] >= 3:  # 3-4 из 6
            validation_results['warning'].append(result)
        else:  # 0-2 из 6
            validation_results['invalid'].append(result)
    
    if idx % 100 == 0:
        print(f"   ✓ Обработано: {idx}/{len(excel_files)}")

# Выводим результаты
print(f"\n" + "=" * 80)
print(f"📊 РЕЗУЛЬТАТЫ ВАЛИДАЦИИ")
print(f"=" * 80)

total = stats['total_checked']
valid_count = len(validation_results['valid'])
warning_count = len(validation_results['warning'])
invalid_count = len(validation_results['invalid'])
error_count = len(validation_results['errors'])

print(f"\n✅ ВАЛИДНЫЕ (5-6/6):        {valid_count:4d} ({valid_count/total*100:5.1f}%)")
print(f"⚠️  С ПРЕДУПРЕЖДЕНИЯМИ (3-4/6): {warning_count:4d} ({warning_count/total*100:5.1f}%)")
print(f"❌ НЕВАЛИДНЫЕ (0-2/6):      {invalid_count:4d} ({invalid_count/total*100:5.1f}%)")
print(f"💥 ОШИБКИ ЧТЕНИЯ:           {error_count:4d} ({error_count/total*100:5.1f}%)")
print(f"{'─' * 80}")
print(f"📁 ВСЕГО ПРОВЕРЕНО:         {total:4d}")

print(f"\n" + "=" * 80)
print(f"📈 ДЕТАЛЬНАЯ СТАТИСТИКА")
print(f"=" * 80)

print(f"\n✅ Проходят проверки:")
print(f"   • 2+ маршрута:           {stats['has_routes']:4d} ({stats['has_routes']/total*100:5.1f}%)")
print(f"   • Строка заголовков:     {stats['has_header_row']:4d} ({stats['has_header_row']/total*100:5.1f}%)")
print(f"   • Колонка 'Название':    {stats['has_product_name']:4d} ({stats['has_product_name']/total*100:5.1f}%)")
print(f"   • Колонка 'Тираж':       {stats['has_quantity']:4d} ({stats['has_quantity']/total*100:5.1f}%)")
print(f"   • Цены (2+):             {stats['has_prices']:4d} ({stats['has_prices']/total*100:5.1f}%)")

# Примеры валидных проектов
if validation_results['valid']:
    print(f"\n" + "=" * 80)
    print(f"✅ ПРИМЕРЫ ВАЛИДНЫХ ПРОЕКТОВ (первые 15):")
    print(f"=" * 80)
    
    for result in validation_results['valid'][:15]:
        score = result['score']
        routes = result['checks']['routes']
        warnings = f" ⚠️ {len(result['warnings'])}" if result['warnings'] else ""
        
        print(f"\n   #{result['project_id']} [{score}/6]{warnings}")
        print(f"      Маршруты: {', '.join(routes['found'])} ({routes['count']} найдено)")
        if result['warnings']:
            for w in result['warnings']:
                print(f"      ⚠️  {w}")

# Примеры с предупреждениями
if validation_results['warning']:
    print(f"\n" + "=" * 80)
    print(f"⚠️  ПРИМЕРЫ С ПРЕДУПРЕЖДЕНИЯМИ (первые 10):")
    print(f"=" * 80)
    
    for result in validation_results['warning'][:10]:
        score = result['score']
        routes = result['checks']['routes']
        
        print(f"\n   #{result['project_id']} [{score}/6]")
        print(f"      Маршруты: {routes['count']}")
        
        # Показываем какие проверки не прошли
        failed = []
        for check_name, check_data in result['checks'].items():
            if isinstance(check_data, dict) and not check_data.get('passed'):
                failed.append(check_name)
        
        if failed:
            print(f"      ❌ Не прошли: {', '.join(failed)}")

# Сохраняем результаты
output = {
    'summary': {
        'total': total,
        'valid': valid_count,
        'warning': warning_count,
        'invalid': invalid_count,
        'errors': error_count
    },
    'stats': stats,
    'valid_projects': [r['project_id'] for r in validation_results['valid']],
    'warning_projects': [r['project_id'] for r in validation_results['warning']],
    'invalid_projects': [r['project_id'] for r in validation_results['invalid']]
}

with open('TEMPLATE7_VALIDATION_RESULTS.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n" + "=" * 80)
print(f"💾 РЕЗУЛЬТАТЫ СОХРАНЕНЫ:")
print(f"=" * 80)
print(f"\n   📄 TEMPLATE7_VALIDATION_RESULTS.json")
print(f"      • Списки валидных/невалидных проектов")
print(f"      • Детальная статистика")

print(f"\n" + "=" * 80)
print(f"💡 ВЫВОДЫ:")
print(f"=" * 80)

parseable = valid_count + warning_count
print(f"\n   ✅ МОЖНО ПАРСИТЬ: {parseable} проектов ({parseable/total*100:.1f}%)")
print(f"   ❌ НЕ ПАРСЯТСЯ:   {invalid_count + error_count} проектов ({(invalid_count + error_count)/total*100:.1f}%)")

if parseable > 0:
    print(f"\n   🎯 РЕКОМЕНДАЦИЯ: Начать с {valid_count} валидных проектов")
    print(f"      Затем доработать парсер для {warning_count} с предупреждениями")

print(f"\n" + "=" * 80)

