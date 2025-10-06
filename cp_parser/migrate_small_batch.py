#!/usr/bin/env python3
"""
Миграция маленькими батчами (по 100 записей)
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLITE_URL = "sqlite:////Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser/database/commercial_proposals.db"
POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

def migrate_price_offers_batch(limit=100):
    """Миграция одного батча price_offers"""
    print(f"\n🚀 Миграция price_offers (батч {limit} записей)")
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    pg_session = PgSession()
    
    try:
        # Получаем максимальный ID в PostgreSQL
        max_id = pg_session.execute(text("SELECT COALESCE(MAX(id), 0) FROM price_offers")).scalar()
        print(f"📊 Макс ID в PostgreSQL: {max_id}")
        
        # Читаем батч из SQLite
        rows = sqlite_session.execute(text(f"""
            SELECT * FROM price_offers 
            WHERE id > {max_id} 
            ORDER BY id 
            LIMIT {limit}
        """)).fetchall()
        
        if not rows:
            print("✅ Нет новых записей")
            return 0
        
        print(f"📥 Получено {len(rows)} записей из SQLite")
        
        # Вставляем по одной
        inserted = 0
        errors = 0
        
        for row in rows:
            try:
                # Преобразуем row в dict
                row_dict = dict(row._mapping)
                
                # Обработка quantity
                quantity_val = None
                if row_dict['quantity'] is not None:
                    try:
                        quantity_val = int(float(row_dict['quantity']))
                    except:
                        pass
                
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
                
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  ⚠️ Ошибка ID {row_dict['id']}: {str(e)[:100]}")
        
        pg_session.commit()
        print(f"✅ Вставлено: {inserted}, Ошибок: {errors}")
        
        return inserted
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        pg_session.rollback()
        return 0
    finally:
        sqlite_session.close()
        pg_session.close()

def migrate_product_images_batch(limit=100):
    """Миграция одного батча product_images"""
    print(f"\n🚀 Миграция product_images (батч {limit} записей)")
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    pg_session = PgSession()
    
    try:
        # Получаем максимальный ID в PostgreSQL
        max_id = pg_session.execute(text("SELECT COALESCE(MAX(id), 0) FROM product_images")).scalar()
        print(f"📊 Макс ID в PostgreSQL: {max_id}")
        
        # Читаем батч из SQLite
        rows = sqlite_session.execute(text(f"""
            SELECT * FROM product_images 
            WHERE id > {max_id} 
            ORDER BY id 
            LIMIT {limit}
        """)).fetchall()
        
        if not rows:
            print("✅ Нет новых записей")
            return 0
        
        print(f"📥 Получено {len(rows)} записей из SQLite")
        
        # Вставляем по одной
        inserted = 0
        errors = 0
        
        for row in rows:
            try:
                row_dict = dict(row._mapping)
                
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
                
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  ⚠️ Ошибка ID {row_dict['id']}: {str(e)[:100]}")
        
        pg_session.commit()
        print(f"✅ Вставлено: {inserted}, Ошибок: {errors}")
        
        return inserted
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        pg_session.rollback()
        return 0
    finally:
        sqlite_session.close()
        pg_session.close()

if __name__ == "__main__":
    print("=" * 80)
    print("МИГРАЦИЯ МАЛЕНЬКИМИ БАТЧАМИ")
    print("=" * 80)
    
    # Мигрируем 10 батчей price_offers
    total_offers = 0
    for i in range(10):
        count = migrate_price_offers_batch(100)
        total_offers += count
        if count == 0:
            break
    
    print(f"\n📊 Всего price_offers мигрировано: {total_offers}")
    
    # Мигрируем 10 батчей product_images
    total_images = 0
    for i in range(10):
        count = migrate_product_images_batch(100)
        total_images += count
        if count == 0:
            break
    
    print(f"\n📊 Всего product_images мигрировано: {total_images}")
    print("\n" + "=" * 80)
    print("✅ ГОТОВО!")
    print("=" * 80)

