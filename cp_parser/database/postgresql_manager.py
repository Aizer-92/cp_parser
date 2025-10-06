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
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,  # Устанавливаем True для отладки
                use_native_hstore=False,  # Отключаем нативные типы
                connect_args={
                    "options": "-c client_encoding=utf8"
                }
            )
            
            # Регистрируем обработчик для неизвестных типов PostgreSQL
            @event.listens_for(self.engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                # Регистрируем все базовые типы PostgreSQL
                cursor = dbapi_conn.cursor()
                # Выполняем простой запрос для инициализации типов
                cursor.execute("SELECT 1")
                cursor.close()
                
                # Патчим psycopg2 для игнорирования неизвестных типов
                import psycopg2.extensions
                # Регистрируем TEXT (OID 25) как STRING
                psycopg2.extensions.register_type(
                    psycopg2.extensions.new_type((25,), "TEXT", psycopg2.STRING)
                )
            
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
