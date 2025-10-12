#!/usr/bin/env python3
"""
Обновление URL для дополнительных фото (с суффиксами _1_, _2_, _3_)
Файлы УЖЕ загружены на S3, нужно только обновить image_url в БД
"""

import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

db = PostgreSQLManager()

print("=" * 80)
print("🔄 ОБНОВЛЕНИЕ URL ДОПОЛНИТЕЛЬНЫХ ФОТО")
print("=" * 80)

with open('template_4_perfect_ids.txt', 'r') as f:
    project_ids = [int(line.strip()) for line in f if line.strip()]

with db.get_session() as session:
    # Получаем ВСЕ изображения из Шаблона 4 без URL
    result = session.execute(text("""
        SELECT 
            pi.id,
            pi.image_filename
        FROM product_images pi
        JOIN products p ON pi.product_id = p.id
        WHERE p.project_id = ANY(:ids)
        AND (pi.image_url IS NULL OR pi.image_url = '')
        ORDER BY pi.id
    """), {'ids': project_ids}).fetchall()
    
    # Фильтруем: только с суффиксами
    to_update = []
    for row in result:
        img_id, filename = row
        parts = filename.replace('.png', '').split('_')
        
        if len(parts) >= 4:
            try:
                int(parts[-2])  # Если это число - значит суффикс есть
                to_update.append((img_id, filename))
            except ValueError:
                pass
    
    print(f"\n📊 Найдено дополнительных фото: {len(to_update):,}")
    
    if not to_update:
        print("\n✅ Все URL уже обновлены!")
        print("=" * 80)
        exit(0)
    
    print(f"\n🔄 Обновляю URL...")
    
    updated = 0
    for img_id, filename in to_update:
        # Формируем правильный URL
        url = f"https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}"
        
        session.execute(text("""
            UPDATE product_images 
            SET image_url = :url 
            WHERE id = :img_id
        """), {'url': url, 'img_id': img_id})
        
        updated += 1
        
        if updated % 100 == 0:
            print(f"   ⏳ {updated}/{len(to_update)}...",flush=True)
    
    session.commit()
    
    print(f"\n✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
    print(f"   Обновлено URL: {updated:,}")
    print("=" * 80)





"""
Обновление URL для дополнительных фото (с суффиксами _1_, _2_, _3_)
Файлы УЖЕ загружены на S3, нужно только обновить image_url в БД
"""

import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

db = PostgreSQLManager()

print("=" * 80)
print("🔄 ОБНОВЛЕНИЕ URL ДОПОЛНИТЕЛЬНЫХ ФОТО")
print("=" * 80)

with open('template_4_perfect_ids.txt', 'r') as f:
    project_ids = [int(line.strip()) for line in f if line.strip()]

with db.get_session() as session:
    # Получаем ВСЕ изображения из Шаблона 4 без URL
    result = session.execute(text("""
        SELECT 
            pi.id,
            pi.image_filename
        FROM product_images pi
        JOIN products p ON pi.product_id = p.id
        WHERE p.project_id = ANY(:ids)
        AND (pi.image_url IS NULL OR pi.image_url = '')
        ORDER BY pi.id
    """), {'ids': project_ids}).fetchall()
    
    # Фильтруем: только с суффиксами
    to_update = []
    for row in result:
        img_id, filename = row
        parts = filename.replace('.png', '').split('_')
        
        if len(parts) >= 4:
            try:
                int(parts[-2])  # Если это число - значит суффикс есть
                to_update.append((img_id, filename))
            except ValueError:
                pass
    
    print(f"\n📊 Найдено дополнительных фото: {len(to_update):,}")
    
    if not to_update:
        print("\n✅ Все URL уже обновлены!")
        print("=" * 80)
        exit(0)
    
    print(f"\n🔄 Обновляю URL...")
    
    updated = 0
    for img_id, filename in to_update:
        # Формируем правильный URL
        url = f"https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}"
        
        session.execute(text("""
            UPDATE product_images 
            SET image_url = :url 
            WHERE id = :img_id
        """), {'url': url, 'img_id': img_id})
        
        updated += 1
        
        if updated % 100 == 0:
            print(f"   ⏳ {updated}/{len(to_update)}...",flush=True)
    
    session.commit()
    
    print(f"\n✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
    print(f"   Обновлено URL: {updated:,}")
    print("=" * 80)








