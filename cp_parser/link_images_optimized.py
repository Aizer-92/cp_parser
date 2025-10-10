#!/usr/bin/env python3
"""
Оптимизированный скрипт для привязки изображений к товарам БЕЗ изображений
Использует облачные URL и работает только с непривязанными изображениями
"""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# Облачный URL для изображений
FTP_BASE_URL = "https://ru1.storage.beget.cloud/creonproject/images/"

def extract_row_from_filename(filename, table_id):
    """
    Извлекает номер строки из имени файла
    Формат: table_id_COLUMNROW_timestamp.ext
    Например: 1xAPdmVpr..._A10_278785378.png -> row 10
    """
    # Убираем table_id из начала
    pattern = f"{table_id}_([A-Z]+)([0-9]+)_"
    match = re.search(pattern, filename)
    if match:
        col_letter = match.group(1)
        row_num = int(match.group(2))
        return row_num, col_letter
    return None, None

def main():
    db = PostgreSQLManager()
    
    # Читаем список проблемных проектов
    with open('projects_need_images.txt', 'r') as f:
        project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print("=" * 80)
    print("🔗 ПРИВЯЗКА ИЗОБРАЖЕНИЙ К ТОВАРАМ (ОПТИМИЗИРОВАННАЯ)")
    print("=" * 80)
    
    # ЭТАП 1: Удаление дубликатов товаров
    print("\n📋 ЭТАП 1: Удаление дубликатов товаров...")
    
    with db.get_session() as session:
        # Находим ID дубликатов которые нужно удалить
        duplicates = session.execute(text("""
            WITH ranked AS (
                SELECT 
                    p.id,
                    p.table_id,
                    p.row_number,
                    p.created_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.table_id, p.row_number 
                        ORDER BY p.created_at DESC
                    ) as rn
                FROM products p
                JOIN projects proj ON proj.table_id = p.table_id
                WHERE proj.id = ANY(:ids)
            )
            SELECT id FROM ranked WHERE rn > 1
        """), {'ids': project_ids}).fetchall()
        
        to_delete_ids = [row.id for row in duplicates]
        
        if to_delete_ids:
            print(f"  Найдено дубликатов: {len(to_delete_ids)}")
            
            # Удаляем изображения дубликатов
            session.execute(text("""
                DELETE FROM product_images
                WHERE product_id = ANY(:ids)
            """), {'ids': to_delete_ids})
            
            # Удаляем ценовые предложения дубликатов
            session.execute(text("""
                DELETE FROM price_offers
                WHERE product_id = ANY(:ids)
            """), {'ids': to_delete_ids})
            
            # Удаляем сами товары-дубликаты
            result = session.execute(text("""
                DELETE FROM products
                WHERE id = ANY(:ids)
            """), {'ids': to_delete_ids})
            
            session.commit()
            print(f"  ✅ Удалено: {result.rowcount} товаров-дубликатов")
        else:
            print(f"  ✅ Дубликатов не найдено")
    
    # ЭТАП 2: Получаем товары БЕЗ изображений
    print("\n🖼️  ЭТАП 2: Анализ товаров БЕЗ изображений...")
    
    with db.get_session() as session:
        products_without_images = session.execute(text("""
            SELECT 
                p.id as product_id,
                p.table_id,
                p.row_number,
                p.name
            FROM products p
            JOIN projects proj ON proj.table_id = p.table_id
            LEFT JOIN product_images pi ON pi.product_id = p.id
            WHERE proj.id = ANY(:ids)
            AND pi.id IS NULL
            ORDER BY p.table_id, p.row_number
        """), {'ids': project_ids}).fetchall()
        
        print(f"  Товаров БЕЗ изображений: {len(products_without_images):,}")
        
        if not products_without_images:
            print("\n✅ Все товары уже имеют изображения!")
            return
        
        # Получаем список уже привязанных изображений
        used_filenames = session.execute(text("""
            SELECT DISTINCT image_filename
            FROM product_images
        """)).fetchall()
        
        used_filenames_set = {row.image_filename for row in used_filenames}
        print(f"  Уже привязано изображений: {len(used_filenames_set):,}")
        
        # Создаем карту: (table_id, row_number) -> product_id
        product_map = {}
        needed_table_ids = set()
        
        for prod in products_without_images:
            key = (prod.table_id, prod.row_number)
            product_map[key] = prod.product_id
            needed_table_ids.add(prod.table_id)
        
        print(f"  Уникальных table_id: {len(needed_table_ids)}")
    
    # ЭТАП 3: Поиск подходящих изображений
    print("\n📁 ЭТАП 3: Поиск изображений для привязки...")
    
    local_dir = Path('storage/images')
    if not local_dir.exists():
        print(f"  ❌ Папка {local_dir} не найдена!")
        return
    
    all_files = [f for f in local_dir.glob('*') if f.is_file()]
    print(f"  Всего файлов в папке: {len(all_files):,}")
    
    # Фильтруем файлы: только для нужных table_id и непривязанные
    candidate_files = []
    for file in all_files:
        filename = file.name
        
        # Пропускаем уже привязанные
        if filename in used_filenames_set:
            continue
        
        # Проверяем что файл относится к нужным table_id
        for table_id in needed_table_ids:
            if table_id in filename:
                candidate_files.append((file, table_id))
                break
    
    print(f"  Кандидатов для привязки: {len(candidate_files):,}")
    
    # ЭТАП 4: Привязка изображений
    print("\n🔗 ЭТАП 4: Привязка изображений...")
    
    with db.get_session() as session:
        linked = 0
        skipped_no_product = 0
        skipped_parse_error = 0
        errors = 0
        
        for i, (file, table_id) in enumerate(candidate_files, 1):
            if i % 500 == 0:
                print(f"    Обработано: {i:,}/{len(candidate_files):,} | Привязано: {linked:,}")
            
            filename = file.name
            
            # Извлекаем номер строки
            row_num, col_letter = extract_row_from_filename(filename, table_id)
            
            if not row_num or not col_letter:
                skipped_parse_error += 1
                continue
            
            # Находим товар БЕЗ изображений
            key = (table_id, row_num)
            product_id = product_map.get(key)
            
            if not product_id:
                skipped_no_product += 1
                continue
            
            # Добавляем изображение с ОБЛАЧНЫМ URL
            try:
                is_main = (col_letter == 'A')  # Колонка A = главное фото
                cloud_url = FTP_BASE_URL + filename
                
                session.execute(text("""
                    INSERT INTO product_images (
                        product_id, table_id, image_filename, image_url,
                        is_main_image, row_number, created_at, updated_at
                    )
                    VALUES (:pid, :tid, :fname, :url, :is_main, :row, NOW(), NOW())
                """), {
                    'pid': product_id,
                    'tid': table_id,
                    'fname': filename,
                    'url': cloud_url,
                    'is_main': is_main,
                    'row': row_num
                })
                linked += 1
                
                # После привязки убираем товар из карты чтобы не привязывать повторно
                if key in product_map:
                    del product_map[key]
                
                if linked % 500 == 0:
                    session.commit()
                    
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"    ❌ Ошибка: {str(e)[:80]}")
        
        session.commit()
        print(f"    Обработано: {len(candidate_files):,}/{len(candidate_files):,} | Привязано: {linked:,}")
    
    # ИТОГИ
    print("\n" + "=" * 80)
    print("📊 ИТОГИ:")
    print("=" * 80)
    print(f"✅ Привязано изображений:         {linked:,}")
    print(f"⏭️  Пропущено (нет товара):       {skipped_no_product:,}")
    print(f"⏭️  Пропущено (ошибка парсинга):  {skipped_parse_error:,}")
    print(f"❌ Ошибок:                        {errors:,}")
    
    # Финальная статистика
    with db.get_session() as session:
        stats = session.execute(text("""
            SELECT 
                COUNT(DISTINCT p.id) as total_products,
                COUNT(DISTINCT CASE WHEN pi.id IS NOT NULL THEN p.id END) as with_images,
                COUNT(DISTINCT CASE WHEN pi.id IS NULL THEN p.id END) as without_images,
                COUNT(pi.id) as total_images,
                COUNT(CASE WHEN pi.image_url LIKE 'https://%' THEN 1 END) as cloud_images
            FROM products p
            JOIN projects proj ON proj.table_id = p.table_id
            LEFT JOIN product_images pi ON pi.product_id = p.id
            WHERE proj.id = ANY(:ids)
        """), {'ids': project_ids}).first()
        
        print(f"\n📦 ТОВАРЫ (после обработки):")
        print(f"  Всего товаров:           {stats.total_products:,}")
        print(f"  ✅ С изображениями:       {stats.with_images:,} ({stats.with_images*100//stats.total_products}%)")
        print(f"  ❌ БЕЗ изображений:       {stats.without_images:,} ({stats.without_images*100//stats.total_products}%)")
        print(f"\n🖼️  ИЗОБРАЖЕНИЯ:")
        print(f"  Всего изображений:       {stats.total_images:,}")
        print(f"  ☁️  Облачные URL:          {stats.cloud_images:,}")
    
    print("=" * 80)

if __name__ == '__main__':
    main()

