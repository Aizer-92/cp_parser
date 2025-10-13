#!/usr/bin/env python3
"""
Скрипт инициализации БД для Railway
Запускается автоматически при деплое и добавляет необходимые колонки если их нет

Использование:
    python3 init_db.py
"""

import os
import sys

def init_database():
    """Инициализирует БД, добавляя необходимые колонки"""
    print("🔧 Инициализация БД...")
    
    try:
        from database import get_database_connection, close_database_connection
        
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        print(f"✅ Подключено к БД: {db_type}")
        
        if db_type == 'postgres':
            print("🐘 PostgreSQL: проверяем и добавляем колонки...")
            
            # Добавляем custom_logistics если нет
            try:
                cursor.execute("""
                    ALTER TABLE calculations 
                    ADD COLUMN IF NOT EXISTS custom_logistics JSONB
                """)
                print("✅ Колонка custom_logistics готова")
            except Exception as e:
                print(f"⚠️ custom_logistics: {e}")
                conn.rollback()
            
            # Добавляем forced_category если нет
            try:
                cursor.execute("""
                    ALTER TABLE calculations 
                    ADD COLUMN IF NOT EXISTS forced_category TEXT
                """)
                print("✅ Колонка forced_category готова")
            except Exception as e:
                print(f"⚠️ forced_category: {e}")
                conn.rollback()
            
            conn.commit()
            
        else:
            print("📦 SQLite: проверяем структуру таблицы...")
            cursor.execute("PRAGMA table_info(calculations)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'custom_logistics' not in columns:
                cursor.execute("ALTER TABLE calculations ADD COLUMN custom_logistics TEXT")
                print("✅ Добавлена колонка custom_logistics")
            else:
                print("✅ Колонка custom_logistics уже существует")
            
            if 'forced_category' not in columns:
                cursor.execute("ALTER TABLE calculations ADD COLUMN forced_category TEXT")
                print("✅ Добавлена колонка forced_category")
            else:
                print("✅ Колонка forced_category уже существует")
            
            conn.commit()
        
        cursor.close()
        close_database_connection()
        
        print("✅ Инициализация БД завершена успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)







