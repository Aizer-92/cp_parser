#!/usr/bin/env python3
"""
Массовая обработка проектов батчами:
1. Анализ Google Sheets для определения диапазонов товаров
2. Удаление дубликатов изображений
3. Перепривязка изображений по диапазонам
4. Назначение главных изображений из столбца A
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import gspread
from google.oauth2.service_account import Credentials
import time


def get_projects_for_processing(batch_num=1, batch_size=20):
    """Получить список проектов для обработки"""
    db = PostgreSQLManager()
    
    with db.get_session() as session:
        projects = session.execute(
            text("""
                SELECT 
                    proj.id as project_id,
                    proj.table_id,
                    COUNT(DISTINCT p.id) as products_total,
                    COUNT(pi.id) as images_total,
                    COUNT(DISTINCT pi.image_url) as unique_images
                FROM projects proj
                LEFT JOIN products p ON proj.id = p.project_id
                LEFT JOIN product_images pi ON p.id = pi.product_id
                WHERE proj.id IN (
                    SELECT DISTINCT project_id 
                    FROM products 
                    WHERE row_number IS NULL
                )
                AND proj.table_id IS NOT NULL
                GROUP BY proj.id, proj.table_id
                HAVING COUNT(DISTINCT p.id) > 0
                ORDER BY (COUNT(pi.id) - COUNT(DISTINCT pi.image_url)) DESC, proj.id
                LIMIT :limit OFFSET :offset
            """),
            {'limit': batch_size, 'offset': (batch_num - 1) * batch_size}
        ).fetchall()
        
        return [
            {
                'id': p[0],
                'table_id': p[1],
                'products': p[2],
                'images': p[3],
                'unique': p[4],
                'duplicates': p[3] - p[4]
            }
            for p in projects
        ]


def analyze_google_sheets(table_id, max_rows=100):
    """Анализ Google Sheets для определения диапазонов товаров"""
    try:
        # Подключение к Google Sheets
        creds_path = Path('../cp_parser_core/config/service_account.json')
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(str(creds_path), scopes=scope)
        client = gspread.authorize(creds)
        
        # Открываем таблицу с retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                spreadsheet = client.open_by_key(table_id)
                worksheet = spreadsheet.get_worksheet(0)
                all_values = worksheet.get_all_values()
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise
        
        # Анализируем структуру (начинаем с строки 4, индекс 3)
        products_gs = []
        current_product = None
        product_start = None
        
        for row_idx in range(3, min(max_rows + 3, len(all_values))):
            row_num = row_idx + 1
            row = all_values[row_idx]
            
            # Проверяем колонку B (индекс 1) - "Наименование"
            product_name = row[1].strip() if len(row) > 1 else ""
            
            # Колонка E - "Тираж"
            quantity = row[4].strip() if len(row) > 4 else ""
            
            if product_name:  # Если есть название товара
                # Сохраняем предыдущий товар
                if current_product:
                    products_gs.append({
                        'name': current_product,
                        'start': product_start,
                        'end': row_num - 1
                    })
                
                # Начинаем новый товар
                current_product = product_name
                product_start = row_num
            
            elif current_product and not quantity:
                # Пустая строка без данных может означать конец товара
                # Но продолжаем пока не встретим следующий товар
                pass
        
        # Добавляем последний товар
        if current_product:
            products_gs.append({
                'name': current_product,
                'start': product_start,
                'end': row_num
            })
        
        return products_gs
        
    except Exception as e:
        return None


def create_ranges_for_db_products(products_gs, products_db):
    """
    Создать диапазоны для товаров в БД на основе Google Sheets
    
    Учитывает что парсер мог объединить товары с одинаковыми названиями
    """
    # Группируем товары из Sheets по названиям
    sheets_by_name = {}
    for prod in products_gs:
        name = prod['name'].lower().strip()
        if name not in sheets_by_name:
            sheets_by_name[name] = []
        sheets_by_name[name].append(prod)
    
    # Создаем диапазоны для товаров из БД
    ranges = []
    
    for prod_id, prod_name in products_db:
        name_lower = prod_name.lower().strip()
        
        # Ищем соответствующие товары в Sheets
        matching = sheets_by_name.get(name_lower, [])
        
        if matching:
            # Если парсер объединил несколько товаров - берем весь диапазон
            start = min(p['start'] for p in matching)
            end = max(p['end'] for p in matching)
            ranges.append((prod_id, start, end, prod_name))
        else:
            # Товар не найден в Sheets - пропускаем
            pass
    
    return ranges


def process_project(project_id, table_id):
    """Обработать один проект"""
    db = PostgreSQLManager()
    results = {
        'sheets_analyzed': False,
        'products_in_sheets': 0,
        'ranges_created': 0,
        'duplicates_deleted': 0,
        'images_relinked': 0,
        'main_assigned': 0,
        'images_after': 0,
        'errors': []
    }
    
    try:
        # 1. Анализ Google Sheets
        products_gs = analyze_google_sheets(table_id)
        
        if products_gs is None:
            results['errors'].append("Не удалось загрузить Google Sheets")
            return results
        
        results['sheets_analyzed'] = True
        results['products_in_sheets'] = len(products_gs)
        
        # Небольшая задержка чтобы не перегружать Google API
        time.sleep(1.5)
        
        with db.get_session() as session:
            # Получаем товары из БД
            products_db = session.execute(
                text("""
                    SELECT id, name
                    FROM products
                    WHERE project_id = :pid
                    ORDER BY id
                """),
                {'pid': project_id}
            ).fetchall()
            
            # 2. Создаем диапазоны для товаров из БД
            ranges = create_ranges_for_db_products(products_gs, products_db)
            results['ranges_created'] = len(ranges)
            
            # 3. Удаление дубликатов по image_url
            duplicates = session.execute(
                text("""
                    SELECT 
                        image_url,
                        STRING_AGG(CAST(id AS TEXT), ',' ORDER BY id) as ids
                    FROM product_images
                    WHERE product_id IN (SELECT id FROM products WHERE project_id = :pid)
                    GROUP BY image_url
                    HAVING COUNT(*) > 1
                """),
                {'pid': project_id}
            ).fetchall()
            
            for url, ids_str in duplicates:
                id_list = [int(x) for x in ids_str.split(',')]
                keep_id = id_list[0]
                delete_ids = id_list[1:]
                
                session.execute(
                    text("DELETE FROM product_images WHERE id = ANY(:ids)"),
                    {'ids': delete_ids}
                )
                results['duplicates_deleted'] += len(delete_ids)
            
            # 4. Перепривязка изображений по диапазонам
            if ranges:
                all_images = session.execute(
                    text("""
                        SELECT pi.id, pi.cell_position, pi.product_id
                        FROM product_images pi
                        WHERE pi.product_id IN (SELECT id FROM products WHERE project_id = :pid)
                    """),
                    {'pid': project_id}
                ).fetchall()
                
                for img_id, cell_position, current_prod_id in all_images:
                    # Извлекаем номер строки
                    try:
                        row_num = int(''.join(filter(str.isdigit, cell_position)))
                    except:
                        continue
                    
                    # Находим правильный товар
                    correct_prod_id = None
                    for prod_id, start, end, note in ranges:
                        if start <= row_num <= end:
                            correct_prod_id = prod_id
                            break
                    
                    if correct_prod_id and current_prod_id != correct_prod_id:
                        session.execute(
                            text("""
                                UPDATE product_images
                                SET product_id = :new_prod_id
                                WHERE id = :img_id
                            """),
                            {'img_id': img_id, 'new_prod_id': correct_prod_id}
                        )
                        results['images_relinked'] += 1
            
            # 5. Назначение главных из столбца A
            session.execute(
                text("""
                    UPDATE product_images
                    SET is_main_image = 'false'
                    WHERE product_id IN (SELECT id FROM products WHERE project_id = :pid)
                """),
                {'pid': project_id}
            )
            
            result = session.execute(
                text("""
                    UPDATE product_images
                    SET is_main_image = 'true'
                    WHERE product_id IN (SELECT id FROM products WHERE project_id = :pid)
                      AND cell_position LIKE 'A%'
                """),
                {'pid': project_id}
            )
            results['main_assigned'] = result.rowcount
            
            # 6. Для товаров без главных - назначаем первое
            no_main = session.execute(
                text("""
                    SELECT p.id
                    FROM products p
                    WHERE p.project_id = :pid
                      AND EXISTS (SELECT 1 FROM product_images pi WHERE pi.product_id = p.id)
                      AND NOT EXISTS (
                          SELECT 1 FROM product_images pi2 
                          WHERE pi2.product_id = p.id AND pi2.is_main_image::text = 'true'
                      )
                """),
                {'pid': project_id}
            ).fetchall()
            
            for (prod_id,) in no_main:
                first_img = session.execute(
                    text("""
                        SELECT id
                        FROM product_images
                        WHERE product_id = :prod_id
                        ORDER BY cell_position
                        LIMIT 1
                    """),
                    {'prod_id': prod_id}
                ).fetchone()
                
                if first_img:
                    session.execute(
                        text("UPDATE product_images SET is_main_image = 'true' WHERE id = :img_id"),
                        {'img_id': first_img[0]}
                    )
                    results['main_assigned'] += 1
            
            # Подсчитываем итоговое количество изображений
            img_count = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM product_images pi
                    WHERE pi.product_id IN (SELECT id FROM products WHERE project_id = :pid)
                """),
                {'pid': project_id}
            ).scalar()
            results['images_after'] = img_count
            
            session.commit()
        
    except Exception as e:
        results['errors'].append(str(e))
    
    return results


