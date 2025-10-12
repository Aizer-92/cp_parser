#!/usr/bin/env python3
"""
Простой мониторинг загрузки изображений на FTP
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import time

def monitor():
    db = PostgreSQLManager()
    
    print("=" * 80)
    print("📊 МОНИТОРИНГ FTP ЗАГРУЗКИ")
    print("=" * 80)
    
    with db.get_session() as session:
        # Всего изображений
        total = session.execute(text("""
            SELECT COUNT(*) FROM product_images
        """)).scalar()
        
        # На FTP
        on_ftp = session.execute(text("""
            SELECT COUNT(*) FROM product_images
            WHERE image_url LIKE 'https://%'
        """)).scalar()
        
        # Локальные существующие
        local_all = session.execute(text("""
            SELECT image_url FROM product_images
            WHERE image_url NOT LIKE 'https://%'
        """)).fetchall()
        
        local_existing = sum(1 for img in local_all if Path(img.image_url).exists())
        local_missing = len(local_all) - local_existing
        
        print(f"\n📊 СТАТИСТИКА:")
        print(f"  Всего изображений: {total:,}")
        print(f"  ✅ На FTP: {on_ftp:,} ({on_ftp*100//total}%)")
        print(f"  📁 Локальные (существуют): {local_existing:,}")
        print(f"  ❌ Файлы не найдены: {local_missing:,}")
        
        remaining = local_existing
        print(f"\n⏳ ОСТАЛОСЬ ЗАГРУЗИТЬ: {remaining:,}")
        
        if remaining > 0:
            # Прогресс бар
            progress = on_ftp / (on_ftp + remaining) * 100
            bar_length = 50
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\n  [{bar}] {progress:.1f}%")
            
            # Проверяем лог
            log_path = Path("upload_ftp_log.txt")
            if log_path.exists():
                print(f"\n📄 ПОСЛЕДНИЕ СТРОКИ ЛОГА:")
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-5:]:
                        print(f"  {line.strip()}")
        else:
            print("\n🎉 ЗАГРУЗКА ЗАВЕРШЕНА!")
    
    print("=" * 80)

if __name__ == "__main__":
    try:
        while True:
            monitor()
            print("\n⏰ Обновление через 30 секунд... (Ctrl+C для выхода)")
            time.sleep(30)
            print("\n" * 2)
    except KeyboardInterrupt:
        print("\n\n✋ Мониторинг остановлен")


