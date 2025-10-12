#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция новых товаров из 97 pending проектов на Railway PostgreSQL
Мигрирует только новые данные:
- 910 товаров
- 2,583 предложения
- 6,618 изображений (уже на облаке)
"""

import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import text
from datetime import datetime
import re
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import PostgreSQLManager

# Railway PostgreSQL URL
RAILWAY_POSTGRESQL_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

class NewProductsMigrator:
    """Мигратор новых товаров из pending проектов на Railway"""
    
    def __init__(self):
        self.local_db = PostgreSQLManager()
        self.railway_url = RAILWAY_POSTGRESQL_URL
        
        # Получаем список pending проектов
        self.project_ids = self._get_pending_project_ids()
        
        logger.info(f"📁 Найдено проектов для миграции: {len(self.project_ids)}")
        logger.info(f"🌐 Railway URL: {self.railway_url}")
    
    def _get_pending_project_ids(self):
        """Получает список project_id из valid_files_list.txt (272 проекта)"""
        valid_list = Path('valid_files_list.txt')  # Используем список ВСЕХ 272 проектов
        if not valid_list.exists():
            raise FileNotFoundError("❌ Файл valid_files_list.txt не найден!")
        
        with open(valid_list, 'r') as f:
            files = [line.strip() for line in f if line.strip()]
        
        project_ids = []
        for filename in files:
            match = re.search(r'project_(\d+)_', filename)
            if match:
                project_ids.append(int(match.group(1)))
        
        return project_ids
    
    def test_railway_connection(self):
        """Тестирует подключение к Railway PostgreSQL"""
        logger.info("🔌 Тестирую подключение к Railway...")
        
        try:
            conn = psycopg2.connect(self.railway_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"✅ Railway PostgreSQL: {version[0][:50]}...")
            
            # Проверяем существование таблиц
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            logger.info(f"✅ Найдено таблиц: {len(tables)}")
            
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Railway: {e}")
            return False
    
    def get_local_stats(self):
        """Получает статистику из локальной БД"""
        logger.info("📊 Получаю статистику из локальной БД...")
        
        with self.local_db.get_session() as session:
            placeholders = ','.join([f':{i}' for i in range(len(self.project_ids))])
            params = {str(i): pid for i, pid in enumerate(self.project_ids)}
            
            # Товары
            products_count = session.execute(text(f"""
                SELECT COUNT(*) FROM products WHERE project_id IN ({placeholders})
            """), params).scalar()
            
            # Предложения
            offers_count = session.execute(text(f"""
                SELECT COUNT(*) FROM price_offers po
                JOIN products p ON po.product_id = p.id
                WHERE p.project_id IN ({placeholders})
            """), params).scalar()
            
            # Изображения
            images_count = session.execute(text(f"""
                SELECT COUNT(*) FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id IN ({placeholders})
            """), params).scalar()
            
            # Проекты
            projects_count = session.execute(text(f"""
                SELECT COUNT(*) FROM projects WHERE id IN ({placeholders})
            """), params).scalar()
            
            return {
                'projects': projects_count,
                'products': products_count,
                'offers': offers_count,
                'images': images_count
            }
    
    def migrate_projects(self, railway_conn):
        """Мигрирует проекты"""
        logger.info("📦 Мигрирую проекты...")
        
        railway_cursor = railway_conn.cursor()
        migrated = 0
        skipped = 0
        
        with self.local_db.get_session() as local_session:
            placeholders = ','.join([f':{i}' for i in range(len(self.project_ids))])
            params = {str(i): pid for i, pid in enumerate(self.project_ids)}
            
            projects = local_session.execute(text(f"""
                SELECT id, table_id, project_name, google_sheets_url, parsing_status, 
                       parsed_at, created_at, updated_at
                FROM projects WHERE id IN ({placeholders})
            """), params).fetchall()
            
            for project in projects:
                try:
                    # Проверяем, есть ли уже этот проект
                    railway_cursor.execute("""
                        SELECT id FROM projects WHERE id = %s
                    """, (project[0],))
                    
                    if railway_cursor.fetchone():
                        skipped += 1
                        continue
                    
                    # Вставляем проект (только основные поля)
                    railway_cursor.execute("""
                        INSERT INTO projects (
                            id, table_id, project_name, google_sheets_url, parsing_status, 
                            parsed_at, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        project[0], project[1], project[2], project[3], project[4],
                        project[5], project[6], project[7]
                    ))
                    migrated += 1
                    
                    if migrated % 10 == 0:
                        railway_conn.commit()
                        logger.info(f"   Проектов: {migrated}/{len(projects)}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка миграции проекта {project[0]}: {e}")
            
            railway_conn.commit()
        
        logger.info(f"✅ Проекты: {migrated} новых, {skipped} пропущено")
        return migrated, skipped
    
    def migrate_products(self, railway_conn):
        """Мигрирует товары"""
        logger.info("📦 Мигрирую товары...")
        
        railway_cursor = railway_conn.cursor()
        migrated = 0
        skipped = 0
        
        with self.local_db.get_session() as local_session:
            placeholders = ','.join([f':{i}' for i in range(len(self.project_ids))])
            params = {str(i): pid for i, pid in enumerate(self.project_ids)}
            
            products = local_session.execute(text(f"""
                SELECT id, project_id, name, description, custom_field,
                       created_at, updated_at
                FROM products WHERE project_id IN ({placeholders})
                ORDER BY id
            """), params).fetchall()
            
            logger.info(f"   Всего товаров для миграции: {len(products)}")
            
            for product in products:
                try:
                    # Проверяем, есть ли уже этот товар
                    railway_cursor.execute("""
                        SELECT id FROM products WHERE id = %s
                    """, (product[0],))
                    
                    if railway_cursor.fetchone():
                        skipped += 1
                        continue
                    
                    # Вставляем товар
                    railway_cursor.execute("""
                        INSERT INTO products (
                            id, project_id, name, description, custom_field,
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        product[0], product[1], product[2], product[3],
                        product[4], product[5], product[6]
                    ))
                    migrated += 1
                    
                    if migrated % 100 == 0:
                        railway_conn.commit()
                        logger.info(f"   Товаров: {migrated}/{len(products)}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка миграции товара {product[0]}: {e}")
            
            railway_conn.commit()
        
        logger.info(f"✅ Товары: {migrated} новых, {skipped} пропущено")
        return migrated, skipped
    
    def migrate_price_offers(self, railway_conn):
        """Мигрирует предложения"""
        logger.info("💰 Мигрирую предложения...")
        
        railway_cursor = railway_conn.cursor()
        migrated = 0
        skipped = 0
        
        with self.local_db.get_session() as local_session:
            placeholders = ','.join([f':{i}' for i in range(len(self.project_ids))])
            params = {str(i): pid for i, pid in enumerate(self.project_ids)}
            
            offers = local_session.execute(text(f"""
                SELECT po.id, po.product_id, po.quantity, po.price_usd, po.price_rub,
                       po.route, po.delivery_time_days, po.created_at, po.updated_at
                FROM price_offers po
                JOIN products p ON po.product_id = p.id
                WHERE p.project_id IN ({placeholders})
                ORDER BY po.id
            """), params).fetchall()
            
            logger.info(f"   Всего предложений для миграции: {len(offers)}")
            
            for offer in offers:
                try:
                    # Проверяем, есть ли уже это предложение
                    railway_cursor.execute("""
                        SELECT id FROM price_offers WHERE id = %s
                    """, (offer[0],))
                    
                    if railway_cursor.fetchone():
                        skipped += 1
                        continue
                    
                    # Вставляем предложение
                    railway_cursor.execute("""
                        INSERT INTO price_offers (
                            id, product_id, quantity, price_usd, price_rub,
                            route, delivery_time_days, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        offer[0], offer[1], offer[2], offer[3], offer[4],
                        offer[5], offer[6], offer[7], offer[8]
                    ))
                    migrated += 1
                    
                    if migrated % 500 == 0:
                        railway_conn.commit()
                        logger.info(f"   Предложений: {migrated}/{len(offers)}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка миграции предложения {offer[0]}: {e}")
            
            railway_conn.commit()
        
        logger.info(f"✅ Предложения: {migrated} новых, {skipped} пропущено")
        return migrated, skipped
    
    def migrate_product_images(self, railway_conn):
        """Мигрирует изображения (только метаданные, файлы уже на облаке)"""
        logger.info("🖼️  Мигрирую изображения...")
        
        railway_cursor = railway_conn.cursor()
        migrated = 0
        skipped = 0
        
        with self.local_db.get_session() as local_session:
            placeholders = ','.join([f':{i}' for i in range(len(self.project_ids))])
            params = {str(i): pid for i, pid in enumerate(self.project_ids)}
            
            images = local_session.execute(text(f"""
                SELECT pi.id, pi.product_id, pi.table_id, pi.image_filename,
                       pi.image_url, pi.cell_position, pi.row_number, pi.column_number,
                       pi.created_at, pi.updated_at
                FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id IN ({placeholders})
                ORDER BY pi.id
            """), params).fetchall()
            
            logger.info(f"   Всего изображений для миграции: {len(images)}")
            
            for image in images:
                try:
                    # Проверяем, есть ли уже это изображение
                    railway_cursor.execute("""
                        SELECT id FROM product_images WHERE id = %s
                    """, (image[0],))
                    
                    if railway_cursor.fetchone():
                        skipped += 1
                        continue
                    
                    # Вставляем изображение
                    railway_cursor.execute("""
                        INSERT INTO product_images (
                            id, product_id, table_id, image_filename, image_url,
                            cell_position, row_number, column_number,
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        image[0], image[1], image[2], image[3], image[4],
                        image[5], image[6], image[7], image[8], image[9]
                    ))
                    migrated += 1
                    
                    if migrated % 1000 == 0:
                        railway_conn.commit()
                        logger.info(f"   Изображений: {migrated}/{len(images)}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка миграции изображения {image[0]}: {e}")
            
            railway_conn.commit()
        
        logger.info(f"✅ Изображения: {migrated} новых, {skipped} пропущено")
        return migrated, skipped
    
    def run_migration(self):
        """Запускает полную миграцию"""
        logger.info("🚀 НАЧИНАЮ МИГРАЦИЮ НОВЫХ ТОВАРОВ НА RAILWAY")
        logger.info("=" * 80)
        
        # Проверяем подключение к Railway
        if not self.test_railway_connection():
            logger.error("❌ Ошибка подключения к Railway. Миграция отменена.")
            return False
        
        # Получаем статистику из локальной БД
        local_stats = self.get_local_stats()
        logger.info("\n📊 ЛОКАЛЬНАЯ СТАТИСТИКА:")
        logger.info(f"   • Проекты: {local_stats['projects']}")
        logger.info(f"   • Товары: {local_stats['products']}")
        logger.info(f"   • Предложения: {local_stats['offers']}")
        logger.info(f"   • Изображения: {local_stats['images']}")
        logger.info("")
        
        try:
            # Открываем соединение с Railway
            railway_conn = psycopg2.connect(self.railway_url)
            railway_conn.autocommit = False  # Используем транзакции
            
            results = {}
            
            # 1. Мигрируем проекты
            results['projects'] = self.migrate_projects(railway_conn)
            
            # 2. Мигрируем товары
            results['products'] = self.migrate_products(railway_conn)
            
            # 3. Мигрируем предложения
            results['offers'] = self.migrate_price_offers(railway_conn)
            
            # 4. Мигрируем изображения
            results['images'] = self.migrate_product_images(railway_conn)
            
            railway_conn.close()
            
            # Выводим итоговую статистику
            logger.info("\n" + "=" * 80)
            logger.info("📊 ИТОГОВАЯ СТАТИСТИКА МИГРАЦИИ:")
            logger.info("=" * 80)
            logger.info(f"✅ Проекты: {results['projects'][0]} новых, {results['projects'][1]} пропущено")
            logger.info(f"✅ Товары: {results['products'][0]} новых, {results['products'][1]} пропущено")
            logger.info(f"✅ Предложения: {results['offers'][0]} новых, {results['offers'][1]} пропущено")
            logger.info(f"✅ Изображения: {results['images'][0]} новых, {results['images'][1]} пропущено")
            logger.info("=" * 80)
            logger.info("🎉 МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
            logger.info(f"🌐 Railway URL: {self.railway_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка миграции: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

def main():
    """Основная функция"""
    print("\n" + "=" * 80)
    print("🚀 МИГРАЦИЯ НОВЫХ ТОВАРОВ НА RAILWAY POSTGRESQL")
    print("=" * 80)
    print("\n📦 Что будет мигрировано:")
    print("   • 272 проекта")
    print("   • 910 товаров")
    print("   • 2,583 предложения")
    print("   • 6,618 изображений (метаданные, файлы уже на FTP)")
    print("\n⚠️  Внимание: Дубликаты будут пропущены автоматически")
    print("\n" + "=" * 80)
    
    try:
        migrator = NewProductsMigrator()
        success = migrator.run_migration()
        
        if success:
            print("\n✅ Миграция завершена успешно!")
            print("🌐 Данные доступны на Railway PostgreSQL")
        else:
            print("\n❌ Миграция завершена с ошибками!")
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()


"""
Миграция новых товаров из 97 pending проектов на Railway PostgreSQL
Мигрирует только новые данные:
- 910 товаров
- 2,583 предложения
- 6,618 изображений (уже на облаке)
"""

import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import text
from datetime import datetime
import re
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import PostgreSQLManager

# Railway PostgreSQL URL
RAILWAY_POSTGRESQL_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

class NewProductsMigrator:
    """Мигратор новых товаров из pending проектов на Railway"""
    
    def __init__(self):
        self.local_db = PostgreSQLManager()
        self.railway_url = RAILWAY_POSTGRESQL_URL
        
        # Получаем список pending проектов
        self.project_ids = self._get_pending_project_ids()
        
        logger.info(f"📁 Найдено проектов для миграции: {len(self.project_ids)}")
        logger.info(f"🌐 Railway URL: {self.railway_url}")
    
    def _get_pending_project_ids(self):
        """Получает список project_id из valid_files_list.txt (272 проекта)"""
        valid_list = Path('valid_files_list.txt')  # Используем список ВСЕХ 272 проектов
        if not valid_list.exists():
            raise FileNotFoundError("❌ Файл valid_files_list.txt не найден!")
        
        with open(valid_list, 'r') as f:
            files = [line.strip() for line in f if line.strip()]
        
        project_ids = []
        for filename in files:
            match = re.search(r'project_(\d+)_', filename)
            if match:
                project_ids.append(int(match.group(1)))
        
        return project_ids
    
    def test_railway_connection(self):
        """Тестирует подключение к Railway PostgreSQL"""
        logger.info("🔌 Тестирую подключение к Railway...")
        
        try:
            conn = psycopg2.connect(self.railway_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"✅ Railway PostgreSQL: {version[0][:50]}...")
            
            # Проверяем существование таблиц
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            logger.info(f"✅ Найдено таблиц: {len(tables)}")
            
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Railway: {e}")
            return False
    
    def get_local_stats(self):
        """Получает статистику из локальной БД"""
        logger.info("📊 Получаю статистику из локальной БД...")
        
        with self.local_db.get_session() as session:
            placeholders = ','.join([f':{i}' for i in range(len(self.project_ids))])
            params = {str(i): pid for i, pid in enumerate(self.project_ids)}
            
            # Товары
            products_count = session.execute(text(f"""
                SELECT COUNT(*) FROM products WHERE project_id IN ({placeholders})
            """), params).scalar()
            
            # Предложения
            offers_count = session.execute(text(f"""
                SELECT COUNT(*) FROM price_offers po
                JOIN products p ON po.product_id = p.id
                WHERE p.project_id IN ({placeholders})
            """), params).scalar()
            
            # Изображения
            images_count = session.execute(text(f"""
                SELECT COUNT(*) FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id IN ({placeholders})
            """), params).scalar()
            
            # Проекты
            projects_count = session.execute(text(f"""
                SELECT COUNT(*) FROM projects WHERE id IN ({placeholders})
            """), params).scalar()
            
            return {
                'projects': projects_count,
                'products': products_count,
                'offers': offers_count,
                'images': images_count
            }
    
    def migrate_projects(self, railway_conn):
        """Мигрирует проекты"""
        logger.info("📦 Мигрирую проекты...")
        
        railway_cursor = railway_conn.cursor()
        migrated = 0
        skipped = 0
        
        with self.local_db.get_session() as local_session:
            placeholders = ','.join([f':{i}' for i in range(len(self.project_ids))])
            params = {str(i): pid for i, pid in enumerate(self.project_ids)}
            
            projects = local_session.execute(text(f"""
                SELECT id, table_id, project_name, google_sheets_url, parsing_status, 
                       parsed_at, created_at, updated_at
                FROM projects WHERE id IN ({placeholders})
            """), params).fetchall()
            
            for project in projects:
                try:
                    # Проверяем, есть ли уже этот проект
                    railway_cursor.execute("""
                        SELECT id FROM projects WHERE id = %s
                    """, (project[0],))
                    
                    if railway_cursor.fetchone():
                        skipped += 1
                        continue
                    
                    # Вставляем проект (только основные поля)
                    railway_cursor.execute("""
                        INSERT INTO projects (
                            id, table_id, project_name, google_sheets_url, parsing_status, 
                            parsed_at, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        project[0], project[1], project[2], project[3], project[4],
                        project[5], project[6], project[7]
                    ))
                    migrated += 1
                    
                    if migrated % 10 == 0:
                        railway_conn.commit()
                        logger.info(f"   Проектов: {migrated}/{len(projects)}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка миграции проекта {project[0]}: {e}")
            
            railway_conn.commit()
        
        logger.info(f"✅ Проекты: {migrated} новых, {skipped} пропущено")
        return migrated, skipped
    
    def migrate_products(self, railway_conn):
        """Мигрирует товары"""
        logger.info("📦 Мигрирую товары...")
        
        railway_cursor = railway_conn.cursor()
        migrated = 0
        skipped = 0
        
        with self.local_db.get_session() as local_session:
            placeholders = ','.join([f':{i}' for i in range(len(self.project_ids))])
            params = {str(i): pid for i, pid in enumerate(self.project_ids)}
            
            products = local_session.execute(text(f"""
                SELECT id, project_id, name, description, custom_field,
                       created_at, updated_at
                FROM products WHERE project_id IN ({placeholders})
                ORDER BY id
            """), params).fetchall()
            
            logger.info(f"   Всего товаров для миграции: {len(products)}")
            
            for product in products:
                try:
                    # Проверяем, есть ли уже этот товар
                    railway_cursor.execute("""
                        SELECT id FROM products WHERE id = %s
                    """, (product[0],))
                    
                    if railway_cursor.fetchone():
                        skipped += 1
                        continue
                    
                    # Вставляем товар
                    railway_cursor.execute("""
                        INSERT INTO products (
                            id, project_id, name, description, custom_field,
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        product[0], product[1], product[2], product[3],
                        product[4], product[5], product[6]
                    ))
                    migrated += 1
                    
                    if migrated % 100 == 0:
                        railway_conn.commit()
                        logger.info(f"   Товаров: {migrated}/{len(products)}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка миграции товара {product[0]}: {e}")
            
            railway_conn.commit()
        
        logger.info(f"✅ Товары: {migrated} новых, {skipped} пропущено")
        return migrated, skipped
    
    def migrate_price_offers(self, railway_conn):
        """Мигрирует предложения"""
        logger.info("💰 Мигрирую предложения...")
        
        railway_cursor = railway_conn.cursor()
        migrated = 0
        skipped = 0
        
        with self.local_db.get_session() as local_session:
            placeholders = ','.join([f':{i}' for i in range(len(self.project_ids))])
            params = {str(i): pid for i, pid in enumerate(self.project_ids)}
            
            offers = local_session.execute(text(f"""
                SELECT po.id, po.product_id, po.quantity, po.price_usd, po.price_rub,
                       po.route, po.delivery_time_days, po.created_at, po.updated_at
                FROM price_offers po
                JOIN products p ON po.product_id = p.id
                WHERE p.project_id IN ({placeholders})
                ORDER BY po.id
            """), params).fetchall()
            
            logger.info(f"   Всего предложений для миграции: {len(offers)}")
            
            for offer in offers:
                try:
                    # Проверяем, есть ли уже это предложение
                    railway_cursor.execute("""
                        SELECT id FROM price_offers WHERE id = %s
                    """, (offer[0],))
                    
                    if railway_cursor.fetchone():
                        skipped += 1
                        continue
                    
                    # Вставляем предложение
                    railway_cursor.execute("""
                        INSERT INTO price_offers (
                            id, product_id, quantity, price_usd, price_rub,
                            route, delivery_time_days, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        offer[0], offer[1], offer[2], offer[3], offer[4],
                        offer[5], offer[6], offer[7], offer[8]
                    ))
                    migrated += 1
                    
                    if migrated % 500 == 0:
                        railway_conn.commit()
                        logger.info(f"   Предложений: {migrated}/{len(offers)}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка миграции предложения {offer[0]}: {e}")
            
            railway_conn.commit()
        
        logger.info(f"✅ Предложения: {migrated} новых, {skipped} пропущено")
        return migrated, skipped
    
    def migrate_product_images(self, railway_conn):
        """Мигрирует изображения (только метаданные, файлы уже на облаке)"""
        logger.info("🖼️  Мигрирую изображения...")
        
        railway_cursor = railway_conn.cursor()
        migrated = 0
        skipped = 0
        
        with self.local_db.get_session() as local_session:
            placeholders = ','.join([f':{i}' for i in range(len(self.project_ids))])
            params = {str(i): pid for i, pid in enumerate(self.project_ids)}
            
            images = local_session.execute(text(f"""
                SELECT pi.id, pi.product_id, pi.table_id, pi.image_filename,
                       pi.image_url, pi.cell_position, pi.row_number, pi.column_number,
                       pi.created_at, pi.updated_at
                FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id IN ({placeholders})
                ORDER BY pi.id
            """), params).fetchall()
            
            logger.info(f"   Всего изображений для миграции: {len(images)}")
            
            for image in images:
                try:
                    # Проверяем, есть ли уже это изображение
                    railway_cursor.execute("""
                        SELECT id FROM product_images WHERE id = %s
                    """, (image[0],))
                    
                    if railway_cursor.fetchone():
                        skipped += 1
                        continue
                    
                    # Вставляем изображение
                    railway_cursor.execute("""
                        INSERT INTO product_images (
                            id, product_id, table_id, image_filename, image_url,
                            cell_position, row_number, column_number,
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        image[0], image[1], image[2], image[3], image[4],
                        image[5], image[6], image[7], image[8], image[9]
                    ))
                    migrated += 1
                    
                    if migrated % 1000 == 0:
                        railway_conn.commit()
                        logger.info(f"   Изображений: {migrated}/{len(images)}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка миграции изображения {image[0]}: {e}")
            
            railway_conn.commit()
        
        logger.info(f"✅ Изображения: {migrated} новых, {skipped} пропущено")
        return migrated, skipped
    
    def run_migration(self):
        """Запускает полную миграцию"""
        logger.info("🚀 НАЧИНАЮ МИГРАЦИЮ НОВЫХ ТОВАРОВ НА RAILWAY")
        logger.info("=" * 80)
        
        # Проверяем подключение к Railway
        if not self.test_railway_connection():
            logger.error("❌ Ошибка подключения к Railway. Миграция отменена.")
            return False
        
        # Получаем статистику из локальной БД
        local_stats = self.get_local_stats()
        logger.info("\n📊 ЛОКАЛЬНАЯ СТАТИСТИКА:")
        logger.info(f"   • Проекты: {local_stats['projects']}")
        logger.info(f"   • Товары: {local_stats['products']}")
        logger.info(f"   • Предложения: {local_stats['offers']}")
        logger.info(f"   • Изображения: {local_stats['images']}")
        logger.info("")
        
        try:
            # Открываем соединение с Railway
            railway_conn = psycopg2.connect(self.railway_url)
            railway_conn.autocommit = False  # Используем транзакции
            
            results = {}
            
            # 1. Мигрируем проекты
            results['projects'] = self.migrate_projects(railway_conn)
            
            # 2. Мигрируем товары
            results['products'] = self.migrate_products(railway_conn)
            
            # 3. Мигрируем предложения
            results['offers'] = self.migrate_price_offers(railway_conn)
            
            # 4. Мигрируем изображения
            results['images'] = self.migrate_product_images(railway_conn)
            
            railway_conn.close()
            
            # Выводим итоговую статистику
            logger.info("\n" + "=" * 80)
            logger.info("📊 ИТОГОВАЯ СТАТИСТИКА МИГРАЦИИ:")
            logger.info("=" * 80)
            logger.info(f"✅ Проекты: {results['projects'][0]} новых, {results['projects'][1]} пропущено")
            logger.info(f"✅ Товары: {results['products'][0]} новых, {results['products'][1]} пропущено")
            logger.info(f"✅ Предложения: {results['offers'][0]} новых, {results['offers'][1]} пропущено")
            logger.info(f"✅ Изображения: {results['images'][0]} новых, {results['images'][1]} пропущено")
            logger.info("=" * 80)
            logger.info("🎉 МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
            logger.info(f"🌐 Railway URL: {self.railway_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка миграции: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

def main():
    """Основная функция"""
    print("\n" + "=" * 80)
    print("🚀 МИГРАЦИЯ НОВЫХ ТОВАРОВ НА RAILWAY POSTGRESQL")
    print("=" * 80)
    print("\n📦 Что будет мигрировано:")
    print("   • 272 проекта")
    print("   • 910 товаров")
    print("   • 2,583 предложения")
    print("   • 6,618 изображений (метаданные, файлы уже на FTP)")
    print("\n⚠️  Внимание: Дубликаты будут пропущены автоматически")
    print("\n" + "=" * 80)
    
    try:
        migrator = NewProductsMigrator()
        success = migrator.run_migration()
        
        if success:
            print("\n✅ Миграция завершена успешно!")
            print("🌐 Данные доступны на Railway PostgreSQL")
        else:
            print("\n❌ Миграция завершена с ошибками!")
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()

