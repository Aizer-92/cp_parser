#!/usr/bin/env python3
"""
Тестовый парсинг проблемного проекта с детальным выводом
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_template_6 import Template6Parser

# Проблемные проекты: 860, 846, 1769, 883
problem_project_id = 1769  # Было 29 изображений из 73 товаров

print("=" * 80)
print(f"🔍 ТЕСТОВЫЙ ПАРСИНГ ПРОЕКТА {problem_project_id}")
print("=" * 80)

parser = Template6Parser()

try:
    result = parser.parse_project(problem_project_id)
    
    print(f"\n✅ Парсинг завершен")
    print(f"\n📊 Результат:")
    print(f"  Товары: {result.get('products', 0)}")
    print(f"  Изображения: {result.get('images', 0)}")
    print(f"  Офферы: {result.get('offers', 0)}")
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

