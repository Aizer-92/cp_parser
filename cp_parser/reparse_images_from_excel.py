#!/usr/bin/env python3
"""
Скрипт для парсинга изображений из уже скачанных Excel файлов
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_template_6 import Template6Parser
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

def reparse_images():
    """Парсит изображения из скачанных Excel файлов"""
    
    # Читаем список проектов
    with open('projects_need_images.txt', 'r') as f:
        project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print("=" * 80)
    print("🖼️  ПАРСИНГ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    print(f"\n📊 Проектов к обработке: {len(project_ids)}")
    
    parser = Template6Parser()
    db = PostgreSQLManager()
    
    excel_dir = Path('excel_files')
    
    # Найдем все скачанные файлы
    excel_files = {}
    for excel_path in excel_dir.glob('project_*.xlsx'):
        try:
            parts = excel_path.stem.split('_')
            if len(parts) >= 2:
                proj_id = int(parts[1])
                excel_files[proj_id] = excel_path
        except:
            continue
    
    print(f"📁 Найдено Excel файлов: {len(excel_files)}")
    
    # Фильтруем только те проекты что есть в списке
    to_process = [pid for pid in project_ids if pid in excel_files]
    not_found = [pid for pid in project_ids if pid not in excel_files]
    
    if not_found:
        print(f"\n⚠️  Не найдено файлов для {len(not_found)} проектов")
    
    print(f"\n✓ Будет обработано: {len(to_process)} проектов")
    
    success = 0
    errors = 0
    no_images = 0
    
    for i, proj_id in enumerate(to_process, 1):
        excel_path = excel_files[proj_id]
        print(f"\n[{i}/{len(to_process)}] Проект {proj_id} ({excel_path.name})...")
        
        try:
            # Получаем table_id
            with db.get_session() as session:
                table_id = session.execute(text("""
                    SELECT table_id FROM projects WHERE id = :id
                """), {'id': proj_id}).scalar()
                
                if not table_id:
                    print(f"  ❌ Нет table_id в БД")
                    errors += 1
                    continue
            
            # Проверяем сколько изображений уже есть
            with db.get_session() as session:
                before_count = session.execute(text("""
                    SELECT COUNT(*) 
                    FROM product_images pi
                    JOIN products p ON p.id = pi.product_id
                    WHERE p.table_id = :table_id
                """), {'table_id': table_id}).scalar()
            
            # Парсим только изображения для существующих товаров
            print(f"  🔄 Парсинг изображений... (уже было: {before_count})")
            try:
                parser.reparse_images_only(proj_id, str(excel_path))
                
                # Проверяем сколько добавилось
                with db.get_session() as session:
                    after_count = session.execute(text("""
                        SELECT COUNT(*) 
                        FROM product_images pi
                        JOIN products p ON p.id = pi.product_id
                        WHERE p.table_id = :table_id
                    """), {'table_id': table_id}).scalar()
                
                new_images = after_count - before_count
                
                if new_images == 0:
                    print(f"  ⚠️  Изображений не добавлено")
                    no_images += 1
                else:
                    print(f"  ✅ Добавлено {new_images} изображений (всего: {after_count})")
                    success += 1
                    
            except Exception as parse_err:
                print(f"  ❌ Ошибка парсинга: {str(parse_err)}")
                errors += 1
                continue
                
        except Exception as e:
            print(f"  ❌ Ошибка: {str(e)}")
            errors += 1
    
    # Итоги
    print("\n" + "=" * 80)
    print("📊 ИТОГИ ПАРСИНГА:")
    print("=" * 80)
    print(f"✅ Успешно:        {success} проектов")
    print(f"⚠️  Без изображений: {no_images} проектов")
    print(f"❌ Ошибок:         {errors} проектов")
    print("=" * 80)
    
    if success > 0:
        # Подсчитаем добавленные изображения
        with db.get_session() as session:
            new_images = session.execute(text("""
                SELECT COUNT(*) 
                FROM product_images 
                WHERE image_url LIKE 'storage/images/%'
            """)).scalar()
            
            print(f"\n🖼️  Всего изображений с локальными путями: {new_images}")
            print("\n✅ Изображения готовы к загрузке на FTP!")
            print("Следующий шаг: загрузить изображения на облако")

if __name__ == '__main__':
    reparse_images()


Скрипт для парсинга изображений из уже скачанных Excel файлов
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_template_6 import Template6Parser
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

def reparse_images():
    """Парсит изображения из скачанных Excel файлов"""
    
    # Читаем список проектов
    with open('projects_need_images.txt', 'r') as f:
        project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print("=" * 80)
    print("🖼️  ПАРСИНГ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    print(f"\n📊 Проектов к обработке: {len(project_ids)}")
    
    parser = Template6Parser()
    db = PostgreSQLManager()
    
    excel_dir = Path('excel_files')
    
    # Найдем все скачанные файлы
    excel_files = {}
    for excel_path in excel_dir.glob('project_*.xlsx'):
        try:
            parts = excel_path.stem.split('_')
            if len(parts) >= 2:
                proj_id = int(parts[1])
                excel_files[proj_id] = excel_path
        except:
            continue
    
    print(f"📁 Найдено Excel файлов: {len(excel_files)}")
    
    # Фильтруем только те проекты что есть в списке
    to_process = [pid for pid in project_ids if pid in excel_files]
    not_found = [pid for pid in project_ids if pid not in excel_files]
    
    if not_found:
        print(f"\n⚠️  Не найдено файлов для {len(not_found)} проектов")
    
    print(f"\n✓ Будет обработано: {len(to_process)} проектов")
    
    success = 0
    errors = 0
    no_images = 0
    
    for i, proj_id in enumerate(to_process, 1):
        excel_path = excel_files[proj_id]
        print(f"\n[{i}/{len(to_process)}] Проект {proj_id} ({excel_path.name})...")
        
        try:
            # Получаем table_id
            with db.get_session() as session:
                table_id = session.execute(text("""
                    SELECT table_id FROM projects WHERE id = :id
                """), {'id': proj_id}).scalar()
                
                if not table_id:
                    print(f"  ❌ Нет table_id в БД")
                    errors += 1
                    continue
            
            # Проверяем сколько изображений уже есть
            with db.get_session() as session:
                before_count = session.execute(text("""
                    SELECT COUNT(*) 
                    FROM product_images pi
                    JOIN products p ON p.id = pi.product_id
                    WHERE p.table_id = :table_id
                """), {'table_id': table_id}).scalar()
            
            # Парсим только изображения для существующих товаров
            print(f"  🔄 Парсинг изображений... (уже было: {before_count})")
            try:
                parser.reparse_images_only(proj_id, str(excel_path))
                
                # Проверяем сколько добавилось
                with db.get_session() as session:
                    after_count = session.execute(text("""
                        SELECT COUNT(*) 
                        FROM product_images pi
                        JOIN products p ON p.id = pi.product_id
                        WHERE p.table_id = :table_id
                    """), {'table_id': table_id}).scalar()
                
                new_images = after_count - before_count
                
                if new_images == 0:
                    print(f"  ⚠️  Изображений не добавлено")
                    no_images += 1
                else:
                    print(f"  ✅ Добавлено {new_images} изображений (всего: {after_count})")
                    success += 1
                    
            except Exception as parse_err:
                print(f"  ❌ Ошибка парсинга: {str(parse_err)}")
                errors += 1
                continue
                
        except Exception as e:
            print(f"  ❌ Ошибка: {str(e)}")
            errors += 1
    
    # Итоги
    print("\n" + "=" * 80)
    print("📊 ИТОГИ ПАРСИНГА:")
    print("=" * 80)
    print(f"✅ Успешно:        {success} проектов")
    print(f"⚠️  Без изображений: {no_images} проектов")
    print(f"❌ Ошибок:         {errors} проектов")
    print("=" * 80)
    
    if success > 0:
        # Подсчитаем добавленные изображения
        with db.get_session() as session:
            new_images = session.execute(text("""
                SELECT COUNT(*) 
                FROM product_images 
                WHERE image_url LIKE 'storage/images/%'
            """)).scalar()
            
            print(f"\n🖼️  Всего изображений с локальными путями: {new_images}")
            print("\n✅ Изображения готовы к загрузке на FTP!")
            print("Следующий шаг: загрузить изображения на облако")

if __name__ == '__main__':
    reparse_images()

