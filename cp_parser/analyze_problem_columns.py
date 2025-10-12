#!/usr/bin/env python3
"""
Анализ колонок в проблемных проектах
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_template_6 import Template6Parser

# ТОП проблемных проектов
problem_projects = [860, 846, 798, 794, 1769, 883, 1151, 2727, 1801, 292]

print("=" * 80)
print("🔍 АНАЛИЗ КОЛОНОК В ПРОБЛЕМНЫХ ПРОЕКТАХ")
print("=" * 80)

parser = Template6Parser()

for proj_id in problem_projects:
    try:
        result = parser.parse_project(proj_id)
        
        # Получаем обнаруженные колонки из лога (парсер выводит их)
        print(f"\n📋 Проект {proj_id}:")
        print(f"  Результат: {result.get('products', 0)} товаров, {result.get('images', 0)} изображений, {result.get('offers', 0)} офферов")
        
        # Парсер выводит колонки в стандартный вывод, они видны выше
        
    except Exception as e:
        print(f"\n❌ Проект {proj_id}: Ошибка - {str(e)[:100]}")

print("\n" + "=" * 80)
print("\n💡 ВЫВОДЫ:")
print("  - Проекты без офферов: парсер не нашел колонку 'тираж_col' или цены")
print("  - Проекты без изображений: нет изображений в Excel или не в ожидаемой колонке")
print("\n" + "=" * 80)



"""
Анализ колонок в проблемных проектах
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_template_6 import Template6Parser

# ТОП проблемных проектов
problem_projects = [860, 846, 798, 794, 1769, 883, 1151, 2727, 1801, 292]

print("=" * 80)
print("🔍 АНАЛИЗ КОЛОНОК В ПРОБЛЕМНЫХ ПРОЕКТАХ")
print("=" * 80)

parser = Template6Parser()

for proj_id in problem_projects:
    try:
        result = parser.parse_project(proj_id)
        
        # Получаем обнаруженные колонки из лога (парсер выводит их)
        print(f"\n📋 Проект {proj_id}:")
        print(f"  Результат: {result.get('products', 0)} товаров, {result.get('images', 0)} изображений, {result.get('offers', 0)} офферов")
        
        # Парсер выводит колонки в стандартный вывод, они видны выше
        
    except Exception as e:
        print(f"\n❌ Проект {proj_id}: Ошибка - {str(e)[:100]}")

print("\n" + "=" * 80)
print("\n💡 ВЫВОДЫ:")
print("  - Проекты без офферов: парсер не нашел колонку 'тираж_col' или цены")
print("  - Проекты без изображений: нет изображений в Excel или не в ожидаемой колонке")
print("\n" + "=" * 80)






