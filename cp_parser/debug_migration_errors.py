#!/usr/bin/env python3
"""
Диагностика ошибок миграции
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

SQLITE_URL = "sqlite:////Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser/database/commercial_proposals.db"
POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

def test_price_offers_insert():
    """Тестируем вставку одной записи price_offers"""
    print("=" * 80)
    print("ТЕСТ ВСТАВКИ PRICE_OFFERS")
    print("=" * 80)
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    PgSession = sessionmaker(bind=postgres_engine)
    pg_session = PgSession()
    
    try:
        # Получаем максимальный ID
        max_id = pg_session.execute(text("SELECT COALESCE(MAX(id), 0) FROM price_offers")).scalar()
        print(f"\n📊 Максимальный ID в PostgreSQL: {max_id}")
        
        # Берем первые 5 записей после max_id
        df = pd.read_sql_query(f"SELECT * FROM price_offers WHERE id > {max_id} LIMIT 5", sqlite_engine)
        print(f"\n📊 Тестовых записей из SQLite: {len(df)}")
        
        if len(df) == 0:
            print("✅ Нет новых записей для теста")
            return
        
        # Показываем структуру первой записи
        print("\n📋 СТРУКТУРА ПЕРВОЙ ЗАПИСИ:")
        first_row = df.iloc[0]
        for col in df.columns:
            val = first_row[col]
            val_type = type(val).__name__
            print(f"  {col}: {val} ({val_type})")
        
        # Пробуем вставить каждую запись и смотрим ошибки
        print("\n" + "=" * 80)
        print("ПОПЫТКА ВСТАВКИ:")
        print("=" * 80)
        
        for idx, row in df.iterrows():
            print(f"\n🔍 Запись ID {row['id']}:")
            
            try:
                # Обработка quantity
                quantity_val = None
                if pd.notna(row['quantity']):
                    try:
                        quantity_val = int(float(row['quantity']))
                        print(f"  ✓ Quantity: {quantity_val} (обработано)")
                    except Exception as e:
                        print(f"  ⚠ Quantity conversion error: {e}")
                
                # Пробуем вставить
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
                
                pg_session.commit()
                print(f"  ✅ УСПЕШНО вставлено!")
                
            except Exception as e:
                print(f"  ❌ ОШИБКА: {e}")
                print(f"  📝 Тип ошибки: {type(e).__name__}")
                pg_session.rollback()
                
                # Детальная информация об ошибке
                import traceback
                print(f"  📋 Traceback:")
                traceback.print_exc()
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pg_session.close()

def test_product_images_insert():
    """Тестируем вставку одной записи product_images"""
    print("\n" + "=" * 80)
    print("ТЕСТ ВСТАВКИ PRODUCT_IMAGES")
    print("=" * 80)
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    PgSession = sessionmaker(bind=postgres_engine)
    pg_session = PgSession()
    
    try:
        # Получаем максимальный ID
        max_id = pg_session.execute(text("SELECT COALESCE(MAX(id), 0) FROM product_images")).scalar()
        print(f"\n📊 Максимальный ID в PostgreSQL: {max_id}")
        
        # Берем первые 3 записи после max_id
        df = pd.read_sql_query(f"SELECT * FROM product_images WHERE id > {max_id} LIMIT 3", sqlite_engine)
        print(f"\n📊 Тестовых записей из SQLite: {len(df)}")
        
        if len(df) == 0:
            print("✅ Нет новых записей для теста")
            return
        
        # Показываем структуру первой записи
        print("\n📋 СТРУКТУРА ПЕРВОЙ ЗАПИСИ:")
        first_row = df.iloc[0]
        for col in df.columns:
            val = first_row[col]
            val_type = type(val).__name__
            print(f"  {col}: {val} ({val_type})")
        
        # Пробуем вставить каждую запись
        print("\n" + "=" * 80)
        print("ПОПЫТКА ВСТАВКИ:")
        print("=" * 80)
        
        for idx, row in df.iterrows():
            print(f"\n🔍 Запись ID {row['id']}:")
            
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
                
                pg_session.commit()
                print(f"  ✅ УСПЕШНО вставлено!")
                
            except Exception as e:
                print(f"  ❌ ОШИБКА: {e}")
                print(f"  📝 Тип ошибки: {type(e).__name__}")
                pg_session.rollback()
                
                # Детальная информация об ошибке
                import traceback
                print(f"  📋 Traceback:")
                traceback.print_exc()
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pg_session.close()

if __name__ == "__main__":
    test_price_offers_insert()
    test_product_images_insert()
