#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Менеджер базы данных PostgreSQL для Railway
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.dialects import postgresql
from contextlib import contextmanager
import logging

# Регистрируем типы PostgreSQL для правильной работы
from sqlalchemy.dialects.postgresql import base as pg_base
pg_base.ischema_names['text'] = postgresql.TEXT

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
                echo=False  # Устанавливаем True для отладки
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
