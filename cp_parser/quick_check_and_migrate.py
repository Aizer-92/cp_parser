#!/usr/bin/env python3
"""
Быстрая проверка и миграция недостающих данных
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

SQLITE_URL = "sqlite:////Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser/database/commercial_proposals.db"
POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

BATCH_SIZE = 500

def check_counts():
    """Проверка количества записей"""
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    PgSession = sessionmaker(bind=postgres_engine)
    pg_session = PgSession()
    
    print("=" * 80)
    print("СРАВНЕНИЕ КОЛИЧЕСТВА ЗАПИСЕЙ")
    print("=" * 80)
    
    tables = ['projects', 'products', 'price_offers', 'product_images']
    results = {}
    
    for table in tables:
        sqlite_count = pd.read_sql_query(f"SELECT COUNT(*) as cnt FROM {table}", sqlite_engine).iloc[0]['cnt']
        postgres_count = pg_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        
        results[table] = {
            'sqlite': sqlite_count,
            'postgres': postgres_count,
            'missing': sqlite_count - postgres_count
        }
        
        status = "✅" if sqlite_count == postgres_count else "⚠️"
        print(f"\n{status} {table}:")
        print(f"   SQLite:     {sqlite_count:,}")
        print(f"   PostgreSQL: {postgres_count:,}")
        print(f"   Недостает:  {results[table]['missing']:,}")
    
    pg_session.close()
    print("\n" + "=" * 80)
    
    return results

def migrate_price_offers_fast():
    """Быстрая миграция price_offers"""
    print("\n🚀 МИГРАЦИЯ PRICE_OFFERS")
    print("=" * 80)
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    PgSession = sessionmaker(bind=postgres_engine)
    pg_session = PgSession()
    
    try:
        max_id = pg_session.execute(text("SELECT COALESCE(MAX(id), 0) FROM price_offers")).scalar()
        print(f"📊 Максимальный ID в PostgreSQL: {max_id}")
        
        df = pd.read_sql_query(f"SELECT * FROM price_offers WHERE id > {max_id}", sqlite_engine)
        total = len(df)
        
        if total == 0:
            print("✅ Все записи уже мигрированы!")
            return
        
        print(f"📊 Новых записей: {total:,}")
        df = df.where(pd.notna(df), None)
        
        inserted = 0
        for start_idx in range(0, total, BATCH_SIZE):
            end_idx = min(start_idx + BATCH_SIZE, total)
            batch = df.iloc[start_idx:end_idx]
            
            for _, row in batch.iterrows():
                try:
                    quantity_val = None
                    if row['quantity'] is not None:
                        try:
                            quantity_val = int(float(row['quantity']))
                        except:
                            pass
                    
                    pg_session.execute(text("""
                        INSERT INTO price_offers 
                        (id, product_id, table_id, quantity, quantity_unit, price_usd, price_rub, 
                         route, delivery_time_days, delivery_conditions, discount_percent, 
                         special_conditions, row_position, is_recommended, data_source, 
                         created_at, updated_at)
                        VALUES 
                        (:id, :product_id, :table_id, :quantity::bigint, :quantity_unit, :price_usd, :price_rub,
                         :route, :delivery_time_days, :delivery_conditions, :discount_percent,
                         :special_conditions, :row_position, :is_recommended, :data_source,
                         :created_at, :updated_at)
                    """), {
                        'id': int(row['id']),
                        'product_id': int(row['product_id']),
                        'table_id': row['table_id'],
                        'quantity': quantity_val,
                        'quantity_unit': row['quantity_unit'],
                        'price_usd': float(row['price_usd']) if row['price_usd'] is not None else None,
                        'price_rub': float(row['price_rub']) if row['price_rub'] is not None else None,
                        'route': row['route'],
                        'delivery_time_days': int(row['delivery_time_days']) if row['delivery_time_days'] is not None else None,
                        'delivery_conditions': row['delivery_conditions'],
                        'discount_percent': float(row['discount_percent']) if row['discount_percent'] is not None else None,
                        'special_conditions': row['special_conditions'],
                        'row_position': row['row_position'],
                        'is_recommended': bool(row['is_recommended']) if row['is_recommended'] is not None else None,
                        'data_source': row['data_source'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                    inserted += 1
                except Exception as e:
                    pg_session.rollback()
            
            pg_session.commit()
            print(f"✅ {end_idx}/{total} ({end_idx*100//total}%)")
        
        print(f"\n✅ Вставлено: {inserted:,}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        pg_session.rollback()
    finally:
        pg_session.close()

def migrate_product_images_fast():
    """Быстрая миграция product_images"""
    print("\n🚀 МИГРАЦИЯ PRODUCT_IMAGES")
    print("=" * 80)
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    PgSession = sessionmaker(bind=postgres_engine)
    pg_session = PgSession()
    
    try:
        max_id = pg_session.execute(text("SELECT COALESCE(MAX(id), 0) FROM product_images")).scalar()
        print(f"📊 Максимальный ID в PostgreSQL: {max_id}")
        
        df = pd.read_sql_query(f"SELECT * FROM product_images WHERE id > {max_id}", sqlite_engine)
        total = len(df)
        
        if total == 0:
            print("✅ Все записи уже мигрированы!")
            return
        
        print(f"📊 Новых записей: {total:,}")
        df = df.where(pd.notna(df), None)
        
        inserted = 0
        for start_idx in range(0, total, BATCH_SIZE):
            end_idx = min(start_idx + BATCH_SIZE, total)
            batch = df.iloc[start_idx:end_idx]
            
            for _, row in batch.iterrows():
                try:
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
                    """), {
                        'id': int(row['id']),
                        'product_id': int(row['product_id']),
                        'table_id': row['table_id'],
                        'image_url': row['image_url'],
                        'local_path': row['local_path'],
                        'image_filename': row['image_filename'],
                        'sheet_name': row['sheet_name'],
                        'cell_position': row['cell_position'],
                        'row_number': int(row['row_number']) if row['row_number'] is not None else None,
                        'column_number': int(row['column_number']) if row['column_number'] is not None else None,
                        'width_px': int(row['width_px']) if row['width_px'] is not None else None,
                        'height_px': int(row['height_px']) if row['height_px'] is not None else None,
                        'file_size_kb': float(row['file_size_kb']) if row['file_size_kb'] is not None else None,
                        'format': row['format'],
                        'is_main_image': bool(row['is_main_image']) if row['is_main_image'] is not None else None,
                        'display_order': int(row['display_order']) if row['display_order'] is not None else None,
                        'extraction_method': row['extraction_method'],
                        'quality_score': float(row['quality_score']) if row['quality_score'] is not None else None,
                        'processing_status': row['processing_status'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                    inserted += 1
                except Exception as e:
                    pg_session.rollback()
            
            pg_session.commit()
            print(f"✅ {end_idx}/{total} ({end_idx*100//total}%)")
        
        print(f"\n✅ Вставлено: {inserted:,}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        pg_session.rollback()
    finally:
        pg_session.close()

if __name__ == "__main__":
    # Проверяем текущее состояние
    results = check_counts()
    
    # Мигрируем недостающие данные
    if results['price_offers']['missing'] > 0:
        migrate_price_offers_fast()
    
    if results['product_images']['missing'] > 0:
        migrate_product_images_fast()
    
    # Финальная проверка
    print("\n" + "=" * 80)
    print("ФИНАЛЬНАЯ ПРОВЕРКА")
    print("=" * 80)
    check_counts()
