#!/usr/bin/env python3
"""
Railway PostgreSQL Database Helper
Утилита для прямого подключения к PostgreSQL на Railway

⚠️ ВАЖНО: Перед использованием установите переменные окружения:
export RAILWAY_DB_HOST="gondola.proxy.rlwy.net"
export RAILWAY_DB_PORT="13805"
export RAILWAY_DB_USER="postgres"
export RAILWAY_DB_PASSWORD="your_password_here"
export RAILWAY_DB_NAME="railway"

Или используйте файл .env (не коммитить в Git!)
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

# Railway PostgreSQL Connection (из переменных окружения)
RAILWAY_CONFIG = {
    'host': os.getenv('RAILWAY_DB_HOST', 'gondola.proxy.rlwy.net'),
    'port': int(os.getenv('RAILWAY_DB_PORT', '13805')),
    'user': os.getenv('RAILWAY_DB_USER', 'postgres'),
    'password': os.getenv('RAILWAY_DB_PASSWORD', ''),  # ОБЯЗАТЕЛЬНО установить!
    'database': os.getenv('RAILWAY_DB_NAME', 'railway')
}

def get_railway_connection():
    """Создает подключение к Railway PostgreSQL"""
    # Проверяем наличие пароля
    if not RAILWAY_CONFIG['password']:
        print("❌ ОШИБКА: Не установлен пароль для Railway PostgreSQL!")
        print("   Установите переменную окружения: export RAILWAY_DB_PASSWORD='your_password'")
        return None
    
    try:
        conn = psycopg2.connect(**RAILWAY_CONFIG)
        print("✅ Подключение к Railway PostgreSQL установлено")
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к Railway PostgreSQL: {e}")
        return None

def execute_query(query, params=None, fetch=True):
    """
    Выполняет SQL запрос к Railway БД
    
    Args:
        query: SQL запрос
        params: Параметры для запроса (опционально)
        fetch: Возвращать результаты (True) или только выполнить (False)
    
    Returns:
        Результаты запроса или None
    """
    conn = get_railway_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        
        if fetch:
            results = cursor.fetchall()
            conn.close()
            return results
        else:
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            print(f"✅ Выполнено. Затронуто строк: {affected_rows}")
            return affected_rows
    except Exception as e:
        print(f"❌ Ошибка выполнения запроса: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None

def add_new_category_to_railway():
    """Добавляет категорию 'Новая категория' в Railway PostgreSQL"""
    print("🔄 Добавление категории 'Новая категория' в Railway PostgreSQL...")
    
    # Проверяем, есть ли уже такая категория
    check_query = "SELECT * FROM categories WHERE category = %s"
    existing = execute_query(check_query, ('Новая категория',))
    
    if existing and len(existing) > 0:
        print("✅ Категория 'Новая категория' уже существует в Railway")
        print(f"   ID: {existing[0]['id']}, Category: {existing[0]['category']}")
        return
    
    # Данные категории
    category_data = {
        'tn_ved_code': '',
        'duty_rate': '0%',
        'vat_rate': '20%',
        'certificates': [],
        'description': 'Для товаров, не распознанных автоматически. Требует ручного ввода пошлин.'
    }
    
    # Добавляем новую категорию
    insert_query = """
        INSERT INTO categories (category, material, data)
        VALUES (%s, %s, %s)
        RETURNING id, category
    """
    
    result = execute_query(
        insert_query,
        ('Новая категория', '', json.dumps(category_data, ensure_ascii=False)),
        fetch=False
    )
    
    if result:
        print("✅ Категория 'Новая категория' добавлена в Railway PostgreSQL")
        
        # Проверяем
        check_result = execute_query(check_query, ('Новая категория',))
        if check_result:
            data = check_result[0]['data']
            # Если data уже dict (PostgreSQL с RealDictCursor), используем как есть
            # Если data строка, парсим JSON
            if isinstance(data, str):
                data = json.loads(data)
            print(f"   ID: {check_result[0]['id']}, Category: {check_result[0]['category']}")
            print(f"   Duty: {data.get('duty_rate', 'N/A')}, VAT: {data.get('vat_rate', 'N/A')}")

def list_categories():
    """Выводит список всех категорий из Railway PostgreSQL"""
    print("📋 Список категорий в Railway PostgreSQL:")
    
    query = "SELECT id, category, material FROM categories ORDER BY id"
    results = execute_query(query)
    
    if results:
        print(f"\nВсего категорий: {len(results)}\n")
        for row in results:
            print(f"  {row['id']:3d}. {row['category']}")
            if row['material']:
                print(f"       └─ {row['material']}")
    else:
        print("❌ Не удалось получить список категорий")

def get_category(category_name):
    """Получает данные категории по имени"""
    print(f"🔍 Поиск категории: {category_name}")
    
    query = "SELECT * FROM categories WHERE category = %s"
    results = execute_query(query, (category_name,))
    
    if results and len(results) > 0:
        row = results[0]
        print(f"\n✅ Найдена категория:")
        print(f"   ID: {row['id']}")
        print(f"   Category: {row['category']}")
        print(f"   Material: {row['material']}")
        
        if row['data']:
            data = row['data']
            if isinstance(data, str):
                data = json.loads(data)
            print(f"\n   Data:")
            for key, value in data.items():
                print(f"     {key}: {value}")
        
        return row
    else:
        print(f"❌ Категория '{category_name}' не найдена")
        return None

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("""
Railway PostgreSQL Helper - Утилита для работы с БД на Railway

Использование:
    python3 railway_db.py add_new_category    # Добавить "Новая категория"
    python3 railway_db.py list                # Список всех категорий
    python3 railway_db.py get "категория"     # Получить данные категории
    python3 railway_db.py test                # Тест подключения

Примеры:
    python3 railway_db.py add_new_category
    python3 railway_db.py list
    python3 railway_db.py get "кружки"
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'test':
        conn = get_railway_connection()
        if conn:
            print("✅ Подключение успешно!")
            conn.close()
        else:
            print("❌ Подключение не удалось!")
    
    elif command == 'add_new_category':
        add_new_category_to_railway()
    
    elif command == 'list':
        list_categories()
    
    elif command == 'get':
        if len(sys.argv) < 3:
            print("❌ Укажите название категории")
            sys.exit(1)
        get_category(sys.argv[2])
    
    else:
        print(f"❌ Неизвестная команда: {command}")
        sys.exit(1)

