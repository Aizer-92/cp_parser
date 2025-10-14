#!/usr/bin/env python3
"""
Перепривязка ВСЕХ изображений проекта #1307 по диапазонам из Google Sheets
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import gspread
from google.oauth2.service_account import Credentials

def get_ranges_from_sheets():
    """Получить диапазоны товаров из Google Sheets"""
    creds_path = Path('../cp_parser_core/config/service_account.json')
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(str(creds_path), scopes=scope)
    client = gspread.authorize(creds)
    
    table_id = '1WIJPZDUtWlRh-NSuecdims3Bc-slmRz6r4PyPrXgXW8'
    spreadsheet = client.open_by_key(table_id)
    worksheet = spreadsheet.get_worksheet(0)
    all_values = worksheet.get_all_values()
    
    # Определяем диапазоны
    products = []
    current_product = None
    product_start = None
    
    for row_idx in range(3, min(100, len(all_values))):
        row_num = row_idx + 1
        row = all_values[row_idx]
        
        product_name = row[1].strip() if len(row) > 1 else ""
        
        if product_name:
            if current_product:
                products.append({
                    'name': current_product,
                    'start': product_start,
                    'end': row_num - 1
                })
            
            current_product = product_name
            product_start = row_num
    
    if current_product:
        products.append({
            'name': current_product,
            'start': product_start,
            'end': row_num
        })
    
    return products


db = PostgreSQLManager()

print("\n" + "="*80)
print("🔄 ПЕРЕПРИВЯЗКА ИЗОБРАЖЕНИЙ ПРОЕКТА #1307")
print("="*80 + "\n")

# 1. Получаем диапазоны из Google Sheets
print("📊 Загрузка диапазонов из Google Sheets...")
gs_ranges = get_ranges_from_sheets()
print(f"   Найдено {len(gs_ranges)} товаров\n")

with db.get_session() as session:
    # 2. Получаем все товары из БД
    products = session.execute(
        text("""
            SELECT id, name
            FROM products
            WHERE project_id = 1307
            ORDER BY id
        """)
    ).fetchall()
    
    print(f"📦 Товаров в БД: {len(products)}\n")
    
    # 3. Получаем ВСЕ изображения проекта
    all_images = session.execute(
        text("""
            SELECT id, cell_position, image_url
            FROM product_images
            WHERE table_id = '1WIJPZDUtWlRh-NSuecdims3Bc-slmRz6r4PyPrXgXW8'
              AND cell_position ~ '^[A-Z]+[0-9]+$'
            ORDER BY cell_position
        """)
    ).fetchall()
    
    print(f"📸 Всего изображений: {len(all_images)}\n")
    print("🔄 ПЕРЕПРИВЯЗКА:\n")
    
    relinked_count = 0
    
    for prod_id, prod_name in products:
        # Находим диапазон для этого товара
        matching = [r for r in gs_ranges if prod_name.lower() in r['name'].lower()]
        
        if not matching:
            print(f"⚠️  #{prod_id:5} {prod_name[:40]:40} - не найден в Google Sheets")
            continue
        
        gs_range = matching[0]
        row_start = gs_range['start']
        row_end = gs_range['end']
        
        # Обновляем row_number
        session.execute(
            text("UPDATE products SET row_number = :row_num WHERE id = :prod_id"),
            {'row_num': row_start, 'prod_id': prod_id}
        )
        
        # Находим изображения в этом диапазоне
        images_for_product = []
        for img_id, cell_pos, img_url in all_images:
            try:
                row_num = int(''.join(filter(str.isdigit, cell_pos)))
                if row_start <= row_num <= row_end:
                    images_for_product.append((img_id, cell_pos))
            except:
                continue
        
        if images_for_product:
            # Привязываем изображения к этому товару
            for img_id, cell_pos in images_for_product:
                is_main = 'true' if cell_pos.startswith('A') else 'false'
                
                session.execute(
                    text("""
                        UPDATE product_images
                        SET product_id = :prod_id,
                            is_main_image = :is_main,
                            updated_at = NOW()
                        WHERE id = :img_id
                    """),
                    {'prod_id': prod_id, 'img_id': img_id, 'is_main': is_main}
                )
                relinked_count += 1
            
            positions = [pos for _, pos in images_for_product[:5]]
            more = f" +{len(images_for_product)-5}" if len(images_for_product) > 5 else ""
            print(f"✅ #{prod_id:5} {prod_name[:40]:40} → [{row_start:2}-{row_end:2}] → {len(images_for_product):2} изобр: {', '.join(positions)}{more}")
        else:
            print(f"⚠️  #{prod_id:5} {prod_name[:40]:40} → [{row_start:2}-{row_end:2}] → 0 изобр")
    
    session.commit()
    
    print("\n" + "="*80)
    print("📊 ИТОГИ:")
    print("="*80)
    print(f"  Изображений перепривязано:  {relinked_count}")
    print("="*80 + "\n")

