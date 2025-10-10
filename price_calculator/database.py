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
    """Возвращает подключение к БД с автоматическим переподключением"""
    global _db_connection, _db_type, _connection_lock
    
    with _connection_lock:
        # Проверяем существующее подключение
        if _db_connection is not None and _db_type is not None:
            try:
                # Тестируем подключение
                if _db_type == 'postgres':
                    cursor = _db_connection.cursor()
                    cursor.execute('SELECT 1')
                    cursor.close()
                    if not _db_connection.closed:
                        return _db_connection, _db_type
                else:
                    _db_connection.cursor().execute('SELECT 1').fetchone()
                    return _db_connection, _db_type
            except Exception as e:
                print(f"⚠️ Подключение к БД неактивно: {e}")
                # Закрываем старое подключение
                try:
                    _db_connection.close()
                except:
                    pass
                _db_connection = None
                _db_type = None
        
        # Создаем новое подключение
        print("🔌 Создание нового подключения к БД...")
        
        # Пробуем PostgreSQL (Railway)
        for url_env in ['DATABASE_PUBLIC_URL', 'DATABASE_URL']:
            database_url = os.environ.get(url_env)
            if database_url:
                try:
                    import psycopg2
                    from psycopg2.extras import RealDictCursor
                    
                    print(f"🐘 Попытка подключения PostgreSQL через {url_env}")
                    
                    # Преобразуем URL для psycopg2
                    if database_url.startswith('postgres://'):
                        database_url = database_url.replace('postgres://', 'postgresql://', 1)
                    
                    # Создаем подключение с настройками для Railway
                    _db_connection = psycopg2.connect(
                        database_url,
                        cursor_factory=RealDictCursor,
                        connect_timeout=10,
                        application_name='price_calculator'
                    )
                    
                    # Настройки для стабильного соединения
                    _db_connection.autocommit = False
                    
                    _db_type = 'postgres'
                    print(f"✅ PostgreSQL подключен успешно через {url_env}")
                    return _db_connection, _db_type
                    
                except Exception as e:
                    print(f"❌ Ошибка PostgreSQL {url_env}: {e}")
                    continue
        
        # Fallback к SQLite
        print("⚠️ PostgreSQL недоступен, переключаемся на SQLite")
        try:
            import sqlite3
            _db_connection = sqlite3.connect(
                'calculations.db', 
                check_same_thread=False,
                timeout=20.0
            )
            _db_connection.row_factory = sqlite3.Row  # Для совместимости с PostgreSQL
            _db_type = 'sqlite'
            print("✅ SQLite подключен")
            return _db_connection, _db_type
        except Exception as e:
            print(f"❌ Критическая ошибка SQLite: {e}")
            raise Exception(f"Не удалось подключиться ни к PostgreSQL, ни к SQLite: {e}")

def close_database_connection():
    """Принудительно закрывает текущее подключение"""
    global _db_connection, _db_type, _connection_lock
    
    with _connection_lock:
        if _db_connection:
            try:
                _db_connection.close()
                print("🔌 Подключение к БД закрыто")
            except:
                pass
            finally:
                _db_connection = None
                _db_type = None

