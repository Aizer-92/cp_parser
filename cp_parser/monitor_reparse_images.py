#!/usr/bin/env python3
"""
Мониторинг парсинга изображений
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

def monitor():
    """Показывает прогресс парсинга изображений"""
    
    db = PostgreSQLManager()
    
    # Читаем список проектов
    with open('projects_need_images.txt', 'r') as f:
        project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    total = len(project_ids)
    
    while True:
        print("\n" + "=" * 80)
        print(f"🖼️  МОНИТОРИНГ ПАРСИНГА ИЗОБРАЖЕНИЙ")
        print("=" * 80)
        
        with db.get_session() as session:
            # Статистика по 132 проблемным проектам
            stats = session.execute(text("""
                SELECT 
                    COUNT(DISTINCT p.id) as products_with_images,
                    COUNT(DISTINCT pi.id) as total_images,
                    COUNT(DISTINCT CASE WHEN pi.image_url LIKE 'storage/%' THEN pi.id END) as local_images
                FROM projects proj
                JOIN products p ON p.table_id = proj.table_id
                LEFT JOIN product_images pi ON pi.product_id = p.id
                WHERE proj.id = ANY(:project_ids)
            """), {'project_ids': project_ids}).first()
            
            # Изображения созданные недавно (за последние 10 минут)
            recent = session.execute(text("""
                SELECT COUNT(*) 
                FROM product_images pi
                JOIN products p ON p.id = pi.product_id
                JOIN projects proj ON proj.table_id = p.table_id
                WHERE proj.id = ANY(:project_ids)
                AND pi.image_url LIKE 'storage/%'
            """), {'project_ids': project_ids}).scalar()
        
        print(f"\n📊 СТАТИСТИКА:")
        print(f"  Проектов обрабатывается:  {total}")
        print(f"  Товаров с изображениями:  {stats.products_with_images:,}")
        print(f"  Всего изображений:        {stats.total_images:,}")
        print(f"  Локальных изображений:    {stats.local_images:,}")
        
        # Локальные файлы
        local_dir = Path('storage/images')
        if local_dir.exists():
            local_files = list(local_dir.glob('*'))
            local_count = len(local_files)
            total_size = sum(f.stat().st_size for f in local_files if f.is_file())
        else:
            local_count = 0
            total_size = 0
        
        print(f"\n💾 ЛОКАЛЬНЫЕ ФАЙЛЫ:")
        print(f"  Файлов в storage/images:  {local_count:,}")
        print(f"  Общий размер:             {total_size/1024/1024:.1f} МБ")
        
        # Проверяем лог
        log_file = Path('reparse_images.log')
        if log_file.exists():
            # Последние 3 строки из лога
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    # Ищем строку с прогрессом
                    for line in reversed(lines[-20:]):
                        if '/132]' in line:
                            print(f"\n📝 ПРОГРЕСС:")
                            print(f"  {line.strip()}")
                            break
        
        print("=" * 80)
        print("\n⏳ Обновление через 15 секунд... (Ctrl+C для выхода)")
        time.sleep(15)

if __name__ == '__main__':
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n\n👋 Мониторинг остановлен")


