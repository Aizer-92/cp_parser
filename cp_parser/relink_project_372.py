#!/usr/bin/env python3
"""
Перепривязка изображений проекта #372 по диапазонам из Google Sheets
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
    
    table_id = '1Y_2xjq5aUBCgJCgEQLwaQ7VsSstvW2a_16DF0Ypuk_U'
    spreadsheet = client.open_by_key(table_id)
    worksheet = spreadsheet.get_worksheet(0)
    all_values = worksheet.get_all_values()
    
    products_found = []
    for row_idx in range(3, min(100, len(all_values))):
        row_num = row_idx + 1
        row = all_values[row_idx]
        
        product_name = row[1].strip() if len(row) > 1 else ""
        
        if product_name:
            products_found.append({
                'row': row_num,
                'name': product_name
            })
    
    # Определяем диапазоны
    products_with_ranges = []
    for i, prod in enumerate(products_found):
        if i < len(products_found) - 1:
            next_row = products_found[i + 1]['row']
            end_row = next_row - 1
        else:
            end_row = prod['row'] + 2
        
        products_with_ranges.append({
            'name': prod['name'],
            'start': prod['row'],
            'end': end_row
        })
    
    return products_with_ranges


db = PostgreSQLManager()

print("\n" + "="*80)
print("🔄 ПЕРЕПРИВЯЗКА ИЗОБРАЖЕНИЙ ПРОЕКТА #372")
print("="*80 + "\n")

print("📊 Загрузка диапазонов из Google Sheets...")
gs_ranges = get_ranges_from_sheets()
print(f"   Найдено {len(gs_ranges)} товаров\n")

with db.get_session() as session:
    # Получаем все товары из БД
    products = session.execute(
        text("""
            SELECT id, name
            FROM products
            WHERE project_id = 372
            ORDER BY id
        """)
    ).fetchall()
    
    print(f"📦 Товаров в БД: {len(products)}\n")
    
    # Получаем ВСЕ изображения проекта (через product_id)
    all_images = session.execute(
        text("""
            SELECT id, cell_position, image_url
            FROM product_images
            WHERE product_id IN (SELECT id FROM products WHERE project_id = 372)
              AND cell_position ~ '^[A-Z]+[0-9]+$'
            ORDER BY cell_position
        """)
    ).fetchall()
    
    print(f"📸 Всего изображений: {len(all_images)}\n")
    print("🔄 ПЕРЕПРИВЯЗКА:\n")
    
    relinked_count = 0
    no_images_count = 0
    
    for prod_id, prod_name in products:
        # Находим диапазон для этого товара (с учетом частичного совпадения)
        matching = []
        for gs_range in gs_ranges:
            # Проверяем частичное совпадение названий
            if prod_name.lower()[:30] in gs_range['name'].lower()[:30]:
                matching.append(gs_range)
        
        if not matching:
            print(f"⚠️  #{prod_id:5} {prod_name[:40]:40} - не найден в Google Sheets")
            no_images_count += 1
            continue
        
        # Берем первый подходящий диапазон
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
            # Сбрасываем все is_main для этого товара
            session.execute(
                text("""
                    UPDATE product_images
                    SET is_main_image = 'false'
                    WHERE product_id = :prod_id
                """),
                {'prod_id': prod_id}
            )
            
            # Привязываем изображения
            main_set = False
            for img_id, cell_pos in images_for_product:
                # Первое изображение из столбца A = главное
                is_main = 'false'
                if not main_set and cell_pos.startswith('A'):
                    is_main = 'true'
                    main_set = True
                
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
            
            # Если не нашли главное из A, назначаем первое
            if not main_set and images_for_product:
                first_img_id = images_for_product[0][0]
                session.execute(
                    text("UPDATE product_images SET is_main_image = 'true' WHERE id = :img_id"),
                    {'img_id': first_img_id}
                )
            
            positions = [pos for _, pos in images_for_product[:3]]
            more = f" +{len(images_for_product)-3}" if len(images_for_product) > 3 else ""
            print(f"✅ #{prod_id:5} {prod_name[:35]:35} → [{row_start:2}-{row_end:2}] → {len(images_for_product):2} изобр: {', '.join(positions)}{more}")
        else:
            print(f"⚠️  #{prod_id:5} {prod_name[:35]:35} → [{row_start:2}-{row_end:2}] → 0 изобр")
            no_images_count += 1
    
    session.commit()
    
    print("\n" + "="*80)
    print("📊 ИТОГИ:")
    print("="*80)
    print(f"  Изображений перепривязано:  {relinked_count}")
    print(f"  Товаров без изображений:    {no_images_count}")
    print("="*80 + "\n")

