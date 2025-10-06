#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Миграция базы данных из SQLite в PostgreSQL на Railway
"""

import os
import sys
from pathlib import Path
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Настройки подключения
SQLITE_DB_PATH = "database/commercial_proposals.db"
POSTGRESQL_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

class DatabaseMigrator:
    """Мигрator базы данных из SQLite в PostgreSQL"""
    
    def __init__(self):
        self.sqlite_path = Path(SQLITE_DB_PATH)
        self.postgresql_url = POSTGRESQL_URL
        
        # Проверяем существование SQLite базы
        if not self.sqlite_path.exists():
            raise FileNotFoundError(f"SQLite база не найдена: {self.sqlite_path}")
        
        logger.info(f"📁 SQLite база: {self.sqlite_path}")
        logger.info(f"🌐 PostgreSQL URL: {self.postgresql_url}")
    
    def test_connections(self):
        """Тестирует подключения к обеим базам данных"""
        logger.info("🔌 Тестирую подключения...")
        
        # Тест SQLite
        try:
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            cursor = sqlite_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.info(f"✅ SQLite: найдено {len(tables)} таблиц")
            sqlite_conn.close()
        except Exception as e:
            logger.error(f"❌ Ошибка SQLite: {e}")
            return False
        
        # Тест PostgreSQL
        try:
            postgres_conn = psycopg2.connect(self.postgresql_url)
            cursor = postgres_conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"✅ PostgreSQL: {version[0]}")
            postgres_conn.close()
        except Exception as e:
            logger.error(f"❌ Ошибка PostgreSQL: {e}")
            return False
        
        return True
    
    def get_sqlite_tables(self):
        """Получает список таблиц из SQLite"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return tables
    
    def get_table_schema(self, table_name):
        """Получает схему таблицы из SQLite"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        conn.close()
        return columns
    
    def get_table_data(self, table_name):
        """Получает все данные из таблицы SQLite"""
        conn = sqlite3.connect(self.sqlite_path)
        
        # Читаем данные в DataFrame
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        conn.close()
        return df
    
    def create_postgresql_tables(self):
        """Создает таблицы в PostgreSQL на основе SQLite схемы"""
        logger.info("🏗️  Создаю таблицы в PostgreSQL...")
        
        # Подключаемся к PostgreSQL
        postgres_conn = psycopg2.connect(self.postgresql_url)
        cursor = postgres_conn.cursor()
        
        # Получаем список таблиц из SQLite
        tables = self.get_sqlite_tables()
        
        for table_name in tables:
            logger.info(f"📋 Создаю таблицу: {table_name}")
            
            # Получаем схему таблицы
            columns = self.get_table_schema(table_name)
            
            # Создаем SQL для создания таблицы
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            column_definitions = []
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                
                # Преобразуем типы SQLite в PostgreSQL
                if col_type.upper() == 'INTEGER':
                    pg_type = 'INTEGER'
                elif col_type.upper() == 'TEXT':
                    pg_type = 'TEXT'
                elif col_type.upper() == 'REAL':
                    pg_type = 'REAL'
                elif col_type.upper() == 'BLOB':
                    pg_type = 'BYTEA'
                else:
                    pg_type = 'TEXT'
                
                # Добавляем ограничения
                constraints = []
                if pk:
                    constraints.append('PRIMARY KEY')
                if not_null and not pk:
                    constraints.append('NOT NULL')
                
                constraint_str = ' '.join(constraints)
                column_def = f"{col_name} {pg_type}"
                if constraint_str:
                    column_def += f" {constraint_str}"
                
                column_definitions.append(column_def)
            
            create_sql += ", ".join(column_definitions) + ");"
            
            try:
                cursor.execute(create_sql)
                logger.info(f"✅ Таблица {table_name} создана")
            except Exception as e:
                logger.error(f"❌ Ошибка создания таблицы {table_name}: {e}")
        
        postgres_conn.commit()
        postgres_conn.close()
    
    def migrate_data(self):
        """Мигрирует данные из SQLite в PostgreSQL"""
        logger.info("📦 Мигрирую данные...")
        
        # Получаем список таблиц
        tables = self.get_sqlite_tables()
        
        total_records = 0
        
        for table_name in tables:
            logger.info(f"📋 Мигрирую таблицу: {table_name}")
            
            # Создаем новое подключение для каждой таблицы
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            postgres_conn = psycopg2.connect(self.postgresql_url)
            postgres_cursor = postgres_conn.cursor()
            
            try:
                # Получаем данные из SQLite
                df = self.get_table_data(table_name)
                
                if df.empty:
                    logger.info(f"⚠️  Таблица {table_name} пуста")
                    continue
                
                # Получаем названия колонок
                columns = list(df.columns)
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                
                # Проверяем, есть ли уже данные в PostgreSQL
                postgres_cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                existing_count = postgres_cursor.fetchone()[0]
                
                if existing_count > 0:
                    logger.info(f"⚠️  В таблице {table_name} уже есть {existing_count} записей, пропускаю")
                    continue
                
                # Вставляем данные
                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                records_inserted = 0
                errors_count = 0
                
                for _, row in df.iterrows():
                    try:
                        # Преобразуем NaN в None
                        values = [None if pd.isna(val) else val for val in row.values]
                        postgres_cursor.execute(insert_sql, values)
                        records_inserted += 1
                    except Exception as e:
                        errors_count += 1
                        if errors_count <= 5:  # Показываем только первые 5 ошибок
                            logger.error(f"❌ Ошибка вставки записи в {table_name}: {e}")
                            logger.error(f"   Значения: {values}")
                        elif errors_count == 6:
                            logger.error(f"❌ ... и еще ошибки в {table_name} (показываю только первые 5)")
                
                # Коммитим изменения для этой таблицы
                postgres_conn.commit()
                
                logger.info(f"✅ {table_name}: {records_inserted} записей, {errors_count} ошибок")
                total_records += records_inserted
                
            except Exception as e:
                logger.error(f"❌ Критическая ошибка в таблице {table_name}: {e}")
                postgres_conn.rollback()
            
            finally:
                # Закрываем подключения для этой таблицы
                postgres_conn.close()
                sqlite_conn.close()
        
        logger.info(f"📊 Всего мигрировано записей: {total_records}")
    
    def verify_migration(self):
        """Проверяет успешность миграции"""
        logger.info("🔍 Проверяю миграцию...")
        
        # Подключаемся к обеим базам
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        postgres_conn = psycopg2.connect(self.postgresql_url)
        postgres_cursor = postgres_conn.cursor()
        
        tables = self.get_sqlite_tables()
        
        for table_name in tables:
            # Считаем записи в SQLite
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            # Считаем записи в PostgreSQL
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            postgres_count = postgres_cursor.fetchone()[0]
            
            if sqlite_count == postgres_count:
                logger.info(f"✅ {table_name}: {sqlite_count} записей (совпадает)")
            else:
                logger.warning(f"⚠️  {table_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
        
        postgres_conn.close()
        sqlite_conn.close()
    
    def run_migration(self):
        """Запускает полную миграцию"""
        logger.info("🚀 НАЧИНАЮ МИГРАЦИЮ БАЗЫ ДАННЫХ")
        logger.info("=" * 60)
        
        # Тестируем подключения
        if not self.test_connections():
            logger.error("❌ Ошибка подключений. Миграция отменена.")
            return False
        
        try:
            # Создаем таблицы
            self.create_postgresql_tables()
            
            # Мигрируем данные
            self.migrate_data()
            
            # Проверяем миграцию
            self.verify_migration()
            
            logger.info("🎉 МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка миграции: {e}")
            return False

def main():
    """Основная функция"""
    print("🔄 Мигрator базы данных SQLite → PostgreSQL")
    print("=" * 60)
    
    try:
        migrator = DatabaseMigrator()
        success = migrator.run_migration()
        
        if success:
            print("\n✅ Миграция завершена успешно!")
            print(f"🌐 PostgreSQL URL: {POSTGRESQL_URL}")
            print("📝 Обновите конфигурацию веб-интерфейса для использования PostgreSQL")
        else:
            print("\n❌ Миграция завершена с ошибками!")
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
