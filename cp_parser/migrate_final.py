#!/usr/bin/env python3
"""
Финальная миграция с исправленным SQL синтаксисом
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

SQLITE_URL = "sqlite:////Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser/database/commercial_proposals.db"
POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

BATCH_SIZE = 1000

def check_counts():
    """Проверка количества записей"""
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    PgSession = sessionmaker(bind=postgres_engine)
    pg_session = PgSession()
    
    print("=" * 80)
    print("ТЕКУЩЕЕ СОСТОЯНИЕ БД")
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

def migrate_price_offers():
    """Миграция price_offers"""
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
            pg_session.close()
            return
        
        print(f"📊 Новых записей для миграции: {total:,}\n")
        df = df.where(pd.notna(df), None)
        
        inserted = 0
        errors = 0
        error_samples = []
        
        for start_idx in range(0, total, BATCH_SIZE):
            end_idx = min(start_idx + BATCH_SIZE, total)
            batch = df.iloc[start_idx:end_idx]
            
            batch_inserted = 0
            batch_errors = 0
            
            for _, row in batch.iterrows():
                try:
                    # Обработка quantity - просто integer, без ::bigint
                    quantity_val = None
                    if row['quantity'] is not None:
                        try:
                            quantity_val = int(float(row['quantity']))
                        except:
                            pass
                    
                    # ИСПРАВЛЕНО: убрал ::bigint из SQL
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
                        'id': int(row['id']),
                        'product_id': int(row['product_id']),
                        'table_id': row['table_id'] if pd.notna(row['table_id']) else None,
                        'quantity': quantity_val,
                        'quantity_unit': row['quantity_unit'] if pd.notna(row['quantity_unit']) else None,
                        'price_usd': float(row['price_usd']) if pd.notna(row['price_usd']) else None,
                        'price_rub': float(row['price_rub']) if pd.notna(row['price_rub']) else None,
                        'route': row['route'] if pd.notna(row['route']) else None,
                        'delivery_time_days': int(row['delivery_time_days']) if pd.notna(row['delivery_time_days']) else None,
                        'delivery_conditions': row['delivery_conditions'] if pd.notna(row['delivery_conditions']) else None,
                        'discount_percent': float(row['discount_percent']) if pd.notna(row['discount_percent']) else None,
                        'special_conditions': row['special_conditions'] if pd.notna(row['special_conditions']) else None,
                        'row_position': row['row_position'] if pd.notna(row['row_position']) else None,
                        'is_recommended': bool(row['is_recommended']) if pd.notna(row['is_recommended']) else None,
                        'data_source': row['data_source'] if pd.notna(row['data_source']) else None,
                        'created_at': row['created_at'] if pd.notna(row['created_at']) else None,
                        'updated_at': row['updated_at'] if pd.notna(row['updated_at']) else None
                    })
                    
                    batch_inserted += 1
                    
                except Exception as e:
                    batch_errors += 1
                    if len(error_samples) < 5:
                        error_samples.append(f"ID {row['id']}: {str(e)[:150]}")
                    continue
            
            # Коммитим батч
            try:
                pg_session.commit()
                inserted += batch_inserted
                errors += batch_errors
                print(f"✅ {end_idx:,}/{total:,} ({end_idx*100//total}%) | +{batch_inserted}, ошибок: {batch_errors}")
            except Exception as e:
                print(f"❌ Ошибка коммита: {e}")
                pg_session.rollback()
        
        print(f"\n{'='*80}")
        print(f"✅ ИТОГО вставлено: {inserted:,}")
        print(f"❌ ИТОГО ошибок: {errors:,}")
        
        if error_samples:
            print(f"\n🔍 Примеры ошибок:")
            for err in error_samples:
                print(f"  - {err}")
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        pg_session.rollback()
    finally:
        pg_session.close()

def migrate_product_images():
    """Миграция product_images"""
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
            pg_session.close()
            return
        
        print(f"📊 Новых записей для миграции: {total:,}\n")
        df = df.where(pd.notna(df), None)
        
        inserted = 0
        errors = 0
        error_samples = []
        
        for start_idx in range(0, total, BATCH_SIZE):
            end_idx = min(start_idx + BATCH_SIZE, total)
            batch = df.iloc[start_idx:end_idx]
            
            batch_inserted = 0
            batch_errors = 0
            
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
                        'table_id': row['table_id'] if pd.notna(row['table_id']) else None,
                        'image_url': row['image_url'] if pd.notna(row['image_url']) else None,
                        'local_path': row['local_path'] if pd.notna(row['local_path']) else None,
                        'image_filename': row['image_filename'] if pd.notna(row['image_filename']) else None,
                        'sheet_name': row['sheet_name'] if pd.notna(row['sheet_name']) else None,
                        'cell_position': row['cell_position'] if pd.notna(row['cell_position']) else None,
                        'row_number': int(row['row_number']) if pd.notna(row['row_number']) else None,
                        'column_number': int(row['column_number']) if pd.notna(row['column_number']) else None,
                        'width_px': int(row['width_px']) if pd.notna(row['width_px']) else None,
                        'height_px': int(row['height_px']) if pd.notna(row['height_px']) else None,
                        'file_size_kb': float(row['file_size_kb']) if pd.notna(row['file_size_kb']) else None,
                        'format': row['format'] if pd.notna(row['format']) else None,
                        'is_main_image': bool(row['is_main_image']) if pd.notna(row['is_main_image']) else None,
                        'display_order': int(row['display_order']) if pd.notna(row['display_order']) else None,
                        'extraction_method': row['extraction_method'] if pd.notna(row['extraction_method']) else None,
                        'quality_score': float(row['quality_score']) if pd.notna(row['quality_score']) else None,
                        'processing_status': row['processing_status'] if pd.notna(row['processing_status']) else None,
                        'created_at': row['created_at'] if pd.notna(row['created_at']) else None,
                        'updated_at': row['updated_at'] if pd.notna(row['updated_at']) else None
                    })
                    
                    batch_inserted += 1
                    
                except Exception as e:
                    batch_errors += 1
                    if len(error_samples) < 5:
                        error_samples.append(f"ID {row['id']}: {str(e)[:150]}")
                    continue
            
            # Коммитим батч
            try:
                pg_session.commit()
                inserted += batch_inserted
                errors += batch_errors
                print(f"✅ {end_idx:,}/{total:,} ({end_idx*100//total}%) | +{batch_inserted}, ошибок: {batch_errors}")
            except Exception as e:
                print(f"❌ Ошибка коммита: {e}")
                pg_session.rollback()
        
        print(f"\n{'='*80}")
        print(f"✅ ИТОГО вставлено: {inserted:,}")
        print(f"❌ ИТОГО ошибок: {errors:,}")
        
        if error_samples:
            print(f"\n🔍 Примеры ошибок:")
            for err in error_samples:
                print(f"  - {err}")
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        pg_session.rollback()
    finally:
        pg_session.close()

if __name__ == "__main__":
    print("\n🚀 НАЧАЛО МИГРАЦИИ")
    print("=" * 80)
    
    # Проверяем текущее состояние
    results = check_counts()
    
    # Мигрируем недостающие данные
    if results['price_offers']['missing'] > 0:
        migrate_price_offers()
    
    if results['product_images']['missing'] > 0:
        migrate_product_images()
    
    # Финальная проверка
    print("\n" + "=" * 80)
    print("🎉 ФИНАЛЬНАЯ ПРОВЕРКА")
    print("=" * 80)
    check_counts()

