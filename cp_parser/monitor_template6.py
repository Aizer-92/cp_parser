#!/usr/bin/env python3
"""
Мониторинг прогресса парсинга Шаблона 6
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text


def get_stats(db):
    """Получает статистику из БД"""
    with db.get_session() as session:
        # Читаем список проектов для парсинга
        with open('template6_project_ids.txt', 'r') as f:
            target_ids = set(int(line.strip()) for line in f if line.strip().isdigit())
        
        # Проверяем сколько спарсено
        result = session.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE parsing_status = 'complete') as completed,
                COUNT(*) FILTER (WHERE parsing_status = 'error') as errors,
                COUNT(*) FILTER (WHERE parsing_status = 'pending') as pending,
                SUM(total_products_found) as products,
                SUM(total_images_found) as images
            FROM projects
            WHERE id = ANY(:ids)
        """), {'ids': list(target_ids)}).fetchone()
        
        return {
            'total': len(target_ids),
            'completed': result[0] or 0,
            'errors': result[1] or 0,
            'pending': result[2] or 0,
            'products': result[3] or 0,
            'images': result[4] or 0
        }


def main():
    db = PostgreSQLManager()
    
    print("=" * 80)
    print("МОНИТОРИНГ ПАРСИНГА ШАБЛОНА 6")
    print("=" * 80)
    
    while True:
        stats = get_stats(db)
        
        processed = stats['completed'] + stats['errors']
        progress = processed * 100 // stats['total'] if stats['total'] > 0 else 0
        
        print(f"\n[{time.strftime('%H:%M:%S')}] Прогресс: {processed}/{stats['total']} ({progress}%)")
        print(f"  ✅ Успешно: {stats['completed']}")
        print(f"  ❌ Ошибок: {stats['errors']}")
        print(f"  ⏳ Осталось: {stats['pending']}")
        print(f"  📦 Товары: {stats['products']:,}")
        print(f"  🖼️  Изображения: {stats['images']:,}")
        
        # Проверяем завершение
        if stats['pending'] == 0:
            print(f"\n{'='*80}")
            print("✅ ПАРСИНГ ЗАВЕРШЕН!")
            print("=" * 80)
            break
        
        time.sleep(10)  # Обновление каждые 10 секунд


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nМониторинг остановлен")




"""
Мониторинг прогресса парсинга Шаблона 6
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text


def get_stats(db):
    """Получает статистику из БД"""
    with db.get_session() as session:
        # Читаем список проектов для парсинга
        with open('template6_project_ids.txt', 'r') as f:
            target_ids = set(int(line.strip()) for line in f if line.strip().isdigit())
        
        # Проверяем сколько спарсено
        result = session.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE parsing_status = 'complete') as completed,
                COUNT(*) FILTER (WHERE parsing_status = 'error') as errors,
                COUNT(*) FILTER (WHERE parsing_status = 'pending') as pending,
                SUM(total_products_found) as products,
                SUM(total_images_found) as images
            FROM projects
            WHERE id = ANY(:ids)
        """), {'ids': list(target_ids)}).fetchone()
        
        return {
            'total': len(target_ids),
            'completed': result[0] or 0,
            'errors': result[1] or 0,
            'pending': result[2] or 0,
            'products': result[3] or 0,
            'images': result[4] or 0
        }


def main():
    db = PostgreSQLManager()
    
    print("=" * 80)
    print("МОНИТОРИНГ ПАРСИНГА ШАБЛОНА 6")
    print("=" * 80)
    
    while True:
        stats = get_stats(db)
        
        processed = stats['completed'] + stats['errors']
        progress = processed * 100 // stats['total'] if stats['total'] > 0 else 0
        
        print(f"\n[{time.strftime('%H:%M:%S')}] Прогресс: {processed}/{stats['total']} ({progress}%)")
        print(f"  ✅ Успешно: {stats['completed']}")
        print(f"  ❌ Ошибок: {stats['errors']}")
        print(f"  ⏳ Осталось: {stats['pending']}")
        print(f"  📦 Товары: {stats['products']:,}")
        print(f"  🖼️  Изображения: {stats['images']:,}")
        
        # Проверяем завершение
        if stats['pending'] == 0:
            print(f"\n{'='*80}")
            print("✅ ПАРСИНГ ЗАВЕРШЕН!")
            print("=" * 80)
            break
        
        time.sleep(10)  # Обновление каждые 10 секунд


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nМониторинг остановлен")











