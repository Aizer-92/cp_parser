import os
import json
from typing import List, Dict, Any

# Универсальный модуль для работы с БД (PostgreSQL или SQLite)

def get_database_connection():
    """Возвращает подключение к БД (PostgreSQL или SQLite)"""
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    database_public_url = os.environ.get('DATABASE_PUBLIC_URL')
    
    if database_url or database_public_url:
        # PostgreSQL
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            # Пробуем сначала внутренний URL, потом публичный
            url_to_try = database_url or database_public_url
            print(f"🔗 Пробуем подключиться к PostgreSQL: {url_to_try[:50]}...")
            
            # Парсим URL
            parsed = urlparse(url_to_try)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],  # убираем ведущий /
                user=parsed.username,
                password=parsed.password,
                sslmode='require'
            )
            print("✅ Подключились к PostgreSQL")
            return conn, 'postgres'
        except Exception as e:
            print(f"❌ Ошибка подключения к PostgreSQL внутреннему: {e}")
            
            # Пробуем публичный URL если есть
            if database_public_url and database_public_url != url_to_try:
                try:
                    print(f"🔗 Пробуем публичный PostgreSQL URL...")
                    parsed = urlparse(database_public_url)
                    conn = psycopg2.connect(
                        host=parsed.hostname,
                        port=parsed.port,
                        database=parsed.path[1:],
                        user=parsed.username,
                        password=parsed.password,
                        sslmode='require'
                    )
                    print("✅ Подключились к PostgreSQL (публичный URL)")
                    return conn, 'postgres'
                except Exception as e2:
                    print(f"❌ Ошибка подключения к PostgreSQL публичному: {e2}")
            
            print("⚠️ Переключаемся на SQLite")
    
    # Fallback к SQLite
    import sqlite3
    conn = sqlite3.connect('calculations.db')
    print("✅ Подключились к SQLite")
    return conn, 'sqlite'

def init_database():
    """Инициализирует таблицы в БД"""
    conn, db_type = get_database_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        # PostgreSQL синтаксис
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calculations (
                id SERIAL PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT,
                price_yuan REAL NOT NULL,
                weight_kg REAL NOT NULL,
                quantity INTEGER NOT NULL,
                markup REAL NOT NULL,
                custom_rate REAL,
                product_url TEXT,
                cost_price_rub REAL NOT NULL,
                cost_price_usd REAL NOT NULL,
                sale_price_rub REAL NOT NULL,
                sale_price_usd REAL NOT NULL,
                profit_rub REAL NOT NULL,
                profit_usd REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        # SQLite синтаксис
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                category TEXT,
                price_yuan REAL NOT NULL,
                weight_kg REAL NOT NULL,
                quantity INTEGER NOT NULL,
                markup REAL NOT NULL,
                custom_rate REAL,
                product_url TEXT,
                cost_price_rub REAL NOT NULL,
                cost_price_usd REAL NOT NULL,
                sale_price_rub REAL NOT NULL,
                sale_price_usd REAL NOT NULL,
                profit_rub REAL NOT NULL,
                profit_usd REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Таблицы инициализированы ({db_type})")

def save_calculation_to_db(data: Dict[str, Any]) -> int:
    """Сохраняет расчет в БД"""
    conn, db_type = get_database_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        cursor.execute('''
            INSERT INTO calculations 
            (product_name, category, price_yuan, weight_kg, quantity, markup, custom_rate, 
             product_url, cost_price_rub, cost_price_usd, sale_price_rub, sale_price_usd, 
             profit_rub, profit_usd) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            RETURNING id
        ''', (
            data['product_name'], data['category'], data['price_yuan'], data['weight_kg'],
            data['quantity'], data['markup'], data.get('custom_rate'), data.get('product_url'),
            data['cost_price_total_rub'], data['cost_price_total_usd'],
            data['sale_price_total_rub'], data['sale_price_total_usd'],
            data['profit_total_rub'], data['profit_total_usd']
        ))
        calculation_id = cursor.fetchone()[0]
    else:
        cursor.execute('''
            INSERT INTO calculations 
            (product_name, category, price_yuan, weight_kg, quantity, markup, custom_rate, 
             product_url, cost_price_rub, cost_price_usd, sale_price_rub, sale_price_usd, 
             profit_rub, profit_usd) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['product_name'], data['category'], data['price_yuan'], data['weight_kg'],
            data['quantity'], data['markup'], data.get('custom_rate'), data.get('product_url'),
            data['cost_price_total_rub'], data['cost_price_total_usd'],
            data['sale_price_total_rub'], data['sale_price_total_usd'],
            data['profit_total_rub'], data['profit_total_usd']
        ))
        calculation_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return calculation_id

def get_calculation_history() -> List[Dict[str, Any]]:
    """Получает историю расчетов из БД"""
    conn, db_type = get_database_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, product_name, category, price_yuan, weight_kg, quantity, markup, 
               custom_rate, product_url, cost_price_rub, cost_price_usd, 
               sale_price_rub, sale_price_usd, profit_rub, profit_usd, created_at 
        FROM calculations 
        ORDER BY created_at DESC 
        LIMIT 50
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row[0],
            'product_name': row[1],
            'category': row[2],
            'price_yuan': row[3],
            'weight_kg': row[4],
            'quantity': row[5],
            'markup': row[6],
            'custom_rate': row[7],
            'product_url': row[8],
            'cost_price_rub': row[9],
            'cost_price_usd': row[10],
            'sale_price_rub': row[11],
            'sale_price_usd': row[12],
            'profit_rub': row[13],
            'profit_usd': row[14],
            'created_at': str(row[15])
        })
    
    return history

def restore_from_backup():
    """Восстанавливает данные из бэкапа при пустой БД"""
    try:
        # Проверяем, пуста ли БД
        history = get_calculation_history()
        if len(history) > 0:
            print(f"✅ БД уже содержит {len(history)} записей")
            return
        
        # Пытаемся загрузить из бэкапа
        try:
            with open('calculations_backup.json', 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
        except FileNotFoundError:
            print("❌ Файл бэкапа не найден")
            return
        
        print(f"🔄 Восстанавливаем {len(backup_data)} записей из бэкапа...")
        
        # Восстанавливаем каждую запись
        for record in backup_data:
            try:
                # Адаптируем данные под новый формат
                data = {
                    'product_name': record.get('product_name', ''),
                    'category': record.get('category', ''),
                    'price_yuan': record.get('price_yuan', 0),
                    'weight_kg': record.get('weight_kg', 0),
                    'quantity': record.get('quantity', 0),
                    'markup': record.get('markup', 1.7),
                    'custom_rate': record.get('custom_rate'),
                    'product_url': record.get('product_url'),
                    'cost_price_total_rub': record.get('cost_price_rub', 0),
                    'cost_price_total_usd': record.get('cost_price_usd', 0),
                    'sale_price_total_rub': record.get('sale_price_rub', 0),
                    'sale_price_total_usd': record.get('sale_price_usd', 0),
                    'profit_total_rub': record.get('profit_rub', 0),
                    'profit_total_usd': record.get('profit_usd', 0)
                }
                save_calculation_to_db(data)
            except Exception as e:
                print(f"⚠️ Ошибка восстановления записи: {e}")
                continue
        
        print(f"✅ Восстановлено {len(backup_data)} записей из бэкапа")
        
    except Exception as e:
        print(f"❌ Ошибка восстановления из бэкапа: {e}")

