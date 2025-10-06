#!/usr/bin/env python3
"""
Полная проверка миграции SQLite -> PostgreSQL
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import random

SQLITE_URL = "sqlite:////Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser/database/commercial_proposals.db"
POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

def check_counts():
    """Проверка количества записей"""
    print("=" * 80)
    print("1. ПРОВЕРКА КОЛИЧЕСТВА ЗАПИСЕЙ")
    print("=" * 80)
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    pg_session = PgSession()
    
    tables = ['projects', 'products', 'price_offers', 'product_images']
    all_match = True
    
    for table in tables:
        sqlite_count = sqlite_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        postgres_count = pg_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        
        match = sqlite_count == postgres_count
        status = "✅" if match else "❌"
        
        print(f"\n{status} {table}:")
        print(f"   SQLite:     {sqlite_count:,}")
        print(f"   PostgreSQL: {postgres_count:,}")
        
        if not match:
            all_match = False
            diff = sqlite_count - postgres_count
            print(f"   ⚠️ Разница:  {diff:,}")
    
    sqlite_session.close()
    pg_session.close()
    
    print("\n" + "=" * 80)
    if all_match:
        print("✅ ВСЕ ТАБЛИЦЫ ИМЕЮТ ОДИНАКОВОЕ КОЛИЧЕСТВО ЗАПИСЕЙ!")
    else:
        print("❌ ЕСТЬ РАСХОЖДЕНИЯ В КОЛИЧЕСТВЕ ЗАПИСЕЙ!")
    print("=" * 80)
    
    return all_match

def verify_random_records(table_name, sample_size=50):
    """Проверка случайных записей из таблицы"""
    print(f"\n{'=' * 80}")
    print(f"2. ПРОВЕРКА СЛУЧАЙНЫХ ЗАПИСЕЙ: {table_name} (выборка {sample_size})")
    print("=" * 80)
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    pg_session = PgSession()
    
    try:
        # Получаем все ID из SQLite
        all_ids = [row[0] for row in sqlite_session.execute(text(f"SELECT id FROM {table_name}")).fetchall()]
        
        # Выбираем случайные ID
        sample_ids = random.sample(all_ids, min(sample_size, len(all_ids)))
        
        print(f"\n📊 Проверяем {len(sample_ids)} случайных записей...")
        
        mismatches = 0
        matches = 0
        missing = 0
        
        for record_id in sample_ids:
            # Получаем запись из SQLite
            sqlite_row = sqlite_session.execute(
                text(f"SELECT * FROM {table_name} WHERE id = :id"),
                {'id': record_id}
            ).fetchone()
            
            # Получаем запись из PostgreSQL
            pg_row = pg_session.execute(
                text(f"SELECT * FROM {table_name} WHERE id = :id"),
                {'id': record_id}
            ).fetchone()
            
            if pg_row is None:
                missing += 1
                if missing <= 3:
                    print(f"  ❌ ID {record_id}: отсутствует в PostgreSQL!")
                continue
            
            # Сравниваем данные
            sqlite_dict = dict(sqlite_row._mapping)
            pg_dict = dict(pg_row._mapping)
            
            # Проверяем каждое поле
            field_mismatches = []
            for key in sqlite_dict.keys():
                sqlite_val = sqlite_dict[key]
                pg_val = pg_dict.get(key)
                
                # Нормализация для сравнения
                if sqlite_val is None and pg_val is None:
                    continue
                
                # Преобразуем типы для сравнения
                if isinstance(sqlite_val, float) and isinstance(pg_val, (float, int)):
                    if abs(float(sqlite_val) - float(pg_val)) < 0.01:
                        continue
                
                if str(sqlite_val) != str(pg_val):
                    field_mismatches.append(f"{key}: SQLite={sqlite_val} vs PG={pg_val}")
            
            if field_mismatches:
                mismatches += 1
                if mismatches <= 3:
                    print(f"  ⚠️ ID {record_id}: несовпадения в полях:")
                    for fm in field_mismatches[:3]:
                        print(f"     - {fm}")
            else:
                matches += 1
        
        print(f"\n{'=' * 80}")
        print(f"РЕЗУЛЬТАТЫ ПРОВЕРКИ {table_name}:")
        print(f"  ✅ Совпадений:     {matches:,}")
        print(f"  ⚠️ Несовпадений:   {mismatches:,}")
        print(f"  ❌ Отсутствуют:    {missing:,}")
        
        success_rate = (matches / len(sample_ids)) * 100 if sample_ids else 0
        print(f"  📊 Успешность:     {success_rate:.1f}%")
        print("=" * 80)
        
        return matches == len(sample_ids)
        
    except Exception as e:
        print(f"\n❌ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        sqlite_session.close()
        pg_session.close()

def verify_specific_records():
    """Проверка конкретных записей с большими значениями"""
    print(f"\n{'=' * 80}")
    print("3. ПРОВЕРКА ЗАПИСЕЙ С БОЛЬШИМИ ЗНАЧЕНИЯМИ QUANTITY")
    print("=" * 80)
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    pg_session = PgSession()
    
    try:
        # Находим записи с большими quantity
        large_qty_rows = sqlite_session.execute(text("""
            SELECT id, quantity FROM price_offers 
            WHERE quantity > 1000000 
            ORDER BY quantity DESC 
            LIMIT 10
        """)).fetchall()
        
        print(f"\n📊 Найдено {len(large_qty_rows)} записей с quantity > 1,000,000")
        
        for row in large_qty_rows:
            record_id = row[0]
            sqlite_qty = row[1]
            
            pg_row = pg_session.execute(
                text("SELECT quantity FROM price_offers WHERE id = :id"),
                {'id': record_id}
            ).fetchone()
            
            if pg_row:
                pg_qty = pg_row[0]
                match = "✅" if sqlite_qty == pg_qty else "❌"
                print(f"  {match} ID {record_id}: SQLite={sqlite_qty:,} | PostgreSQL={pg_qty:,}")
            else:
                print(f"  ❌ ID {record_id}: отсутствует в PostgreSQL!")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        sqlite_session.close()
        pg_session.close()

def main():
    print("\n" + "=" * 80)
    print("ПОЛНАЯ ПРОВЕРКА МИГРАЦИИ SQLite → PostgreSQL")
    print("=" * 80)
    
    # 1. Проверка количества
    counts_match = check_counts()
    
    # 2. Проверка случайных записей из каждой таблицы
    tables_to_check = {
        'projects': 50,
        'products': 100,
        'price_offers': 100,
        'product_images': 50
    }
    
    all_verified = True
    for table, sample_size in tables_to_check.items():
        verified = verify_random_records(table, sample_size)
        if not verified:
            all_verified = False
    
    # 3. Проверка записей с большими значениями
    verify_specific_records()
    
    # Итоговый отчет
    print("\n" + "=" * 80)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)
    
    if counts_match and all_verified:
        print("✅ МИГРАЦИЯ ПРОШЛА УСПЕШНО!")
        print("✅ Все записи перенесены корректно")
        print("✅ Данные полностью совпадают")
    else:
        print("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
        if not counts_match:
            print("  - Количество записей не совпадает")
        if not all_verified:
            print("  - Обнаружены несовпадения в данных")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
