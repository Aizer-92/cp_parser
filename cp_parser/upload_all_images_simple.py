#!/usr/bin/env python3
"""
Простая загрузка ВСЕХ изображений из storage/images на FTP
Потом обновляет image_url в БД по filename
"""

import sys
from pathlib import Path
from ftplib import FTP_TLS
import time

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# FTP настройки
FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

def upload_all_images():
    """Загружает ВСЕ изображения на FTP"""
    
    images_dir = Path("storage/images")
    all_images = [f for f in images_dir.glob("*") if f.is_file()]
    
    print("=" * 80)
    print("🚀 ЗАГРУЗКА ВСЕХ ИЗОБРАЖЕНИЙ НА FTP")
    print("=" * 80)
    print(f"\n📊 Всего изображений в папке: {len(all_images):,}")
    
    # Подключаемся к FTP
    print(f"\n🔌 Подключение к FTP: {FTP_HOST}")
    ftp = FTP_TLS(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.prot_p()
    
    try:
        ftp.cwd(FTP_DIR)
    except:
        print(f"📁 Создаю директорию: {FTP_DIR}")
        ftp.mkd(FTP_DIR)
        ftp.cwd(FTP_DIR)
    
    # Получаем список уже загруженных файлов
    print("\n📋 Проверяю существующие файлы на FTP...")
    existing_files = set()
    try:
        ftp.retrlines('NLST', existing_files.add)
    except:
        pass
    
    print(f"✅ Уже на FTP: {len(existing_files):,} файлов")
    
    # Загружаем файлы
    uploaded = 0
    skipped = 0
    errors = 0
    
    print(f"\n🔄 Начинаю загрузку...")
    start_time = time.time()
    
    for i, img_file in enumerate(all_images, 1):
        filename = img_file.name
        
        # Пропускаем если уже есть
        if filename in existing_files:
            skipped += 1
            continue
        
        try:
            # Загружаем
            with open(img_file, 'rb') as f:
                ftp.storbinary(f'STOR {filename}', f)
            
            uploaded += 1
            
            # Прогресс каждые 100 файлов
            if uploaded % 100 == 0:
                elapsed = time.time() - start_time
                speed = uploaded / elapsed if elapsed > 0 else 0
                remaining = len(all_images) - skipped - uploaded
                eta_minutes = int(remaining / speed / 60) if speed > 0 else 0
                
                print(f"  📤 {uploaded:,}/{len(all_images):,} | {speed:.1f} файлов/сек | ETA: ~{eta_minutes} мин")
        
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  ❌ Ошибка ({filename}): {e}")
    
    ftp.quit()
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("✅ ЗАГРУЗКА НА FTP ЗАВЕРШЕНА!")
    print("=" * 80)
    print(f"\n📊 Результаты:")
    print(f"  ✅ Загружено: {uploaded:,}")
    print(f"  ⏭️  Пропущено (уже есть): {skipped:,}")
    print(f"  ❌ Ошибок: {errors:,}")
    print(f"  ⏱️  Время: {int(elapsed/60)} мин {int(elapsed%60)} сек")
    if uploaded > 0:
        print(f"  🚀 Средняя скорость: {uploaded/elapsed:.1f} файлов/сек")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    upload_all_images()



