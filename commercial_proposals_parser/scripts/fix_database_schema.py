#!/usr/bin/env python3
"""
Скрипт для исправления схемы базы данных - изменение типа поля characteristics
"""

import sqlite3

def fix_database_schema():
    """Исправление схемы базы данных"""
    conn = sqlite3.connect('commercial_proposals_v4.db')
    cursor = conn.cursor()
    
    try:
        # Создаем новую таблицу с правильной схемой
        cursor.execute('''
            CREATE TABLE products_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(300) NOT NULL,
                description TEXT,
                characteristics TEXT,
                custom_design VARCHAR(200),
                sheet_id INTEGER NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (sheet_id) REFERENCES sheets_metadata (id)
            )
        ''')
        
        # Копируем данные из старой таблицы
        cursor.execute('''
            INSERT INTO products_new (id, name, description, characteristics, custom_design, sheet_id, created_at, updated_at)
            SELECT id, name, description, characteristics, custom_design, sheet_id, created_at, updated_at
            FROM products
        ''')
        
        # Удаляем старую таблицу
        cursor.execute('DROP TABLE products')
        
        # Переименовываем новую таблицу
        cursor.execute('ALTER TABLE products_new RENAME TO products')
        
        conn.commit()
        print("✅ Схема базы данных исправлена!")
        
    finally:
        conn.close()

def main():
    print("🔄 Исправление схемы базы данных...")
    fix_database_schema()
    
    # Проверяем результат
    conn = sqlite3.connect('commercial_proposals_v4.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('PRAGMA table_info(products)')
        columns = cursor.fetchall()
        
        print(f"\n📊 Структура таблицы products:")
        for col in columns:
            print(f"  {col[1]} - {col[2]}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
