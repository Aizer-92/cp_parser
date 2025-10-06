#!/usr/bin/env python3
"""
Полная миграция всех price_offers
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLITE_URL = "sqlite:////Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser/database/commercial_proposals.db"
POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

def migrate_price_offers_continuous():
    """Непрерывная миграция price_offers до конца"""
    print("🚀 ПОЛНАЯ МИГРАЦИЯ PRICE_OFFERS")
    print("=" * 80)
    
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=postgres_engine)
    
    total_inserted = 0
    total_errors = 0
    batch_num = 0
    batch_size = 500
    
    while True:
        batch_num += 1
        sqlite_session = SqliteSession()
        pg_session = PgSession()
        
        try:
            # Получаем максимальный ID
            max_id = pg_session.execute(text("SELECT COALESCE(MAX(id), 0) FROM price_offers")).scalar()
            
            # Читаем батч
            rows = sqlite_session.execute(text(f"""
                SELECT * FROM price_offers 
                WHERE id > {max_id} 
                ORDER BY id 
                LIMIT {batch_size}
            """)).fetchall()
            
            if not rows:
                print(f"\n✅ Миграция завершена!")
                break
            
            # Вставляем
            inserted = 0
            errors = 0
            
            for row in rows:
                try:
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
                    # Откатываем только эту запись
                    pg_session.rollback()
                    pg_session = PgSession()  # Новая сессия
            
            # Коммитим батч
            try:
                pg_session.commit()
                total_inserted += inserted
                total_errors += errors
                
                # Прогресс
                progress = (total_inserted / 21545) * 100 if total_inserted < 21545 else 100
                print(f"Батч #{batch_num}: +{inserted} записей, ошибок: {errors} | Всего: {total_inserted:,} ({progress:.1f}%)")
                
            except Exception as e:
                print(f"❌ Ошибка коммита батча #{batch_num}: {e}")
                pg_session.rollback()
        
        finally:
            sqlite_session.close()
            pg_session.close()
    
    print("\n" + "=" * 80)
    print(f"✅ ИТОГО вставлено: {total_inserted:,}")
    print(f"❌ ИТОГО ошибок: {total_errors:,}")
    print("=" * 80)

if __name__ == "__main__":
    migrate_price_offers_continuous()
