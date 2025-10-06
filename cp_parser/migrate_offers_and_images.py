#!/usr/bin/env python3
"""
Миграция price_offers и product_images из SQLite в PostgreSQL
С обработкой больших значений тиража и предотвращением дублей
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Database URLs
SQLITE_URL = "sqlite:////Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser/database/commercial_proposals.db"
POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

BATCH_SIZE = 1000

def migrate_price_offers():
    """Миграция price_offers с обработкой больших чисел"""
    print("\n" + "=" * 80)
    print("МИГРАЦИЯ PRICE_OFFERS")
    print("=" * 80)
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    PgSession = sessionmaker(bind=postgres_engine)
    pg_session = PgSession()
    
    try:
        # Проверяем текущее количество в PostgreSQL
        existing_count = pg_session.execute(text("SELECT COUNT(*) FROM price_offers")).scalar()
        print(f"\n📊 Текущее количество в PostgreSQL: {existing_count:,}")
        
        # Получаем максимальный ID из PostgreSQL для продолжения
        max_id = pg_session.execute(text("SELECT COALESCE(MAX(id), 0) FROM price_offers")).scalar()
        print(f"📊 Максимальный ID в PostgreSQL: {max_id}")
        
        # Читаем все данные из SQLite
        print("\n📥 Читаем данные из SQLite...")
        df = pd.read_sql_query("SELECT * FROM price_offers", sqlite_engine)
        total_count = len(df)
        print(f"📊 Всего записей в SQLite: {total_count:,}")
        
        # Фильтруем только новые записи (ID > max_id)
        df_new = df[df['id'] > max_id].copy()
        new_count = len(df_new)
        
        if new_count == 0:
            print("\n✅ Все записи уже мигрированы, новых нет!")
            return
        
        print(f"📊 Новых записей для миграции: {new_count:,}")
        
        # Заменяем NaN на None
        df_new = df_new.where(pd.notna(df_new), None)
        
        # Обрабатываем в батчах
        inserted = 0
        errors = 0
        error_log = []
        
        for start_idx in range(0, new_count, BATCH_SIZE):
            end_idx = min(start_idx + BATCH_SIZE, new_count)
            batch = df_new.iloc[start_idx:end_idx]
            
            print(f"\n📦 Обработка батча {start_idx+1}-{end_idx} из {new_count}...")
            
            for _, row in batch.iterrows():
                try:
                    # Явное приведение quantity к строке для BIGINT
                    quantity_val = None
                    if row['quantity'] is not None:
                        try:
                            quantity_val = int(float(row['quantity']))
                        except (ValueError, TypeError):
                            quantity_val = None
                    
                    insert_query = text("""
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
                    """)
                    
                    pg_session.execute(insert_query, {
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
                    errors += 1
                    error_msg = f"ID {row['id']}, Quantity {row['quantity']}: {str(e)}"
                    if len(error_log) < 10:
                        error_log.append(error_msg)
                    
                    # Откатываем транзакцию для этой записи
                    pg_session.rollback()
                    continue
            
            # Коммитим батч
            try:
                pg_session.commit()
                print(f"✅ Батч закоммичен: +{len(batch)} записей")
            except Exception as e:
                print(f"❌ Ошибка коммита батча: {e}")
                pg_session.rollback()
        
        print("\n" + "=" * 80)
        print(f"✅ Вставлено: {inserted:,} записей")
        print(f"❌ Ошибок: {errors:,}")
        
        if error_log:
            print("\n🔍 Примеры ошибок:")
            for err in error_log[:5]:
                print(f"  - {err}")
        
        # Финальная проверка
        final_count = pg_session.execute(text("SELECT COUNT(*) FROM price_offers")).scalar()
        print(f"\n📊 Итоговое количество в PostgreSQL: {final_count:,}")
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        pg_session.rollback()
    finally:
        pg_session.close()


def migrate_product_images():
    """Миграция product_images"""
    print("\n" + "=" * 80)
    print("МИГРАЦИЯ PRODUCT_IMAGES")
    print("=" * 80)
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    PgSession = sessionmaker(bind=postgres_engine)
    pg_session = PgSession()
    
    try:
        # Проверяем текущее количество в PostgreSQL
        existing_count = pg_session.execute(text("SELECT COUNT(*) FROM product_images")).scalar()
        print(f"\n📊 Текущее количество в PostgreSQL: {existing_count:,}")
        
        # Получаем максимальный ID из PostgreSQL
        max_id = pg_session.execute(text("SELECT COALESCE(MAX(id), 0) FROM product_images")).scalar()
        print(f"📊 Максимальный ID в PostgreSQL: {max_id}")
        
        # Читаем все данные из SQLite
        print("\n📥 Читаем данные из SQLite...")
        df = pd.read_sql_query("SELECT * FROM product_images", sqlite_engine)
        total_count = len(df)
        print(f"📊 Всего записей в SQLite: {total_count:,}")
        
        # Фильтруем только новые записи
        df_new = df[df['id'] > max_id].copy()
        new_count = len(df_new)
        
        if new_count == 0:
            print("\n✅ Все записи уже мигрированы, новых нет!")
            return
        
        print(f"📊 Новых записей для миграции: {new_count:,}")
        
        # Заменяем NaN на None
        df_new = df_new.where(pd.notna(df_new), None)
        
        # Обрабатываем в батчах
        inserted = 0
        errors = 0
        error_log = []
        
        for start_idx in range(0, new_count, BATCH_SIZE):
            end_idx = min(start_idx + BATCH_SIZE, new_count)
            batch = df_new.iloc[start_idx:end_idx]
            
            print(f"\n📦 Обработка батча {start_idx+1}-{end_idx} из {new_count}...")
            
            for _, row in batch.iterrows():
                try:
                    insert_query = text("""
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
                    """)
                    
                    pg_session.execute(insert_query, {
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
                    errors += 1
                    error_msg = f"ID {row['id']}: {str(e)}"
                    if len(error_log) < 10:
                        error_log.append(error_msg)
                    
                    pg_session.rollback()
                    continue
            
            # Коммитим батч
            try:
                pg_session.commit()
                print(f"✅ Батч закоммичен: +{len(batch)} записей")
            except Exception as e:
                print(f"❌ Ошибка коммита батча: {e}")
                pg_session.rollback()
        
        print("\n" + "=" * 80)
        print(f"✅ Вставлено: {inserted:,} записей")
        print(f"❌ Ошибок: {errors:,}")
        
        if error_log:
            print("\n🔍 Примеры ошибок:")
            for err in error_log[:5]:
                print(f"  - {err}")
        
        # Финальная проверка
        final_count = pg_session.execute(text("SELECT COUNT(*) FROM product_images")).scalar()
        print(f"\n📊 Итоговое количество в PostgreSQL: {final_count:,}")
        
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
    
    # Сначала мигрируем price_offers
    migrate_price_offers()
    
    # Затем мигрируем product_images
    migrate_product_images()
    
    print("\n" + "=" * 80)
    print("🎉 МИГРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 80)
