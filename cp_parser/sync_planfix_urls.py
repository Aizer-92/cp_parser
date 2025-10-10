#!/usr/bin/env python3
"""
Синхронизация ссылок на задачи Planfix из мастер-таблицы
"""

import sys
import csv
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# Путь к CSV файлу
CSV_PATH = "/Users/bakirovresad/Downloads/Reshad 1/projects/Копилка Презентаций - Просчеты  (1).csv"

def main():
    print("=" * 80)
    print("🔄 СИНХРОНИЗАЦИЯ PLANFIX URLs")
    print("=" * 80)
    
    db = PostgreSQLManager()
    
    # Читаем CSV
    print("\n📖 Читаем CSV файл...")
    mappings = []  # [(google_sheets_url, planfix_url), ...]
    
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                google_url = row.get('Ссылка на GoogleSheets', '').strip()
                planfix_url = row.get('URL', '').strip()
                
                if google_url and planfix_url:
                    # Извлекаем ID из Google Sheets URL
                    if '/d/' in google_url:
                        table_id = google_url.split('/d/')[1].split('/')[0]
                        mappings.append((table_id, planfix_url))
        
        print(f"✅ Найдено {len(mappings)} записей с ссылками")
    except Exception as e:
        print(f"❌ Ошибка чтения CSV: {e}")
        return
    
    # Обновляем БД
    print("\n🔄 Обновляем базу данных...")
    updated = 0
    not_found = 0
    
    with db.get_session() as session:
        for table_id, planfix_url in mappings:
            # Проверяем есть ли проект с таким table_id
            result = session.execute(text("""
                UPDATE projects 
                SET planfix_task_url = :url 
                WHERE table_id = :table_id
                RETURNING id, project_name
            """), {'url': planfix_url, 'table_id': table_id}).first()
            
            if result:
                updated += 1
                if updated <= 5:  # Показываем первые 5
                    print(f"  ✅ {result.project_name[:60]}")
            else:
                not_found += 1
        
        session.commit()
    
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"  ✅ Обновлено: {updated}")
    print(f"  ⚠️  Не найдено в БД: {not_found}")
    print(f"  📝 Всего в CSV: {len(mappings)}")
    
    # Проверяем сколько проектов теперь имеют Planfix URL
    with db.get_session() as session:
        total_projects = session.execute(text("SELECT COUNT(*) FROM projects")).scalar()
        with_planfix = session.execute(text("""
            SELECT COUNT(*) FROM projects WHERE planfix_task_url IS NOT NULL
        """)).scalar()
        
        print(f"\n📌 ИТОГО В БД:")
        print(f"  Всего проектов: {total_projects}")
        print(f"  С Planfix URL: {with_planfix} ({with_planfix*100//total_projects}%)")
    
    print("=" * 80)

if __name__ == "__main__":
    main()

