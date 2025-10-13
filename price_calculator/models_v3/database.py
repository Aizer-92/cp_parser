"""
Database configuration and session management for SQLAlchemy
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from .base import Base

# Database URL detection (Railway PostgreSQL or local SQLite)
def get_database_url() -> str:
    """Get database URL from environment or default to SQLite"""
    # Try Railway public URL first
    for url_env in ['DATABASE_PUBLIC_URL', 'DATABASE_URL']:
        database_url = os.environ.get(url_env)
        if database_url:
            print(f"✅ Using PostgreSQL from {url_env}")
            return database_url
    
    # Fallback to SQLite
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'calculations_v3.db')
    sqlite_url = f'sqlite:///{db_path}'
    print(f"✅ Using SQLite: {db_path}")
    return sqlite_url

# Create engine
DATABASE_URL = get_database_url()

# Engine configuration
if DATABASE_URL.startswith('postgresql'):
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,  # Disable connection pooling for Railway
        echo=False,  # Set to True for SQL debugging
        connect_args={
            'connect_timeout': 10,
            'options': '-c timezone=utc'
        }
    )
else:
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={'check_same_thread': False}
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session
    
    Usage in FastAPI:
        @app.get("/api/v3/positions")
        def get_positions(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def drop_all_tables():
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All tables dropped")