def reconnect_database():
    """Принудительно переподключается к БД"""
    print("🔄 Принудительное переподключение к БД...")
    close_database_connection()
    return get_database_connection()

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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                category TEXT NOT NULL,
                material TEXT NOT NULL,
                data JSONB NOT NULL,
                UNIQUE (category, material)
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                material TEXT NOT NULL,
                data TEXT NOT NULL,
                UNIQUE (category, material)
            )
        ''')
    
    conn.commit()
    
    # МИГРАЦИЯ ОТКЛЮЧЕНА: init_db.py уже добавляет все необходимые колонки при старте
    # migrate_database_schema(conn, cursor, db_type)  # Закомментировано
    
    # НЕ закрываем подключение - переиспользуем его
    print(f"Таблицы инициализированы ({db_type})")

def migrate_database_schema(conn, cursor, db_type):
    """Добавляет отсутствующие столбцы в базу данных"""
    try:
        # Список новых столбцов для добавления
        new_columns = [
            ('calculation_type', 'TEXT DEFAULT "quick"'),
            ('packing_units_per_box', 'INTEGER'),
            ('packing_box_weight', 'REAL'),
            ('packing_box_length', 'REAL'),
            ('packing_box_width', 'REAL'),
            ('packing_box_height', 'REAL'),
            ('packing_total_boxes', 'INTEGER'),
            ('packing_total_volume', 'REAL'),
            ('packing_total_weight', 'REAL'),
            ('tnved_code', 'TEXT'),
            ('duty_rate', 'TEXT'),
            ('vat_rate', 'TEXT'),
            ('duty_amount_usd', 'REAL'),
            ('vat_amount_usd', 'REAL'),
            ('total_customs_cost_usd', 'REAL'),
            ('certificates', 'TEXT'),
            ('customs_notes', 'TEXT'),
            ('density_warning_message', 'TEXT'),
            ('calculated_density', 'REAL'),
            ('category_density', 'REAL')
        ]
        
        for column_name, column_type in new_columns:
            try:
                if db_type == 'postgres':
                    cursor.execute(f'ALTER TABLE calculations ADD COLUMN {column_name} {column_type}')
                else:
                    cursor.execute(f'ALTER TABLE calculations ADD COLUMN {column_name} {column_type}')
                print(f"✅ Добавлен столбец: {column_name}")
            except Exception as e:
                # Столбец уже существует или другая ошибка
                conn.rollback()  # КРИТИЧНО для PostgreSQL: откатываем абортированную транзакцию
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    continue  # Столбец уже есть, это нормально
                else:
                    print(f"⚠️  Не удалось добавить столбец {column_name}: {e}")
        
        conn.commit()
        print("Миграция базы данных завершена")
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        # Продолжаем работу - это не критично

def save_calculation_to_db(data: Dict[str, Any]) -> int:
    """Сохраняет расчет в БД"""
    try:
        conn, db_type = get_database_connection()  # Переиспользуем единое подключение
        cursor = conn.cursor()
        
        print(f"💾 Сохранение расчета в БД ({db_type}): {data['product_name']}")
        
        # Сериализуем custom_logistics для сохранения
        custom_logistics_json = None
        if data.get('custom_logistics'):
            custom_logistics_json = json.dumps(data['custom_logistics'])
        
        if db_type == 'postgres':
            cursor.execute('''
                INSERT INTO calculations 
                (product_name, category, price_yuan, weight_kg, quantity, markup, custom_rate, 
                 product_url, cost_price_rub, cost_price_usd, sale_price_rub, sale_price_usd, 
                 profit_rub, profit_usd, calculation_type,
                 packing_units_per_box, packing_box_weight, packing_box_length, packing_box_width, packing_box_height,
                 packing_total_boxes, packing_total_volume, packing_total_weight,
                 tnved_code, duty_rate, vat_rate, duty_amount_usd, vat_amount_usd, total_customs_cost_usd,
                 certificates, customs_notes, density_warning_message, calculated_density, category_density,
                 custom_logistics, forced_category) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                RETURNING id
            ''', (
                data['product_name'], data['category'], data['price_yuan'], data['weight_kg'],
                data['quantity'], data['markup'], data.get('custom_rate'), data.get('product_url'),
                data['cost_price_total_rub'], data['cost_price_total_usd'],
                data['sale_price_total_rub'], data['sale_price_total_usd'],
                data['profit_total_rub'], data['profit_total_usd'],
                data.get('calculation_type', 'quick'),
                data.get('packing_units_per_box'), data.get('packing_box_weight'), 
                data.get('packing_box_length'), data.get('packing_box_width'), data.get('packing_box_height'),
                data.get('packing_total_boxes'), data.get('packing_total_volume'), data.get('packing_total_weight'),
                # Данные о пошлинах
                data.get('tnved_code'), data.get('duty_rate'), data.get('vat_rate'),
                data.get('duty_amount_usd'), data.get('vat_amount_usd'), data.get('total_customs_cost_usd'),
                data.get('certificates'), data.get('customs_notes'),
                # Данные о предупреждениях плотности
                data.get('density_warning_message'), data.get('calculated_density'), data.get('category_density'),
                # Новые поля для кастомных параметров
                custom_logistics_json, data.get('forced_category')
            ))
            result = cursor.fetchone()
            calculation_id = result['id'] if isinstance(result, dict) else result[0]
            print(f"✅ PostgreSQL: Расчет сохранен с ID {calculation_id}")
        else:
            cursor.execute('''
                INSERT INTO calculations 
                (product_name, category, price_yuan, weight_kg, quantity, markup, custom_rate, 
                 product_url, cost_price_rub, cost_price_usd, sale_price_rub, sale_price_usd, 
                 profit_rub, profit_usd, calculation_type,
                 packing_units_per_box, packing_box_weight, packing_box_length, packing_box_width, packing_box_height,
                 packing_total_boxes, packing_total_volume, packing_total_weight,
                 tnved_code, duty_rate, vat_rate, duty_amount_usd, vat_amount_usd, total_customs_cost_usd,
                 certificates, customs_notes, density_warning_message, calculated_density, category_density,
                 custom_logistics, forced_category) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['product_name'], data['category'], data['price_yuan'], data['weight_kg'],
                data['quantity'], data['markup'], data.get('custom_rate'), data.get('product_url'),
                data['cost_price_total_rub'], data['cost_price_total_usd'],
                data['sale_price_total_rub'], data['sale_price_total_usd'],
                data['profit_total_rub'], data['profit_total_usd'],
                data.get('calculation_type', 'quick'),
                data.get('packing_units_per_box'), data.get('packing_box_weight'), 
                data.get('packing_box_length'), data.get('packing_box_width'), data.get('packing_box_height'),
                data.get('packing_total_boxes'), data.get('packing_total_volume'), data.get('packing_total_weight'),
                # Данные о пошлинах
                data.get('tnved_code'), data.get('duty_rate'), data.get('vat_rate'),
                data.get('duty_amount_usd'), data.get('vat_amount_usd'), data.get('total_customs_cost_usd'),
                data.get('certificates'), data.get('customs_notes'),
                # Данные о предупреждениях плотности
                data.get('density_warning_message'), data.get('calculated_density'), data.get('category_density'),
                # Новые поля для кастомных параметров
                custom_logistics_json, data.get('forced_category')
            ))
            calculation_id = cursor.lastrowid
            print(f"✅ SQLite: Расчет сохранен с ID {calculation_id}")
        
        # КРИТИЧНО: Коммитим изменения
        conn.commit()
        print(f"✅ COMMIT выполнен успешно для ID {calculation_id}")
        
        # НЕ закрываем подключение - переиспользуем его
        cursor.close()
        return calculation_id
        
    except Exception as e:
        print(f"❌ ОШИБКА сохранения в БД: {e}")
        import traceback
        traceback.print_exc()
        # Откатываем транзакцию при ошибке
        try:
            conn.rollback()
            print("⚠️ ROLLBACK выполнен")
        except:
            pass
        raise e


