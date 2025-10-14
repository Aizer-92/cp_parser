#!/usr/bin/env python3
"""
Мониторинг прогресса массовой обработки батчей
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text


def get_stats():
    """Получить статистику по обработанным проектам"""
    db = PostgreSQLManager()
    
    with db.get_session() as session:
        # Всего проектов с NULL row_number
        total_null = session.execute(
            text("""
                SELECT COUNT(DISTINCT project_id)
                FROM products
                WHERE row_number IS NULL
            """)
        ).scalar()
        
        # Статистика по изображениям
        stats = session.execute(
            text("""
                SELECT 
                    COUNT(DISTINCT p.project_id) as projects_with_images,
                    COUNT(pi.id) as total_images,
                    COUNT(DISTINCT pi.image_url) as unique_images,
                    SUM(CASE WHEN pi.is_main_image::text = 'true' THEN 1 ELSE 0 END) as main_images
                FROM products p
                JOIN product_images pi ON p.id = pi.product_id
                WHERE p.row_number IS NULL
            """)
        ).fetchone()
        
        return {
            'total_projects': total_null,
            'projects_with_images': stats[0],
            'total_images': stats[1],
            'unique_images': stats[2],
            'main_images': stats[3],
            'duplicates': stats[1] - stats[2]
        }


def read_last_log_lines(n=10):
    """Прочитать последние N строк из лога"""
    log_file = Path('batch_processing.log')
    if not log_file.exists():
        return []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return lines[-n:] if len(lines) > n else lines


def main():
    """Главная функция"""
    print("\n" + "="*80)
    print("📊 МОНИТОРИНГ ОБРАБОТКИ БАТЧЕЙ")
    print("="*80 + "\n")
    
    try:
        while True:
            stats = get_stats()
            
            print(f"\r{'='*80}", end='')
            print(f"\r⏱️  {time.strftime('%H:%M:%S')}", end=' | ')
            print(f"Проектов с NULL: {stats['total_projects']:3}", end=' | ')
            print(f"Изображений: {stats['total_images']:,}", end=' | ')
            print(f"Дубликатов: {stats['duplicates']:,}", end=' | ')
            print(f"Главных: {stats['main_images']:,}", end='    ')
            
            # Показываем последние строки лога
            log_lines = read_last_log_lines(3)
            if log_lines:
                print("\n\n📝 Последние события:")
                for line in log_lines:
                    line = line.strip()
                    if line and ('БАТЧ' in line or '✅' in line or 'Осталось' in line):
                        print(f"  {line[:76]}")
            
            print("\n" + "="*80)
            
            time.sleep(5)
            print("\033[F" * 8, end='')  # Поднимаемся на 8 строк вверх
            
    except KeyboardInterrupt:
        print("\n\n✋ Мониторинг остановлен\n")


if __name__ == "__main__":
    main()

