#!/usr/bin/env python3
"""
Обновление URL для ВСЕХ фото Шаблона 4 (основных и дополнительных)
Файлы УЖЕ на S3, нужно только обновить image_url в БД
"""

import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

db = PostgreSQLManager()

print("=" * 80)
print("🔄 ОБНОВЛЕНИЕ URL ВСЕХ ФОТО ШАБЛОНА 4")
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
    
    total = len(result)
    
    print(f"\n📊 Найдено изображений без URL: {total:,}")
    
    if total == 0:
        print("\n✅ Все URL уже обновлены!")
        print("=" * 80)
        exit(0)
    
    print(f"\n🔄 Обновляю URL...")
    
    updated = 0
    for img_id, filename in result:
        # Формируем правильный URL (одинаковый для всех)
        url = f"https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}"
        
        session.execute(text("""
            UPDATE product_images 
            SET image_url = :url 
            WHERE id = :img_id
        """), {'url': url, 'img_id': img_id})
        
        updated += 1
        
        if updated % 200 == 0:
            print(f"   ⏳ {updated}/{total}...", flush=True)
    
    session.commit()
    
    print(f"\n✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
    print(f"   Обновлено URL: {updated:,}")
    print("=" * 80)




