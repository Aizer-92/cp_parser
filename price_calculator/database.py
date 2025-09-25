import os
import json
from typing import List, Dict, Any, Optional, Tuple
import threading

# Универсальный модуль для работы с БД (PostgreSQL или SQLite)

# Глобальные переменные для singleton подключения
_db_connection = None
_db_type = None
_connection_lock = threading.Lock()

def get_database_connection() -> Tuple[any, str]:
    """Возвращает единое переиспользуемое подключение к БД (PostgreSQL или SQLite)"""
    global _db_connection, _db_type, _connection_lock
    
    with _connection_lock:
        # Если подключение уже существует и активно, возвращаем его
        if _db_connection is not None and _db_type is not None:
            try:
                # Проверяем активность подключения
                if _db_type == 'postgres':
                    _db_connection.cursor().execute('SELECT 1')
                else:
                    _db_connection.cursor().execute('SELECT 1').fetchone()
                return _db_connection, _db_type
            except:
                # Подключение неактивно, создаем новое
                _db_connection = None
                _db_type = None
        
        # Создаем новое подключение
        print(f"🔌 Создание единого подключения к БД...")
        
        # Сначала пробуем PUBLIC URL (более надежный на Railway)
        database_public_url = os.environ.get('DATABASE_PUBLIC_URL')
        if database_public_url:
            try:
                import psycopg2
                print(f"🔗 PostgreSQL через PUBLIC URL")
                
                # Преобразуем URL для psycopg2
                if database_public_url.startswith('postgres://'):
                    database_public_url = database_public_url.replace('postgres://', 'postgresql://', 1)
                
                _db_connection = psycopg2.connect(database_public_url)
                _db_type = 'postgres'
                print("✅ PostgreSQL подключен успешно")
                return _db_connection, _db_type
            except Exception as e:
                print(f"❌ Ошибка PostgreSQL PUBLIC URL: {e}")
        
        # Fallback на обычный DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            try:
                import psycopg2
                print(f"🔗 PostgreSQL через DATABASE_URL (fallback)")
                
                # Преобразуем URL для psycopg2
                if database_url.startswith('postgres://'):
                    database_url = database_url.replace('postgres://', 'postgresql://', 1)
                
                _db_connection = psycopg2.connect(database_url)
                _db_type = 'postgres'
                print("✅ PostgreSQL подключен успешно")
                return _db_connection, _db_type
            except Exception as e:
                print(f"❌ Ошибка PostgreSQL DATABASE_URL: {e}")
                print("⚠️ Переключаемся на SQLite")
        
        # Fallback к SQLite
        import sqlite3
        _db_connection = sqlite3.connect('calculations.db', check_same_thread=False)
        _db_type = 'sqlite'
        print("✅ SQLite подключен")
        return _db_connection, _db_type

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
    # НЕ закрываем подключение - переиспользуем его
    print(f"✅ Таблицы инициализированы ({db_type})")

def save_calculation_to_db(data: Dict[str, Any]) -> int:
    """Сохраняет расчет в БД"""
    conn, db_type = get_database_connection()  # Переиспользуем единое подключение
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
    # НЕ закрываем подключение - переиспользуем его
    return calculation_id

def get_calculation_history() -> List[Dict[str, Any]]:
    """Получает историю расчетов из БД"""
    conn, db_type = get_database_connection()  # Переиспользуем единое подключение
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
    # НЕ закрываем подключение - переиспользуем его
    
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
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM calculations')
        count = cursor.fetchone()[0]
        # НЕ закрываем подключение - переиспользуем его
        
        if count > 0:
            print(f"✅ БД уже содержит {count} записей")
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

