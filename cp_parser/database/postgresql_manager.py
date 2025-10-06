#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Менеджер базы данных PostgreSQL для Railway
"""

import os
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

# Функция для регистрации типов на каждом соединении
def register_pg_types(dbapi_conn, connection_record):
    """Регистрирует TEXT и другие типы PostgreSQL для каждого соединения в пуле"""
    try:
        import psycopg2.extensions
        import psycopg2
        
        # Регистрируем TEXT (OID 25) как STRING для ЭТОГО соединения
        TEXT = psycopg2.extensions.new_type((25,), "TEXT", psycopg2.STRING)
        psycopg2.extensions.register_type(TEXT, dbapi_conn)
        
        # Также регистрируем VARCHAR (OID 1043) на всякий случай
        VARCHAR = psycopg2.extensions.new_type((1043,), "VARCHAR", psycopg2.STRING)
        psycopg2.extensions.register_type(VARCHAR, dbapi_conn)
        
        # Отключаем автоматическую конвертацию типов, которые могут вызывать проблемы
        cursor = dbapi_conn.cursor()
        cursor.execute("SET SESSION client_encoding TO 'UTF8'")
        cursor.close()
        
        logging.info(f"✅ Типы зарегистрированы для соединения {id(dbapi_conn)}")
    except Exception as e:
        logging.error(f"❌ Ошибка регистрации типов для соединения: {e}")

# Настройки PostgreSQL
# Railway предоставляет DATABASE_URL или DATABASE_PUBLIC_URL
POSTGRESQL_URL = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL', "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway")

class PostgreSQLManager:
    """Менеджер базы данных PostgreSQL"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or POSTGRESQL_URL
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Настраивает подключение к PostgreSQL"""
        try:
            # Создаем engine с оптимизациями для Railway
            # КРИТИЧЕСКИ ВАЖНО: Используем специальный URL с параметрами
            # Добавляем ?client_encoding=utf8 в URL для правильной работы с типами
            connection_url = self.database_url
            if '?' not in connection_url:
                connection_url += '?client_encoding=utf8'
            
            self.engine = create_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
                # КРИТИЧЕСКИ ВАЖНО: Отключаем ВСЕ нативные типы PostgreSQL
                use_native_hstore=False,
                # Явно указываем, что НЕ используем prepared statements
                connect_args={
                    "options": "-c client_encoding=utf8",
                },
                # Отключаем автоматическое определение типов
                isolation_level="AUTOCOMMIT"
            )
            
            # Регистрируем обработчик для КАЖДОГО соединения в пуле
            event.listen(self.engine, "connect", register_pg_types)
            logging.info("✅ Обработчик регистрации типов подключен к engine")
            
            # Создаем фабрику сессий
            self.SessionLocal = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )
            )
            
            logging.info("✅ PostgreSQL подключение настроено")
            
        except Exception as e:
            logging.error(f"❌ Ошибка настройки PostgreSQL: {e}")
            raise
    
    def test_connection(self):
        """Тестирует подключение к базе данных"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version();"))
                version = result.fetchone()[0]
                logging.info(f"✅ PostgreSQL подключение работает: {version}")
                return True
        except Exception as e:
            logging.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
            return False
    
    @contextmanager
    def get_session(self):
        """Контекстный менеджер для работы с сессией"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"❌ Ошибка в сессии: {e}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self):
        """Получает сессию напрямую (для совместимости)"""
        return self.SessionLocal()
    
    def close_all_connections(self):
        """Закрывает все подключения"""
        if self.engine:
            self.engine.dispose()
            logging.info("✅ Все подключения к PostgreSQL закрыты")

# Глобальный экземпляр менеджера
postgresql_manager = PostgreSQLManager()

def get_postgresql_manager():
    """Получает глобальный экземпляр менеджера PostgreSQL"""
    return postgresql_manager

# Для совместимости с существующим кодом
db_manager = postgresql_manager
