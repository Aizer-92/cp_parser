#!/usr/bin/env python3
"""
Очистка локальных файлов Шаблона 5 после успешной загрузки на FTP
"""

import sys
from pathlib import Path
from sqlalchemy import text
import os

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

def main():
    db = PostgreSQLManager()
    
    print("=" * 80)
    print("🧹 ОЧИСТКА ЛОКАЛЬНЫХ ФАЙЛОВ ШАБЛОНА 5")
    print("=" * 80)
    
    # Загружаем список проектов Шаблона 5
    with open('template_5_candidate_ids.txt', 'r') as f:
        template5_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print(f"\n📋 Проектов Шаблона 5: {len(template5_ids)}")
    
    with db.get_session() as session:
        # Проверяем что все изображения загружены
        images_without_url = session.execute(text("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(:ids)
            AND (pi.image_url IS NULL OR pi.image_url = '')
        """), {'ids': template5_ids}).scalar()
        
        if images_without_url > 0:
            print(f"\n⚠️  ВНИМАНИЕ: {images_without_url} изображений еще не загружены!")
            print(f"⚠️  Рекомендуется дождаться завершения загрузки.")
            response = input("\nПродолжить очистку? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Очистка отменена")
                return
        
        # Получаем все table_id и local_path для Шаблона 5
        results = session.execute(text("""
            SELECT DISTINCT pr.table_id, pi.local_path
            FROM projects pr
            JOIN products p ON pr.id = p.project_id
            LEFT JOIN product_images pi ON p.id = pi.product_id
            WHERE pr.id = ANY(:ids)
        """), {'ids': template5_ids}).fetchall()
        
        table_ids = set()
        image_paths = set()
        
        for table_id, local_path in results:
            if table_id:
                table_ids.add(table_id)
            if local_path:
                image_paths.add(local_path)
        
        print(f"\n📊 Найдено:")
        print(f"  • Excel файлов: {len(table_ids)}")
        print(f"  • Изображений: {len(image_paths)}")
        
        # Удаляем Excel файлы
        print(f"\n🗑️  Удаление Excel файлов...")
        excel_dir = Path('storage/excel_files')
        deleted_excel = 0
        not_found_excel = 0
        
        # Получаем все Excel файлы Шаблона 5 по проектным ID
        for proj_id in template5_ids:
            # Ищем файлы с паттерном project_{proj_id}_*.xlsx
            excel_files = list(excel_dir.glob(f"project_{proj_id}_*.xlsx")) + list(excel_dir.glob(f"project_{proj_id}_*.xls"))
            
            if excel_files:
                for excel_path in excel_files:
                    try:
                        os.remove(excel_path)
                        deleted_excel += 1
                        if deleted_excel % 50 == 0:
                            print(f"  ✅ Удалено: {deleted_excel}")
                    except Exception as e:
                        print(f"  ❌ Ошибка удаления {excel_path.name}: {e}")
            else:
                not_found_excel += 1
        
        print(f"\n  ✅ Удалено Excel: {deleted_excel}")
        print(f"  ⚠️  Не найдено: {not_found_excel}")
        
        # Удаляем изображения
        print(f"\n🗑️  Удаление изображений...")
        deleted_images = 0
        not_found_images = 0
        
        for local_path in image_paths:
            if local_path and local_path.strip():
                img_path = Path(local_path)
                if img_path.exists():
                    try:
                        os.remove(img_path)
                        deleted_images += 1
                        if deleted_images % 500 == 0:
                            print(f"  ✅ Удалено: {deleted_images}/{len(image_paths)}")
                    except Exception as e:
                        print(f"  ❌ Ошибка удаления {img_path.name}: {e}")
                else:
                    not_found_images += 1
        
        print(f"\n  ✅ Удалено изображений: {deleted_images}")
        print(f"  ⚠️  Не найдено: {not_found_images}")
        
        # Проверяем освобожденное место
        print(f"\n📊 Статистика:")
        
        # Считаем оставшиеся файлы
        remaining_excel = len(list(excel_dir.glob('*.xlsx')))
        
        images_dir = Path('storage/images')
        if images_dir.exists():
            remaining_images = len(list(images_dir.glob('*.*')))
        else:
            remaining_images = 0
        
        print(f"  • Осталось Excel файлов: {remaining_excel}")
        print(f"  • Осталось изображений: {remaining_images}")
        
        print("\n" + "=" * 80)
        print("✅ ОЧИСТКА ЗАВЕРШЕНА")
        print("=" * 80)

if __name__ == '__main__':
    main()

