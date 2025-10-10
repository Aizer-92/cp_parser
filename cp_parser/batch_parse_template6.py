#!/usr/bin/env python3
"""
Батч-парсинг всех проектов Шаблона 6
"""
import sys
from pathlib import Path
from datetime import datetime
from parse_template_6 import Template6Parser

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text


def main():
    db = PostgreSQLManager()
    
    # Читаем список проектов
    with open('template6_project_ids.txt', 'r') as f:
        all_project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    # Фильтруем уже обработанные
    with db.get_session() as session:
        from sqlalchemy import text
        processed = session.execute(text("""
            SELECT id FROM projects 
            WHERE id = ANY(:ids) AND parsing_status IN ('complete', 'error')
        """), {'ids': all_project_ids}).fetchall()
        processed_ids = set(r[0] for r in processed)
    
    project_ids = [pid for pid in all_project_ids if pid not in processed_ids]
    
    print("=" * 80)
    print("БАТЧ-ПАРСИНГ ШАБЛОНА 6")
    print("=" * 80)
    print(f"\nВсего проектов: {len(all_project_ids)}")
    print(f"Уже обработано: {len(processed_ids)}")
    print(f"Осталось парсить: {len(project_ids)}")
    print(f"Начало: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    parser = Template6Parser()
    
    stats = {
        'success': 0,
        'errors': 0,
        'total_products': 0,
        'total_images': 0,
        'total_offers': 0
    }
    
    errors_list = []
    
    for i, project_id in enumerate(project_ids, 1):
        print(f"\n[{i}/{len(project_ids)}] Проект {project_id}...", end=' ')
        
        try:
            result = parser.parse_project(project_id)
            
            if result['success']:
                stats['success'] += 1
                stats['total_products'] += result['products']
                stats['total_images'] += result['images']
                stats['total_offers'] += result['offers']
                
                print(f"OK (T:{result['products']}, I:{result['images']}, O:{result['offers']})")
            else:
                stats['errors'] += 1
                errors_list.append((project_id, result['error']))
                print(f"ERROR: {result['error']}")
        
        except Exception as e:
            stats['errors'] += 1
            errors_list.append((project_id, str(e)))
            print(f"EXCEPTION: {e}")
        
        # Прогресс каждые 50 проектов
        if i % 50 == 0:
            print(f"\n--- ПРОГРЕСС: {i}/{len(project_ids)} ({i*100//len(project_ids)}%) ---")
            print(f"    Успешно: {stats['success']}, Ошибок: {stats['errors']}")
            print(f"    Товары: {stats['total_products']}, Изображения: {stats['total_images']}")
    
    # Итоговый отчет
    print("\n" + "=" * 80)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)
    print(f"\nОбработано проектов: {len(project_ids)}")
    print(f"  Успешно: {stats['success']} ({stats['success']*100//len(project_ids)}%)")
    print(f"  Ошибок: {stats['errors']} ({stats['errors']*100//len(project_ids) if project_ids else 0}%)")
    print(f"\nСпарсено:")
    print(f"  Товары: {stats['total_products']:,}")
    print(f"  Изображения: {stats['total_images']:,}")
    print(f"  Предложения: {stats['total_offers']:,}")
    
    if errors_list:
        print(f"\nОШИБКИ ({len(errors_list)}):")
        for proj_id, error in errors_list[:10]:
            print(f"  Проект {proj_id}: {error[:60]}")
        if len(errors_list) > 10:
            print(f"  ... и еще {len(errors_list) - 10} ошибок")
        
        # Сохраняем ошибки
        with open('template6_errors.txt', 'w', encoding='utf-8') as f:
            for proj_id, error in errors_list:
                f.write(f"{proj_id} | {error}\n")
        print(f"\nПолный список ошибок: template6_errors.txt")
    
    print(f"\nЗавершено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == '__main__':
    main()

