#!/usr/bin/env python3
"""
Загрузка изображений Шаблона 6 на FTP
Загружает только изображения из проектов Template 6 которые еще не на FTP
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
FTP_USER = "73d16f7545b3"
FTP_PASS = "zpS64xT0"
FTP_DIR = "/73d16f7545b3-promogoods/images"

def upload_to_ftp():
    """Загружает изображения Template 6 на FTP"""
    
    db = PostgreSQLManager()
    
    # Получаем ID проектов Template 6
    with open('template6_project_ids.txt', 'r') as f:
        template6_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print("=" * 80)
    print("🚀 ЗАГРУЗКА ИЗОБРАЖЕНИЙ ШАБЛОНА 6 НА FTP")
    print("=" * 80)
    
    # Получаем список локальных путей к изображениям Template 6
    with db.get_session() as session:
        images = session.execute(text("""
            SELECT DISTINCT pi.image_url
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(:ids)
            AND pi.image_url NOT LIKE 'https://%'
        """), {'ids': template6_ids}).fetchall()
    
    print(f"\n📊 Изображений для загрузки: {len(images):,}")
    
    if not images:
        print("✅ Все изображения уже загружены!")
        return
    
    # Подключаемся к FTP
    print(f"\n🔌 Подключение к FTP: {FTP_HOST}")
    ftp = FTP_TLS(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.prot_p()  # Защищенный канал данных
    
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
    
    print(f"✅ Найдено на FTP: {len(existing_files):,} файлов")
    
    # Загружаем файлы
    uploaded = 0
    skipped = 0
    errors = 0
    not_found = 0
    
    print(f"\n🔄 Начинаю загрузку...")
    start_time = time.time()
    
    for i, (local_path,) in enumerate(images, 1):
        # Получаем имя файла из локального пути
        filename = Path(local_path).name
        local_file = Path("storage/images") / filename
        
        # Проверяем существование локального файла
        if not local_file.exists():
            not_found += 1
            continue
        
        # Пропускаем если уже загружен
        if filename in existing_files:
            skipped += 1
            continue
        
        try:
            # Загружаем файл
            with open(local_file, 'rb') as f:
                ftp.storbinary(f'STOR {filename}', f)
            
            # Обновляем URL в БД
            new_url = f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}"
            
            with db.get_session() as session:
                session.execute(
                    text("UPDATE product_images SET image_url = :url WHERE image_url = :old_url"),
                    {'url': new_url, 'old_url': local_path}
                )
                session.commit()
            
            uploaded += 1
            
            # Прогресс каждые 100 файлов
            if uploaded % 100 == 0:
                elapsed = time.time() - start_time
                speed = uploaded / elapsed
                remaining = len(images) - i
                eta_seconds = remaining / speed if speed > 0 else 0
                eta_minutes = int(eta_seconds / 60)
                
                print(f"  📤 {uploaded:,}/{len(images):,} | {speed:.1f} файлов/сек | Осталось: ~{eta_minutes} мин")
        
        except Exception as e:
            errors += 1
            if errors <= 5:  # Показываем первые 5 ошибок
                print(f"  ❌ Ошибка ({filename}): {e}")
    
    ftp.quit()
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
    print("=" * 80)
    print(f"\n📊 Результаты:")
    print(f"  ✅ Загружено: {uploaded:,}")
    print(f"  ⏭️  Пропущено (уже есть): {skipped:,}")
    print(f"  ❌ Не найдено локально: {not_found:,}")
    print(f"  ❌ Ошибок: {errors:,}")
    print(f"  ⏱️  Время: {int(elapsed/60)} мин {int(elapsed%60)} сек")
    if uploaded > 0:
        print(f"  🚀 Средняя скорость: {uploaded/elapsed:.1f} файлов/сек")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    upload_to_ftp()


