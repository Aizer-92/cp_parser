#!/usr/bin/env python3
"""
Проверка данных в PostgreSQL после миграции
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# PostgreSQL connection
POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

def check_data():
    """Проверяем количество записей в каждой таблице"""
    engine = create_engine(POSTGRES_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("=" * 80)
        print("ПРОВЕРКА ДАННЫХ В POSTGRESQL")
        print("=" * 80)
        
        # Проверяем projects
        projects_count = session.execute(text("SELECT COUNT(*) FROM projects")).scalar()
        print(f"\n✓ Projects: {projects_count:,} записей")
        
        if projects_count > 0:
            sample = session.execute(text("SELECT id, project_name, table_id FROM projects LIMIT 3")).fetchall()
            print("  Примеры:")
            for row in sample:
                print(f"    ID: {row[0]}, Name: {row[1][:50]}, Table ID: {row[2]}")
        
        # Проверяем products
        products_count = session.execute(text("SELECT COUNT(*) FROM products")).scalar()
        print(f"\n✓ Products: {products_count:,} записей")
        
        if products_count > 0:
            sample = session.execute(text("SELECT id, name, project_id FROM products LIMIT 3")).fetchall()
            print("  Примеры:")
            for row in sample:
                print(f"    ID: {row[0]}, Name: {row[1][:50]}, Project ID: {row[2]}")
        
        # Проверяем price_offers
        offers_count = session.execute(text("SELECT COUNT(*) FROM price_offers")).scalar()
        print(f"\n✓ Price Offers: {offers_count:,} записей")
        
        if offers_count > 0:
            sample = session.execute(text("SELECT id, product_id, quantity FROM price_offers LIMIT 3")).fetchall()
            print("  Примеры:")
            for row in sample:
                print(f"    ID: {row[0]}, Product ID: {row[1]}, Quantity: {row[2]}")
        
        # Проверяем product_images
        images_count = session.execute(text("SELECT COUNT(*) FROM product_images")).scalar()
        print(f"\n✓ Product Images: {images_count:,} записей")
        
        if images_count > 0:
            sample = session.execute(text("SELECT id, product_id, image_filename FROM product_images LIMIT 3")).fetchall()
            print("  Примеры:")
            for row in sample:
                print(f"    ID: {row[0]}, Product ID: {row[1]}, Image: {row[2]}")
        
        print("\n" + "=" * 80)
        print("ИТОГО:")
        print(f"  Projects: {projects_count:,}")
        print(f"  Products: {products_count:,}")
        print(f"  Price Offers: {offers_count:,}")
        print(f"  Product Images: {images_count:,}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Ошибка при проверке данных: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_data()
