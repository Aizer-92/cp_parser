#!/usr/bin/env python3
"""
Массовая обработка проектов батчами:
- Удаление дубликатов изображений
- Назначение главных изображений из столбца A

БЕЗ перепривязки изображений (так как нет row_number)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text


def get_projects_for_processing(batch_num=1, batch_size=20):
    """Получить список проектов для обработки"""
    db = PostgreSQLManager()
    
    with db.get_session() as session:
        projects = session.execute(
            text("""
                SELECT 
                    proj.id as project_id,
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
                GROUP BY proj.id
                HAVING COUNT(DISTINCT p.id) > 0
                ORDER BY (COUNT(pi.id) - COUNT(DISTINCT pi.image_url)) DESC, proj.id
                LIMIT :limit OFFSET :offset
            """),
            {'limit': batch_size, 'offset': (batch_num - 1) * batch_size}
        ).fetchall()
        
        return [
            {
                'id': p[0],
                'products': p[1],
                'images': p[2],
                'unique': p[3],
                'duplicates': p[2] - p[3]
            }
            for p in projects
        ]


def process_project(project_id):
    """Обработать один проект"""
    db = PostgreSQLManager()
    results = {
        'duplicates_deleted': 0,
        'main_assigned': 0,
        'images_after': 0,
        'errors': []
    }
    
    with db.get_session() as session:
        try:
            # 1. Удаление дубликатов по image_url
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
            
            # 2. Назначение главных из столбца A
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
            
            # 3. Для товаров без главных - назначаем первое
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
            session.rollback()
    
    return results


def main(batch_num=1):
    """Главная функция"""
    print("\n" + "="*80)
    print(f"🔧 МАССОВАЯ ОБРАБОТКА ПРОЕКТОВ - БАТЧ #{batch_num}")
    print("="*80 + "\n")
    
    # Получаем проекты для обработки
    projects = get_projects_for_processing(batch_num=batch_num, batch_size=20)
    
    if not projects:
        print("✅ Проекты для обработки не найдены!")
        return
    
    print(f"📊 Проектов в батче: {len(projects)}\n")
    
    print("ID    | Товаров | Изобр | Уникал | Дублей")
    print("-"*80)
    for p in projects:
        print(f"{p['id']:5} | {p['products']:7} | {p['images']:5} | {p['unique']:6} | {p['duplicates']:6}")
    
    print("\n" + "="*80)
    print("🚀 НАЧАЛО ОБРАБОТКИ")
    print("="*80 + "\n")
    
    total_dupes_deleted = 0
    total_main_assigned = 0
    errors_count = 0
    
    for idx, project in enumerate(projects, 1):
        proj_id = project['id']
        print(f"{idx:2}/20 | Проект #{proj_id:5} | ", end='', flush=True)
        
        results = process_project(proj_id)
        
        if results['errors']:
            print(f"❌ ОШИБКА: {results['errors'][0][:50]}")
            errors_count += 1
        else:
            print(f"✅ Дублей удалено: {results['duplicates_deleted']:3} | "
                  f"Главных назначено: {results['main_assigned']:2} | "
                  f"Осталось изображений: {results['images_after']:3}")
            
            total_dupes_deleted += results['duplicates_deleted']
            total_main_assigned += results['main_assigned']
    
    print("\n" + "="*80)
    print("📊 ИТОГИ БАТЧА:")
    print("="*80)
    print(f"  Обработано проектов: {len(projects)}")
    print(f"  Удалено дубликатов: {total_dupes_deleted:,}")
    print(f"  Назначено главных: {total_main_assigned:,}")
    print(f"  Ошибок: {errors_count}")
    
    print("\n💡 Для следующего батча запусти:")
    print(f"   python3 batch_fix_projects.py {batch_num + 1}")
    print("="*80 + "\n")


if __name__ == "__main__":
    batch_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    main(batch_number)

