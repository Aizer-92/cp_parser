#!/usr/bin/env python3
"""
Миграция 001: Добавление полей custom_logistics и forced_category в таблицу calculations

Добавляет:
- custom_logistics: JSONB (PostgreSQL) / TEXT (SQLite) - хранит кастомные параметры логистики для каждого маршрута
- forced_category: TEXT - хранит категорию, выбранную пользователем вручную (например, "Новая категория")

Дата: 2025-10-10
"""

import os
import sys

# Добавляем корневую директорию в путь для импорта database.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_database_connection, close_database_connection

def run_migration():
    """Выполняет миграцию"""
    print("🔄 Начало миграции 001: добавление custom_logistics и forced_category")
    
    conn, db_type = get_database_connection()
    cursor = conn.cursor()
    
    try:
        if db_type == 'postgres':
            print("🐘 PostgreSQL: добавляем колонки...")
            
            # Пробуем добавить custom_logistics (если уже есть - получим ошибку и пропустим)
            try:
                print("   → Добавляем колонку custom_logistics...")
                cursor.execute("""
                    ALTER TABLE calculations 
                    ADD COLUMN custom_logistics JSONB
                """)
                conn.commit()
                print("✅ Добавлена колонка custom_logistics (JSONB)")
            except Exception as e:
                if 'already exists' in str(e) or 'duplicate column' in str(e).lower():
                    print("⚠️ Колонка custom_logistics уже существует")
                    conn.rollback()
                else:
                    raise
            
            # Пробуем добавить forced_category
            try:
                print("   → Добавляем колонку forced_category...")
                cursor.execute("""
                    ALTER TABLE calculations 
                    ADD COLUMN forced_category TEXT
                """)
                conn.commit()
                print("✅ Добавлена колонка forced_category (TEXT)")
            except Exception as e:
                if 'already exists' in str(e) or 'duplicate column' in str(e).lower():
                    print("⚠️ Колонка forced_category уже существует")
                    conn.rollback()
                else:
                    raise
                
        else:  # SQLite
            print("📦 SQLite: добавляем колонки...")
            
            # Проверяем структуру таблицы
            cursor.execute("PRAGMA table_info(calculations)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'custom_logistics' not in columns:
                cursor.execute("""
                    ALTER TABLE calculations 
                    ADD COLUMN custom_logistics TEXT
                """)
                print("✅ Добавлена колонка custom_logistics (TEXT)")
            else:
                print("⚠️ Колонка custom_logistics уже существует")
            
            if 'forced_category' not in columns:
                cursor.execute("""
                    ALTER TABLE calculations 
                    ADD COLUMN forced_category TEXT
                """)
                print("✅ Добавлена колонка forced_category (TEXT)")
            else:
                print("⚠️ Колонка forced_category уже существует")
        
        print("✅ Миграция 001 завершена успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        cursor.close()
        close_database_connection()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

