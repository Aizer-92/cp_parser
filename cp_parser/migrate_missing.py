#!/usr/bin/env python3
"""
Миграция пропущенных записей
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLITE_URL = "sqlite:////Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser/database/commercial_proposals.db"
POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

def find_and_migrate_missing_offers():
    """Находим и мигрируем пропущенные price_offers"""
    print("🔍 Поиск пропущенных price_offers...")
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    pg_session = PgSession()
    
    try:
        # Получаем все ID из обеих БД
        sqlite_ids = set([row[0] for row in sqlite_session.execute(text("SELECT id FROM price_offers")).fetchall()])
        pg_ids = set([row[0] for row in pg_session.execute(text("SELECT id FROM price_offers")).fetchall()])
        
        missing_ids = sqlite_ids - pg_ids
        
        print(f"📊 SQLite: {len(sqlite_ids):,} записей")
        print(f"📊 PostgreSQL: {len(pg_ids):,} записей")
        print(f"❌ Пропущено: {len(missing_ids):,} записей")
        
        if not missing_ids:
            print("✅ Все записи уже мигрированы!")
            return
        
        print(f"\n🚀 Миграция {len(missing_ids)} пропущенных записей...")
        
        inserted = 0
        errors = 0
        
        for record_id in sorted(missing_ids):
            try:
                # Читаем из SQLite
                row = sqlite_session.execute(
                    text("SELECT * FROM price_offers WHERE id = :id"),
                    {'id': record_id}
                ).fetchone()
                
                if not row:
                    continue
                
                row_dict = dict(row._mapping)
                
                # Обработка quantity
                quantity_val = None
                if row_dict['quantity'] is not None:
                    try:
                        quantity_val = int(float(row_dict['quantity']))
                    except:
                        pass
                
                # Вставляем в PostgreSQL
                pg_session.execute(text("""
                    INSERT INTO price_offers 
                    (id, product_id, table_id, quantity, quantity_unit, price_usd, price_rub, 
                     route, delivery_time_days, delivery_conditions, discount_percent, 
                     special_conditions, row_position, is_recommended, data_source, 
                     created_at, updated_at)
                    VALUES 
                    (:id, :product_id, :table_id, :quantity, :quantity_unit, :price_usd, :price_rub,
                     :route, :delivery_time_days, :delivery_conditions, :discount_percent,
                     :special_conditions, :row_position, :is_recommended, :data_source,
                     :created_at, :updated_at)
                """), {
                    'id': row_dict['id'],
                    'product_id': row_dict['product_id'],
                    'table_id': row_dict['table_id'],
                    'quantity': quantity_val,
                    'quantity_unit': row_dict['quantity_unit'],
                    'price_usd': row_dict['price_usd'],
                    'price_rub': row_dict['price_rub'],
                    'route': row_dict['route'],
                    'delivery_time_days': row_dict['delivery_time_days'],
                    'delivery_conditions': row_dict['delivery_conditions'],
                    'discount_percent': row_dict['discount_percent'],
                    'special_conditions': row_dict['special_conditions'],
                    'row_position': row_dict['row_position'],
                    'is_recommended': bool(row_dict['is_recommended']) if row_dict['is_recommended'] is not None else None,
                    'data_source': row_dict['data_source'],
                    'created_at': row_dict['created_at'],
                    'updated_at': row_dict['updated_at']
                })
                
                inserted += 1
                
                if inserted % 50 == 0:
                    pg_session.commit()
                    print(f"  ✅ {inserted}/{len(missing_ids)}")
                
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  ❌ ID {record_id}: {str(e)[:100]}")
        
        pg_session.commit()
        print(f"\n✅ Вставлено: {inserted}, Ошибок: {errors}")
        
    finally:
        sqlite_session.close()
        pg_session.close()

def find_and_migrate_missing_images():
    """Находим и мигрируем пропущенные product_images"""
    print("\n🔍 Поиск пропущенных product_images...")
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    pg_session = PgSession()
    
    try:
        # Получаем все ID
        sqlite_ids = set([row[0] for row in sqlite_session.execute(text("SELECT id FROM product_images")).fetchall()])
        pg_ids = set([row[0] for row in pg_session.execute(text("SELECT id FROM product_images")).fetchall()])
        
        missing_ids = sqlite_ids - pg_ids
        
        print(f"📊 SQLite: {len(sqlite_ids):,} записей")
        print(f"📊 PostgreSQL: {len(pg_ids):,} записей")
        print(f"❌ Пропущено: {len(missing_ids):,} записей")
        
        if not missing_ids:
            print("✅ Все записи уже мигрированы!")
            return
        
        print(f"\n🚀 Миграция {len(missing_ids)} пропущенных записей...")
        
        inserted = 0
        errors = 0
        
        for record_id in sorted(missing_ids):
            try:
                # Читаем из SQLite
                row = sqlite_session.execute(
                    text("SELECT * FROM product_images WHERE id = :id"),
                    {'id': record_id}
                ).fetchone()
                
                if not row:
                    continue
                
                row_dict = dict(row._mapping)
                
                # Вставляем в PostgreSQL
                pg_session.execute(text("""
                    INSERT INTO product_images 
                    (id, product_id, table_id, image_url, local_path, image_filename, 
                     sheet_name, cell_position, row_number, column_number, 
                     width_px, height_px, file_size_kb, format, is_main_image, 
                     display_order, extraction_method, quality_score, processing_status,
                     created_at, updated_at)
                    VALUES 
                    (:id, :product_id, :table_id, :image_url, :local_path, :image_filename,
                     :sheet_name, :cell_position, :row_number, :column_number,
                     :width_px, :height_px, :file_size_kb, :format, :is_main_image,
                     :display_order, :extraction_method, :quality_score, :processing_status,
                     :created_at, :updated_at)
                """), row_dict)
                
                inserted += 1
                
                if inserted % 500 == 0:
                    pg_session.commit()
                    print(f"  ✅ {inserted}/{len(missing_ids)}")
                
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  ❌ ID {record_id}: {str(e)[:100]}")
        
        pg_session.commit()
        print(f"\n✅ Вставлено: {inserted}, Ошибок: {errors}")
        
    finally:
        sqlite_session.close()
        pg_session.close()

if __name__ == "__main__":
    print("=" * 80)
    print("МИГРАЦИЯ ПРОПУЩЕННЫХ ЗАПИСЕЙ")
    print("=" * 80)
    
    find_and_migrate_missing_offers()
    find_and_migrate_missing_images()
    
    print("\n" + "=" * 80)
    print("✅ ГОТОВО!")
    print("=" * 80)

