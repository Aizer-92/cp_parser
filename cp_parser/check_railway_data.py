#!/usr/bin/env python3
"""
Проверка данных на Railway PostgreSQL
"""

import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import re

sys.path.insert(0, str(Path(__file__).parent))

RAILWAY_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

def get_pending_project_ids():
    """Получает project_id из pending файлов"""
    valid_list = Path('valid_pending_files.txt')
    if not valid_list.exists():
        valid_list = Path('valid_files_list.txt')
    
    with open(valid_list, 'r') as f:
        files = [line.strip() for line in f if line.strip()]
    
    project_ids = []
    for filename in files:
        match = re.search(r'project_(\d+)_', filename)
        if match:
            project_ids.append(int(match.group(1)))
    
    return project_ids

def check_railway_data():
    """Проверяет данные на Railway"""
    project_ids = get_pending_project_ids()
    
    print("\n" + "=" * 80)
    print("📊 ПРОВЕРКА ДАННЫХ НА RAILWAY POSTGRESQL")
    print("=" * 80)
    print(f"\n📁 Pending проектов для проверки: {len(project_ids)}\n")
    
    try:
        conn = psycopg2.connect(RAILWAY_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Формируем плейсхолдеры
        placeholders = ','.join(['%s'] * len(project_ids))
        
        # Проверяем проекты
        cursor.execute(f"""
            SELECT COUNT(*) as count FROM projects WHERE id IN ({placeholders})
        """, project_ids)
        projects_count = cursor.fetchone()['count']
        
        # Проверяем товары
        cursor.execute(f"""
            SELECT COUNT(*) as count FROM products WHERE project_id IN ({placeholders})
        """, project_ids)
        products_count = cursor.fetchone()['count']
        
        # Проверяем предложения
        cursor.execute(f"""
            SELECT COUNT(*) as count 
            FROM price_offers po
            JOIN products p ON po.product_id = p.id
            WHERE p.project_id IN ({placeholders})
        """, project_ids)
        offers_count = cursor.fetchone()['count']
        
        # Проверяем изображения
        cursor.execute(f"""
            SELECT COUNT(*) as count 
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id IN ({placeholders})
        """, project_ids)
        images_count = cursor.fetchone()['count']
        
        # Получаем 10 примеров товаров
        cursor.execute(f"""
            SELECT p.id, p.project_id, p.name,
                   (SELECT COUNT(*) FROM price_offers WHERE product_id = p.id) as offers,
                   (SELECT COUNT(*) FROM product_images WHERE product_id = p.id) as images
            FROM products p
            WHERE p.project_id IN ({placeholders})
            ORDER BY p.id DESC
            LIMIT 10
        """, project_ids)
        sample_products = cursor.fetchall()
        
        conn.close()
        
        print("✅ ДАННЫЕ НА RAILWAY:")
        print("=" * 80)
        print(f"📦 Проекты: {projects_count}")
        print(f"📦 Товары: {products_count}")
        print(f"💰 Предложения: {offers_count}")
        print(f"🖼️  Изображения: {images_count}")
        print("")
        print("=" * 80)
        print("📋 10 ПОСЛЕДНИХ ТОВАРОВ ДЛЯ ПРОВЕРКИ:")
        print("=" * 80)
        
        for prod in sample_products:
            print(f"ID: {prod['id']:5d} | Проект: {prod['project_id']:4d} | "
                  f"Офферы: {prod['offers']:2d} | Фото: {prod['images']:2d} | {prod['name'][:50]}")
        
        print("\n" + "=" * 80)
        print(f"📝 ID для проверки: {', '.join(str(p['id']) for p in sample_products)}")
        print("=" * 80)
        print(f"\n🌐 Railway URL: {RAILWAY_URL}")
        print("\n✅ Проверка завершена!")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    check_railway_data()