def upsert_category(category_data: Dict[str, Any]) -> None:
    """Сохраняет или обновляет категорию в таблице categories"""
    conn, db_type = get_database_connection()
    cursor = conn.cursor()

    category = category_data.get('category')
    material = category_data.get('material', '')

    serialized = json.dumps(category_data, ensure_ascii=False)

    if db_type == 'postgres':
        cursor.execute('''
            INSERT INTO categories (category, material, data)
            VALUES (%s, %s, %s)
            ON CONFLICT (category, material) DO UPDATE SET data = EXCLUDED.data
        ''', (category, material, serialized))
    else:
        cursor.execute('''
            INSERT INTO categories (category, material, data)
            VALUES (?, ?, ?)
            ON CONFLICT(category, material) DO UPDATE SET data = ?
        ''', (category, material, serialized, serialized))

    conn.commit()


def load_categories_from_db() -> List[Dict[str, Any]]:
    """Загружает все категории из таблицы categories"""
    conn, db_type = get_database_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT data FROM categories ORDER BY category')
    rows = cursor.fetchall()

    categories = []
    for row in rows:
        try:
            # Универсальный способ получения данных
            if db_type == 'postgres':
                # PostgreSQL с RealDictCursor - доступ по ключу
                raw = row['data'] if isinstance(row, dict) else row[0]
            else:
                # SQLite с row_factory - доступ по ключу или индексу
                raw = row['data'] if hasattr(row, 'keys') else row[0]

            # JSONB в Postgres приходит как dict, а в SQLite — как str/bytes
            if isinstance(raw, (dict, list)):
                categories.append(raw)
                continue

            if isinstance(raw, bytes):
                raw = raw.decode('utf-8')

            if isinstance(raw, str):
                try:
                    categories.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue
                    
        except (KeyError, IndexError, TypeError) as e:
            print(f"⚠️ Ошибка обработки строки категории: {e}")
            continue

    return categories