def main(batch_num=1):
    """Главная функция"""
    print("\n" + "="*80)
    print(f"🔧 МАССОВАЯ ОБРАБОТКА ПРОЕКТОВ (С GOOGLE SHEETS) - БАТЧ #{batch_num}")
    print("="*80 + "\n")
    
    # Получаем проекты для обработки
    projects = get_projects_for_processing(batch_num=batch_num, batch_size=20)
    
    if not projects:
        print("✅ Проекты для обработки не найдены!")
        return
    
    print(f"📊 Проектов в батче: {len(projects)}\n")
    
    print("ID    | Товаров | Изобр | Дублей")
    print("-"*80)
    for p in projects:
        print(f"{p['id']:5} | {p['products']:7} | {p['images']:5} | {p['duplicates']:6}")
    
    print("\n" + "="*80)
    print("🚀 НАЧАЛО ОБРАБОТКИ")
    print("="*80 + "\n")
    
    total_dupes_deleted = 0
    total_relinked = 0
    total_main_assigned = 0
    errors_count = 0
    
    for idx, project in enumerate(projects, 1):
        proj_id = project['id']
        table_id = project['table_id']
        
        print(f"{idx:2}/20 | #{proj_id:5} | ", end='', flush=True)
        
        results = process_project(proj_id, table_id)
        
        if results['errors']:
            print(f"❌ {results['errors'][0][:60]}")
            errors_count += 1
        else:
            print(f"✅ Sheets:{results['products_in_sheets']:2} | "
                  f"Дубл:{results['duplicates_deleted']:3} | "
                  f"Перепривяз:{results['images_relinked']:3} | "
                  f"Главн:{results['main_assigned']:2} | "
                  f"Осталось:{results['images_after']:3}")
            
            total_dupes_deleted += results['duplicates_deleted']
            total_relinked += results['images_relinked']
            total_main_assigned += results['main_assigned']
    
    print("\n" + "="*80)
    print("📊 ИТОГИ БАТЧА:")
    print("="*80)
    print(f"  Обработано проектов: {len(projects)}")
    print(f"  Удалено дубликатов: {total_dupes_deleted:,}")
    print(f"  Перепривязано изображений: {total_relinked:,}")
    print(f"  Назначено главных: {total_main_assigned:,}")
    print(f"  Ошибок: {errors_count}")
    
    print("\n💡 Для следующего батча запусти:")
    print(f"   python3 batch_fix_projects_full.py {batch_num + 1}")
    print("="*80 + "\n")


if __name__ == "__main__":
    batch_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    main(batch_number)

