#!/usr/bin/env python3
"""
Парсинг ВСЕХ 406 проектов Template 7
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd().parent / 'cp_parser_core'))

from parsers.parse_template_7_clean import Template7Parser
import json
from datetime import datetime
import time

# Загружаем список Template 7 проектов
with open('TEMPLATE7_FILTERED_RESULTS.json', 'r', encoding='utf-8') as f:
    template7_data = json.load(f)

all_project_ids = [int(pid) for pid in template7_data.get('template7_projects', [])]

# Исключаем уже обработанные
already_parsed = [1188]  # Проект 1188 уже обработан
project_ids = [pid for pid in all_project_ids if pid not in already_parsed]

print(f"\n{'='*80}")
print(f"🚀 ПОЛНЫЙ ПАРСИНГ TEMPLATE 7")
print(f"{'='*80}")
print(f"Всего проектов Template 7: {len(all_project_ids)}")
print(f"Уже обработано: {len(already_parsed)}")
print(f"К обработке: {len(project_ids)}")
print(f"Время старта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}\n")

parser = Template7Parser()
results = []
start_time = time.time()

successful_count = 0
failed_count = 0
total_products = 0
total_offers = 0
total_images = 0

for i, project_id in enumerate(project_ids, 1):
    # Прогресс каждые 10 проектов
    if i % 10 == 1 or i == len(project_ids):
        elapsed = time.time() - start_time
        avg_time = elapsed / i if i > 0 else 0
        remaining = (len(project_ids) - i) * avg_time
        
        print(f"\n{'▓'*80}")
        print(f"📊 [{i}/{len(project_ids)}] ({i*100//len(project_ids)}%) | "
              f"✅ {successful_count} | ❌ {failed_count} | "
              f"Осталось: ~{int(remaining/60)} мин")
        print(f"{'▓'*80}")
    
    try:
        result = parser.parse_project(project_id)
        results.append({
            'project_id': project_id,
            'result': result
        })
        
        if result['success']:
            successful_count += 1
            total_products += result['products']
            total_offers += result['total_offers']
            total_images += result['total_images']
            
            # Краткий лог
            if i % 10 == 0:
                print(f"   ✅ #{project_id}: {result['products']} товаров, "
                      f"{result['total_offers']} офферов, {result['total_images']} изображений")
        else:
            failed_count += 1
            print(f"   ❌ #{project_id}: {result['error']}")
        
        # Очищаем динамические данные для следующего проекта
        parser.columns = {}
        parser.routes = {}
        parser.header_row = None
        parser.data_start_row = None
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Прервано пользователем на проекте #{project_id}")
        break
    except Exception as e:
        failed_count += 1
        print(f"   ❌ #{project_id}: КРИТИЧЕСКАЯ ОШИБКА - {e}")
        results.append({
            'project_id': project_id,
            'result': {'success': False, 'error': f'КРИТИЧЕСКАЯ ОШИБКА: {str(e)}'}
        })

# Итоговый отчет
elapsed_total = time.time() - start_time

print(f"\n{'='*80}")
print(f"📊 ИТОГОВЫЙ ОТЧЕТ")
print(f"{'='*80}")
print(f"Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Общее время: {int(elapsed_total/60)} минут {int(elapsed_total%60)} секунд")
print(f"Средняя скорость: {elapsed_total/len(results):.1f} сек/проект")

print(f"\n✅ Успешно: {successful_count}/{len(project_ids)} ({successful_count*100//len(project_ids)}%)")
print(f"❌ Ошибки: {failed_count}/{len(project_ids)} ({failed_count*100//len(project_ids) if len(project_ids) > 0 else 0}%)")

if successful_count > 0:
    print(f"\n📦 Общая статистика:")
    print(f"   Товаров: {total_products:,}")
    print(f"   Офферов: {total_offers:,}")
    print(f"   Изображений: {total_images:,}")
    print(f"   Среднее офферов на товар: {total_offers/total_products:.1f}")
    print(f"   Среднее изображений на товар: {total_images/total_products:.1f}")

if failed_count > 0 and failed_count <= 20:
    print(f"\n❌ Проекты с ошибками:")
    for r in results:
        if not r['result']['success']:
            error = r['result']['error'][:80]
            print(f"   #{r['project_id']}: {error}")

# Сохраняем результаты
output_file = f"TEMPLATE7_FULL_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n💾 Результаты сохранены в {output_file}")
print(f"{'='*80}\n")