def get_calculation_history() -> List[Dict[str, Any]]:
    """Получает историю расчетов из БД с автоматическим переподключением"""
    try:
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, product_name, category, price_yuan, weight_kg, quantity, markup, 
                   custom_rate, product_url, cost_price_rub, cost_price_usd, 
                   sale_price_rub, sale_price_usd, profit_rub, profit_usd, created_at,
                   calculation_type,
                   packing_units_per_box, packing_box_weight, packing_box_length, packing_box_width, packing_box_height,
                   packing_total_boxes, packing_total_volume, packing_total_weight,
                   custom_logistics, forced_category
            FROM calculations 
            ORDER BY created_at DESC 
            LIMIT 50
        ''')
        
        rows = cursor.fetchall()
        cursor.close()
        
        history = []
        for row in rows:
            if db_type == 'postgres':
                # PostgreSQL с RealDictCursor возвращает dict-like объекты
                item = dict(row)
            else:
                # SQLite с row_factory = sqlite3.Row
                item = dict(row)
            
            # Десериализуем custom_logistics из JSON если есть
            if item.get('custom_logistics'):
                if isinstance(item['custom_logistics'], str):
                    try:
                        item['custom_logistics'] = json.loads(item['custom_logistics'])
                    except json.JSONDecodeError:
                        item['custom_logistics'] = None
            
            history.append(item)
        
        print(f"✅ История загружена: {len(history)} записей")
        return history
        
    except Exception as e:
        print(f"❌ Ошибка загрузки истории: {e}")
        # Пробуем переподключиться один раз
        try:
            print("🔄 Попытка переподключения к БД...")
            conn, db_type = reconnect_database()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, product_name, category, price_yuan, weight_kg, quantity, markup, 
                       custom_rate, product_url, cost_price_rub, cost_price_usd, 
                       sale_price_rub, sale_price_usd, profit_rub, profit_usd, created_at,
                       calculation_type,
                       packing_units_per_box, packing_box_weight, packing_box_length, packing_box_width, packing_box_height,
                       packing_total_boxes, packing_total_volume, packing_total_weight,
                       custom_logistics, forced_category
                FROM calculations 
                ORDER BY created_at DESC 
                LIMIT 50
            ''')
            
            rows = cursor.fetchall()
            cursor.close()
            
            history = []
            for row in rows:
                item = dict(row)
                
                # Десериализуем custom_logistics из JSON если есть
                if item.get('custom_logistics'):
                    if isinstance(item['custom_logistics'], str):
                        try:
                            item['custom_logistics'] = json.loads(item['custom_logistics'])
                        except json.JSONDecodeError:
                            item['custom_logistics'] = None
                
                history.append(item)
            
            print(f"✅ История загружена после переподключения: {len(history)} записей")
            return history
            
        except Exception as retry_error:
            print(f"❌ Повторная ошибка загрузки истории: {retry_error}")
            return []

