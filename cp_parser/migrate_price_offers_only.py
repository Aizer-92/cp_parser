#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Миграция только таблицы price_offers в PostgreSQL
"""

import sqlite3
import psycopg2
import pandas as pd
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Настройки подключения
SQLITE_DB_PATH = "database/commercial_proposals.db"
POSTGRESQL_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

def migrate_price_offers():
    """Мигрирует только таблицу price_offers"""
    logger.info("📦 Мигрирую таблицу price_offers...")
    
    # Подключаемся к SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    
    # Подключаемся к PostgreSQL
    postgres_conn = psycopg2.connect(POSTGRESQL_URL)
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # Проверяем, есть ли уже данные в PostgreSQL
        postgres_cursor.execute("SELECT COUNT(*) FROM price_offers;")
        existing_count = postgres_cursor.fetchone()[0]
        
        if existing_count > 0:
            logger.info(f"⚠️  В таблице price_offers уже есть {existing_count} записей")
            return
        
        # Получаем данные из SQLite
        df = pd.read_sql_query("SELECT * FROM price_offers", sqlite_conn)
        
        if df.empty:
            logger.info("⚠️  Таблица price_offers пуста в SQLite")
            return
        
        logger.info(f"📊 Найдено {len(df)} записей в SQLite")
        
        # Получаем названия колонок
        columns = list(df.columns)
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        
        # Вставляем данные
        insert_sql = f"INSERT INTO price_offers ({columns_str}) VALUES ({placeholders})"
        
        records_inserted = 0
        errors_count = 0
        
        for _, row in df.iterrows():
            try:
                # Преобразуем NaN в None
                values = [None if pd.isna(val) else val for val in row.values]
                postgres_cursor.execute(insert_sql, values)
                records_inserted += 1
                
                if records_inserted % 100 == 0:
                    logger.info(f"   Обработано: {records_inserted}/{len(df)}")
                    
            except Exception as e:
                errors_count += 1
                if errors_count <= 5:  # Показываем только первые 5 ошибок
                    logger.error(f"❌ Ошибка вставки записи: {e}")
                    logger.error(f"   Значения: {values}")
                elif errors_count == 6:
                    logger.error(f"❌ ... и еще ошибки (показываю только первые 5)")
        
        # Коммитим изменения
        postgres_conn.commit()
        
        logger.info(f"✅ price_offers: {records_inserted} записей, {errors_count} ошибок")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        postgres_conn.rollback()
    
    finally:
        # Закрываем подключения
        postgres_conn.close()
        sqlite_conn.close()

if __name__ == "__main__":
    migrate_price_offers()
