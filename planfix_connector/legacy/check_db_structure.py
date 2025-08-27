#!/usr/bin/env python3
"""
Детальный анализ структуры базы данных Planfix Connector
"""

import sqlite3
import os

def analyze_database():
    """Детальный анализ базы данных"""
    
    db_path = 'output/planfix_tasks_correct.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Детальный анализ базы данных...")
        print(f"📁 Файл: {db_path}")
        
        # Получаем размер файла
        file_size = os.path.getsize(db_path)
        print(f"📏 Размер: {file_size / (1024*1024):.2f} MB")
        
        # Список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n🗄️ Все таблицы ({len(tables)}):")
        for table in tables:
            table_name = table[0]
            print(f"  📋 {table_name}")
            
            # Структура таблицы
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"    Структура:")
                for col in columns:
                    col_id, col_name, col_type, not_null, default_val, pk = col
                    pk_mark = " 🔑" if pk else ""
                    print(f"      - {col_name}: {col_type}{pk_mark}")
                
                # Количество записей
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"    📊 Записей: {count}")
                
                # Пример данных (первые 3 записи)
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    print(f"    📝 Пример данных:")
                    for i, row in enumerate(sample_data, 1):
                        print(f"      {i}. {row[:3]}...")  # Показываем первые 3 поля
                
                print()
                
            except Exception as e:
                print(f"    ❌ Ошибка анализа: {e}")
        
        # Анализ таблицы tasks
        print("🎯 Детальный анализ таблицы tasks:")
        try:
            # Статусы задач
            cursor.execute("SELECT status_id, COUNT(*) FROM tasks GROUP BY status_id ORDER BY COUNT(*) DESC")
            statuses = cursor.fetchall()
            print(f"  📊 Статусы задач:")
            for status_id, count in statuses:
                print(f"    - Статус {status_id}: {count} задач")
            
            # Приоритеты задач
            cursor.execute("SELECT priority, COUNT(*) FROM tasks GROUP BY priority ORDER BY COUNT(*) DESC")
            priorities = cursor.fetchall()
            print(f"  ⚡ Приоритеты задач:")
            for priority, count in priorities:
                print(f"    - Приоритет {priority}: {count} задач")
            
            # Постановщики задач
            cursor.execute("SELECT owner_id, COUNT(*) FROM tasks GROUP BY owner_id ORDER BY COUNT(*) DESC LIMIT 5")
            owners = cursor.fetchall()
            print(f"  👤 Топ постановщиков:")
            for owner_id, count in owners:
                print(f"    - ID {owner_id}: {count} задач")
            
            # Проекты задач
            cursor.execute("SELECT project_id, COUNT(*) FROM tasks GROUP BY project_id ORDER BY COUNT(*) DESC LIMIT 5")
            projects = cursor.fetchall()
            print(f"  🏗️ Топ проектов:")
            for project_id, count in projects:
                print(f"    - ID {project_id}: {count} задач")
                
        except Exception as e:
            print(f"  ❌ Ошибка анализа tasks: {e}")
        
        # Анализ custom_field_values
        print("\n🎯 Анализ кастомных полей:")
        try:
            cursor.execute("SELECT * FROM custom_field_values LIMIT 5")
            cf_values = cursor.fetchall()
            if cf_values:
                print(f"  📊 Найдено значений: {len(cf_values)}")
                for i, row in enumerate(cf_values, 1):
                    print(f"    {i}. {row}")
            else:
                print("  ⚠️ Таблица custom_field_values пуста")
        except Exception as e:
            print(f"  ❌ Ошибка анализа кастомных полей: {e}")
        
        conn.close()
        print("\n✅ Анализ базы данных завершен")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе базы данных: {e}")

if __name__ == "__main__":
    analyze_database()