def update_calculation(calculation_id: int, data: dict):
    """Обновляет существующий расчет в базе данных"""
    try:
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        # Сериализуем custom_logistics для сохранения
        custom_logistics_json = None
        if data.get('custom_logistics'):
            custom_logistics_json = json.dumps(data['custom_logistics'])
        
        # Обновляем запись
        if db_type == 'postgres':
            cursor.execute('''
                UPDATE calculations 
                SET product_name = %s, category = %s, price_yuan = %s, weight_kg = %s, 
                    quantity = %s, markup = %s, custom_rate = %s, product_url = %s,
                    cost_price_rub = %s, cost_price_usd = %s, sale_price_rub = %s, 
                    sale_price_usd = %s, profit_rub = %s, profit_usd = %s,
                    packing_units_per_box = %s, packing_box_weight = %s, 
                    packing_box_length = %s, packing_box_width = %s, packing_box_height = %s,
                    packing_total_boxes = %s, packing_total_volume = %s, packing_total_weight = %s,
                    custom_logistics = %s, forced_category = %s
                WHERE id = %s
                RETURNING id
            ''', (
                data['product_name'], data['category'], data['price_yuan'], data['weight_kg'],
                data['quantity'], data['markup'], data.get('custom_rate'),
                data.get('product_url', ''), data['cost_price_rub'], data['cost_price_usd'],
                data['sale_price_rub'], data['sale_price_usd'], data['profit_rub'],
                data['profit_usd'],
                # Данные пакинга
                data.get('packing_units_per_box'), data.get('packing_box_weight'),
                data.get('packing_box_length'), data.get('packing_box_width'), data.get('packing_box_height'),
                data.get('packing_total_boxes'), data.get('packing_total_volume'), data.get('packing_total_weight'),
                # Новые поля для кастомных параметров
                custom_logistics_json, data.get('forced_category'),
                calculation_id
            ))
            
            if not cursor.fetchone():
                raise ValueError("Расчет не найден")
            
        else:  # SQLite
            cursor.execute('''
                UPDATE calculations 
                SET product_name = ?, category = ?, price_yuan = ?, weight_kg = ?, 
                    quantity = ?, markup = ?, custom_rate = ?, product_url = ?,
                    cost_price_rub = ?, cost_price_usd = ?, sale_price_rub = ?, 
                    sale_price_usd = ?, profit_rub = ?, profit_usd = ?,
                    packing_units_per_box = ?, packing_box_weight = ?, 
                    packing_box_length = ?, packing_box_width = ?, packing_box_height = ?,
                    packing_total_boxes = ?, packing_total_volume = ?, packing_total_weight = ?,
                    custom_logistics = ?, forced_category = ?
                WHERE id = ?
            ''', (
                data['product_name'], data['category'], data['price_yuan'], data['weight_kg'],
                data['quantity'], data['markup'], data.get('custom_rate'),
                data.get('product_url', ''), data['cost_price_rub'], data['cost_price_usd'],
                data['sale_price_rub'], data['sale_price_usd'], data['profit_rub'],
                data['profit_usd'],
                # Данные пакинга
                data.get('packing_units_per_box'), data.get('packing_box_weight'),
                data.get('packing_box_length'), data.get('packing_box_width'), data.get('packing_box_height'),
                data.get('packing_total_boxes'), data.get('packing_total_volume'), data.get('packing_total_weight'),
                # Новые поля для кастомных параметров
                custom_logistics_json, data.get('forced_category'),
                calculation_id
            ))
            
            if cursor.rowcount == 0:
                raise ValueError("Расчет не найден")
        
        conn.commit()
        print(f"✅ Расчет {calculation_id} обновлен")
        return True
        
    except ValueError as e:
        print(f"❌ {e}")
        raise
    except Exception as e:
        print(f"❌ Ошибка обновления расчета: {e}")
        raise

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

