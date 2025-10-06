#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Безопасная миграция базы данных из SQLite в PostgreSQL с защитой от дублирования
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

class SafeDatabaseMigrator:
    """Безопасный мигрator базы данных с защитой от дублирования"""
    
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
                
                # Преобразуем типы SQLite в PostgreSQL с учетом больших чисел
                if col_type.upper() == 'INTEGER':
                    # Используем BIGINT для больших чисел
                    pg_type = 'BIGINT'
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
    
    def migrate_table_safely(self, table_name):
        """Безопасно мигрирует одну таблицу с защитой от дублирования"""
        logger.info(f"📋 Мигрирую таблицу: {table_name}")
        
        # Создаем новое подключение для каждой таблицы
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        postgres_conn = psycopg2.connect(self.postgresql_url)
        postgres_cursor = postgres_conn.cursor()
        
        try:
            # Проверяем, есть ли уже данные в PostgreSQL
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            existing_count = postgres_cursor.fetchone()[0]
            
            if existing_count > 0:
                logger.info(f"⚠️  В таблице {table_name} уже есть {existing_count} записей, пропускаю")
                return {'status': 'skipped', 'count': existing_count}
            
            # Получаем данные из SQLite
            df = self.get_table_data(table_name)
            
            if df.empty:
                logger.info(f"⚠️  Таблица {table_name} пуста")
                return {'status': 'empty', 'count': 0}
            
            # Получаем названия колонок
            columns = list(df.columns)
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            
            # Вставляем данные батчами
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            records_inserted = 0
            errors_count = 0
            batch_size = 100  # Вставляем по 100 записей за раз
            
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                
                try:
                    # Подготавливаем данные для батча
                    batch_data = []
                    for _, row in batch_df.iterrows():
                        values = []
                        for val in row.values:
                            if pd.isna(val):
                                values.append(None)
                            elif isinstance(val, (int, float)) and val > 2147483647:  # Максимальное значение INTEGER
                                # Преобразуем большие числа в строки
                                values.append(str(val))
                            else:
                                values.append(val)
                        batch_data.append(tuple(values))
                    
                    # Вставляем батч
                    postgres_cursor.executemany(insert_sql, batch_data)
                    records_inserted += len(batch_data)
                    
                    # Коммитим каждый батч
                    postgres_conn.commit()
                    
                    if records_inserted % 1000 == 0:
                        logger.info(f"   Обработано: {records_inserted}/{len(df)}")
                        
                except Exception as e:
                    errors_count += 1
                    logger.error(f"❌ Ошибка вставки батча в {table_name}: {e}")
                    postgres_conn.rollback()
                    
                    # Пробуем вставить записи по одной
                    for _, row in batch_df.iterrows():
                        try:
                            values = []
                            for val in row.values:
                                if pd.isna(val):
                                    values.append(None)
                                elif isinstance(val, (int, float)) and val > 2147483647:
                                    values.append(str(val))
                                else:
                                    values.append(val)
                            
                            postgres_cursor.execute(insert_sql, values)
                            records_inserted += 1
                        except Exception as single_error:
                            logger.error(f"❌ Ошибка вставки записи: {single_error}")
                            logger.error(f"   Значения: {values}")
            
            logger.info(f"✅ {table_name}: {records_inserted} записей, {errors_count} ошибок")
            return {'status': 'success', 'count': records_inserted, 'errors': errors_count}
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в таблице {table_name}: {e}")
            postgres_conn.rollback()
            return {'status': 'error', 'count': 0, 'errors': 1}
        
        finally:
            # Закрываем подключения для этой таблицы
            postgres_conn.close()
            sqlite_conn.close()
    
    def run_safe_migration(self):
        """Запускает безопасную миграцию"""
        logger.info("🚀 НАЧИНАЮ БЕЗОПАСНУЮ МИГРАЦИЮ БАЗЫ ДАННЫХ")
        logger.info("=" * 60)
        
        # Тестируем подключения
        if not self.test_connections():
            logger.error("❌ Ошибка подключений. Миграция отменена.")
            return False
        
        try:
            # Создаем таблицы
            self.create_postgresql_tables()
            
            # Получаем список таблиц
            tables = self.get_sqlite_tables()
            
            # Мигрируем каждую таблицу отдельно
            total_records = 0
            results = {}
            
            for table_name in tables:
                result = self.migrate_table_safely(table_name)
                results[table_name] = result
                total_records += result.get('count', 0)
            
            # Выводим итоговую статистику
            logger.info("📊 ИТОГОВАЯ СТАТИСТИКА МИГРАЦИИ:")
            logger.info("=" * 60)
            
            for table_name, result in results.items():
                status = result['status']
                count = result['count']
                errors = result.get('errors', 0)
                
                if status == 'skipped':
                    logger.info(f"⏭️  {table_name}: {count} записей (уже было)")
                elif status == 'empty':
                    logger.info(f"📭 {table_name}: пустая таблица")
                elif status == 'success':
                    logger.info(f"✅ {table_name}: {count} записей, {errors} ошибок")
                else:
                    logger.error(f"❌ {table_name}: ошибка миграции")
            
            logger.info(f"📊 Всего записей: {total_records}")
            logger.info("🎉 БЕЗОПАСНАЯ МИГРАЦИЯ ЗАВЕРШЕНА!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка миграции: {e}")
            return False

def main():
    """Основная функция"""
    print("🔄 Безопасный мигрator базы данных SQLite → PostgreSQL")
    print("=" * 60)
    
    try:
        migrator = SafeDatabaseMigrator()
        success = migrator.run_safe_migration()
        
        if success:
            print("\n✅ Безопасная миграция завершена успешно!")
            print(f"🌐 PostgreSQL URL: {POSTGRESQL_URL}")
            print("📝 Обновите конфигурацию веб-интерфейса для использования PostgreSQL")
        else:
            print("\n❌ Миграция завершена с ошибками!")
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
