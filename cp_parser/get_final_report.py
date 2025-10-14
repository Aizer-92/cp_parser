#!/usr/bin/env python3
"""
Итоговый отчет после массовой обработки всех батчей
"""

import re
from pathlib import Path

log_file = Path('batch_processing.log')

if not log_file.exists():
    print("❌ Файл лога не найден!")
    exit(1)

with open(log_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Извлекаем все итоги батчей
batches = re.findall(
    r'БАТЧ #(\d+).*?'
    r'Обработано проектов: (\d+).*?'
    r'Удалено дубликатов: ([\d,]+).*?'
    r'Перепривязано изображений: ([\d,]+).*?'
    r'Назначено главных: ([\d,]+).*?'
    r'Ошибок: (\d+)',
    content,
    re.DOTALL
)

if not batches:
    print("⚠️  Ни один батч еще не завершен")
    exit(0)

print("\n" + "="*80)
print("📊 ИТОГОВЫЙ ОТЧЕТ ПО ВСЕМ БАТЧАМ")
print("="*80 + "\n")

total_projects = 0
total_duplicates = 0
total_relinked = 0
total_main = 0
total_errors = 0

print("Батч | Проектов | Дубликатов | Перепривязок | Главных | Ошибок")
print("-"*80)

for batch_num, projects, dupes, relinked, main, errors in batches:
    # Убираем запятые из чисел
    dupes = int(dupes.replace(',', ''))
    relinked = int(relinked.replace(',', ''))
    main = int(main.replace(',', ''))
    
    print(f"  #{batch_num:2} | {int(projects):8} | {dupes:10,} | {relinked:12,} | {int(main):7,} | {int(errors):6}")
    
    total_projects += int(projects)
    total_duplicates += dupes
    total_relinked += relinked
    total_main += int(main)
    total_errors += int(errors)

print("-"*80)
print(f"ИТОГО | {total_projects:8} | {total_duplicates:10,} | {total_relinked:12,} | {total_main:7,} | {total_errors:6}")

print("\n" + "="*80)
print("📈 СТАТИСТИКА:")
print("="*80)
print(f"  ✅ Обработано батчей:           {len(batches)}/14")
print(f"  📦 Обработано проектов:         {total_projects}")
print(f"  🗑️  Удалено дубликатов:          {total_duplicates:,}")
print(f"  🔄 Перепривязано изображений:   {total_relinked:,}")
print(f"  🎯 Назначено главных:           {total_main:,}")
print(f"  ❌ Ошибок:                      {total_errors}")
print(f"  📊 Прогресс:                    {total_projects/268*100:.1f}%")
print("="*80 + "\n")

if len(batches) < 14:
    remaining = 14 - len(batches)
    print(f"⏳ Осталось батчей: {remaining}")
    print(f"⏱️  Примерное время: ~{remaining * 2} минут\n")
else:
    print("🎉 ВСЕ БАТЧИ ЗАВЕРШЕНЫ!\n")

