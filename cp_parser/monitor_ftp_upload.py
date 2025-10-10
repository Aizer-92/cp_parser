#!/usr/bin/env python3
"""
Мониторинг загрузки изображений Шаблона 6 на FTP
"""

import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

def monitor_upload():
    """Мониторит прогресс загрузки"""
    
    db = PostgreSQLManager()
    images_dir = Path("storage/images")
    
    # Считаем ВСЕ файлы в папке для загрузки
    total_files = len([
        f for f in images_dir.glob("*")
        if f.is_file()
    ])
    
    print("=" * 80)
    print("📊 МОНИТОРИНГ ЗАГРУЗКИ ИЗОБРАЖЕНИЙ НА FTP")
    print("=" * 80)
    print(f"\n📁 Всего файлов для загрузки: {total_files:,}")
    
    last_uploaded = 0
    iteration = 0
    
    while True:
        iteration += 1
        
        with db.get_session() as session:
            # Считаем сколько URL уже обновлено (загружено) - ВСЕ изображения
            uploaded = session.execute(text("""
                SELECT COUNT(*)
                FROM product_images
                WHERE image_url LIKE 'https://s3.ru1.storage.beget.cloud%'
            """)).scalar()
            
            # Прогресс
            progress = (uploaded * 100 // total_files) if total_files > 0 else 0
            remaining = total_files - uploaded
            
            # Скорость
            speed = uploaded - last_uploaded if iteration > 1 else 0
            eta_minutes = (remaining / speed) if speed > 0 else 0
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Итерация #{iteration}")
            print(f"  📤 Загружено: {uploaded:,}/{total_files:,} ({progress}%)")
            print(f"  ⏳ Осталось: {remaining:,}")
            
            if speed > 0:
                print(f"  🚀 Скорость: ~{speed} файлов/10 сек")
                print(f"  ⏱️  Осталось времени: ~{int(eta_minutes)} минут")
            
            # Если все загружено
            if uploaded >= total_files:
                print("\n" + "=" * 80)
                print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
                print("=" * 80)
                break
            
            last_uploaded = uploaded
        
        # Пауза 10 секунд
        time.sleep(10)

if __name__ == '__main__':
    try:
        monitor_upload()
    except KeyboardInterrupt:
        print("\n\n⏹️  Мониторинг остановлен")

