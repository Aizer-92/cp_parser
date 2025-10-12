#!/usr/bin/env python3
"""
Синхронизация URLs изображений с локальной БД на Railway
"""
import sys
from pathlib import Path
from sqlalchemy import text
import psycopg2

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

RAILWAY_URL = 'postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway'

class ImageURLSyncer:
    def __init__(self):
        self.local_db = PostgreSQLManager()
        
    def sync_urls(self):
        """Синхронизирует URLs изображений с локальной БД на Railway"""
        print("=" * 80)
        print("🔄 СИНХРОНИЗАЦИЯ URLs ИЗОБРАЖЕНИЙ НА RAILWAY")
        print("=" * 80)
        
        # Читаем список проектов Шаблона 4
        with open('template_4_perfect_ids.txt', 'r') as f:
            project_ids = [int(line.strip()) for line in f if line.strip()]
        
        print(f"\n📋 Проекты Шаблона 4: {len(project_ids)}")
        
        # Получаем изображения с URLs из локальной БД
        with self.local_db.get_session() as session:
            images = session.execute(text("""
                SELECT 
                    pi.id,
                    pi.image_filename,
                    pi.image_url,
                    p.project_id
                FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id = ANY(:ids)
                AND pi.image_url IS NOT NULL 
                AND pi.image_url != ''
            """), {'ids': project_ids}).fetchall()
        
        print(f"🔍 Найдено изображений с URL в локальной БД: {len(images):,}")
        
        # Подключаемся к Railway
        railway_conn = psycopg2.connect(RAILWAY_URL)
        railway_cursor = railway_conn.cursor()
        
        # Проверяем текущее состояние на Railway
        railway_cursor.execute("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(%s)
            AND pi.image_url IS NOT NULL 
            AND pi.image_url != ''
        """, (project_ids,))
        railway_with_urls = railway_cursor.fetchone()[0]
        
        print(f"📊 На Railway с URL: {railway_with_urls:,}")
        print(f"\n🔄 Начинаю обновление...")
        
        updated_count = 0
        not_found_count = 0
        
        for img_id, filename, url, proj_id in images:
            try:
                # Обновляем по image_filename (уникальный)
                # Убираем условие на пустой URL - обновляем все!
                railway_cursor.execute("""
                    UPDATE product_images pi
                    SET image_url = %s
                    FROM products p
                    WHERE pi.product_id = p.id
                    AND pi.image_filename = %s
                    AND p.project_id = %s
                """, (url, filename, proj_id))
                
                if railway_cursor.rowcount > 0:
                    updated_count += 1
                else:
                    not_found_count += 1
                
                if updated_count % 100 == 0:
                    print(f"   ✅ Обновлено: {updated_count:,}")
                
            except Exception as e:
                print(f"   ❌ Ошибка для {filename}: {e}")
        
        railway_conn.commit()
        
        # Финальная проверка
        railway_cursor.execute("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(%s)
            AND pi.image_url IS NOT NULL 
            AND pi.image_url != ''
        """, (project_ids,))
        final_count = railway_cursor.fetchone()[0]
        
        railway_cursor.close()
        railway_conn.close()
        
        print("")
        print("=" * 80)
        print("📊 РЕЗУЛЬТАТЫ СИНХРОНИЗАЦИИ")
        print("=" * 80)
        print(f"✅ Обновлено:       {updated_count:,}")
        print(f"⚠️  Не найдено:     {not_found_count:,}")
        print(f"📊 Было на Railway: {railway_with_urls:,}")
        print(f"📊 Стало:           {final_count:,}")
        print(f"➕ Добавлено:       {final_count - railway_with_urls:,}")
        print("=" * 80)

if __name__ == '__main__':
    syncer = ImageURLSyncer()
    syncer.sync_urls()


Синхронизация URLs изображений с локальной БД на Railway
"""
import sys
from pathlib import Path
from sqlalchemy import text
import psycopg2

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

RAILWAY_URL = 'postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway'

class ImageURLSyncer:
    def __init__(self):
        self.local_db = PostgreSQLManager()
        
    def sync_urls(self):
        """Синхронизирует URLs изображений с локальной БД на Railway"""
        print("=" * 80)
        print("🔄 СИНХРОНИЗАЦИЯ URLs ИЗОБРАЖЕНИЙ НА RAILWAY")
        print("=" * 80)
        
        # Читаем список проектов Шаблона 4
        with open('template_4_perfect_ids.txt', 'r') as f:
            project_ids = [int(line.strip()) for line in f if line.strip()]
        
        print(f"\n📋 Проекты Шаблона 4: {len(project_ids)}")
        
        # Получаем изображения с URLs из локальной БД
        with self.local_db.get_session() as session:
            images = session.execute(text("""
                SELECT 
                    pi.id,
                    pi.image_filename,
                    pi.image_url,
                    p.project_id
                FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id = ANY(:ids)
                AND pi.image_url IS NOT NULL 
                AND pi.image_url != ''
            """), {'ids': project_ids}).fetchall()
        
        print(f"🔍 Найдено изображений с URL в локальной БД: {len(images):,}")
        
        # Подключаемся к Railway
        railway_conn = psycopg2.connect(RAILWAY_URL)
        railway_cursor = railway_conn.cursor()
        
        # Проверяем текущее состояние на Railway
        railway_cursor.execute("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(%s)
            AND pi.image_url IS NOT NULL 
            AND pi.image_url != ''
        """, (project_ids,))
        railway_with_urls = railway_cursor.fetchone()[0]
        
        print(f"📊 На Railway с URL: {railway_with_urls:,}")
        print(f"\n🔄 Начинаю обновление...")
        
        updated_count = 0
        not_found_count = 0
        
        for img_id, filename, url, proj_id in images:
            try:
                # Обновляем по image_filename (уникальный)
                # Убираем условие на пустой URL - обновляем все!
                railway_cursor.execute("""
                    UPDATE product_images pi
                    SET image_url = %s
                    FROM products p
                    WHERE pi.product_id = p.id
                    AND pi.image_filename = %s
                    AND p.project_id = %s
                """, (url, filename, proj_id))
                
                if railway_cursor.rowcount > 0:
                    updated_count += 1
                else:
                    not_found_count += 1
                
                if updated_count % 100 == 0:
                    print(f"   ✅ Обновлено: {updated_count:,}")
                
            except Exception as e:
                print(f"   ❌ Ошибка для {filename}: {e}")
        
        railway_conn.commit()
        
        # Финальная проверка
        railway_cursor.execute("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(%s)
            AND pi.image_url IS NOT NULL 
            AND pi.image_url != ''
        """, (project_ids,))
        final_count = railway_cursor.fetchone()[0]
        
        railway_cursor.close()
        railway_conn.close()
        
        print("")
        print("=" * 80)
        print("📊 РЕЗУЛЬТАТЫ СИНХРОНИЗАЦИИ")
        print("=" * 80)
        print(f"✅ Обновлено:       {updated_count:,}")
        print(f"⚠️  Не найдено:     {not_found_count:,}")
        print(f"📊 Было на Railway: {railway_with_urls:,}")
        print(f"📊 Стало:           {final_count:,}")
        print(f"➕ Добавлено:       {final_count - railway_with_urls:,}")
        print("=" * 80)

if __name__ == '__main__':
    syncer = ImageURLSyncer()
    syncer.sync_urls()

