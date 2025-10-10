#!/usr/bin/env python3
"""
Загрузка изображений Шаблона 5 на Beget FTP
"""

import sys
from pathlib import Path
from ftplib import FTP_TLS
from sqlalchemy import text
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

# FTP настройки Beget
FTP_HOST = 'ftp.ru1.storage.beget.cloud'
FTP_USER = 'RECD00AQJIM4300MLJ0W'
FTP_PASS = 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
FTP_PATH = '/73d16f7545b3-promogoods/images/'

def main():
    db = PostgreSQLManager()
    
    print("=" * 80)
    print("🚀 ЗАГРУЗКА ИЗОБРАЖЕНИЙ ШАБЛОНА 5 НА FTP")
    print("=" * 80)
    
    # Получаем список ID проектов Шаблона 5
    with open('template_5_candidate_ids.txt', 'r') as f:
        template5_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print(f"\n📋 Проектов Шаблона 5: {len(template5_ids)}")
    
    # Получаем изображения для загрузки
    with db.get_session() as session:
        images = session.execute(text("""
            SELECT pi.id, pi.image_filename, pi.local_path, pi.image_url
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(:ids)
            AND pi.local_path IS NOT NULL
            ORDER BY pi.id
        """), {'ids': template5_ids}).fetchall()
        
        print(f"🖼️  Изображений для загрузки: {len(images)}")
        
        # Проверяем сколько уже загружено
        already_uploaded = sum(1 for img in images if img[3] and 'beget.cloud' in img[3])
        print(f"✅ Уже загружено: {already_uploaded}")
        print(f"📤 Нужно загрузить: {len(images) - already_uploaded}")
    
    if len(images) == already_uploaded:
        print("\n✅ Все изображения уже загружены!")
        return
    
    print(f"\n🔌 Подключаюсь к FTP...")
    ftp = FTP_TLS(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.prot_p()  # Защищенный канал данных
    ftp.cwd(FTP_PATH)
    print(f"✅ Подключен к {FTP_HOST}")
    
    # Получаем список уже загруженных файлов
    existing_files = set(ftp.nlst())
    print(f"📁 Файлов на FTP: {len(existing_files)}")
    
    uploaded = 0
    skipped = 0
    errors = 0
    
    print(f"\n🚀 Начинаю загрузку...")
    
    for img_id, filename, local_path, image_url in images:
        # Пропускаем уже загруженные
        if image_url and 'beget.cloud' in image_url:
            skipped += 1
            continue
        
        # Проверяем существование файла
        local_file = Path(local_path)
        if not local_file.exists():
            print(f"⚠️  Файл не найден: {local_path}")
            errors += 1
            continue
        
        # Загружаем только если файла нет на FTP
        if filename not in existing_files:
            try:
                with open(local_file, 'rb') as f:
                    ftp.storbinary(f'STOR {filename}', f)
                uploaded += 1
                
                if uploaded % 100 == 0:
                    print(f"  ⏳ Загружено: {uploaded} изображений...")
                    
            except Exception as e:
                print(f"❌ Ошибка загрузки {filename}: {e}")
                errors += 1
                continue
        else:
            skipped += 1
        
        # Обновляем URL в БД (ПРАВИЛЬНЫЙ формат с s3. префиксом!)
        new_url = f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}"
        
        with db.get_session() as session:
            session.execute(text("""
                UPDATE product_images
                SET image_url = :url
                WHERE id = :id
            """), {'url': new_url, 'id': img_id})
            session.commit()
    
    ftp.quit()
    
    print("\n" + "=" * 80)
    print("✅ ЗАГРУЗКА ЗАВЕРШЕНА")
    print("=" * 80)
    print(f"\n📊 Статистика:")
    print(f"  • Загружено:  {uploaded}")
    print(f"  • Пропущено:  {skipped}")
    print(f"  • Ошибок:     {errors}")
    print(f"  • Всего:      {len(images)}")
    print("=" * 80)

if __name__ == '__main__':
    main()

