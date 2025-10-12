#!/usr/bin/env python3
"""
Создание таблицы kp_items для хранения товаров в КП
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def create_kp_items_table():
    """Создает таблицу kp_items в БД"""
    
    db_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URL_PRIVATE')
    
    if not db_url:
        print("❌ Не найден DATABASE_URL")
        sys.exit(1)
    
    print(f"📊 Подключение к БД: {db_url[:50]}...")
    engine = create_engine(db_url, pool_pre_ping=True)
    
    with engine.begin() as conn:
        print("\n1️⃣  Проверка существования таблицы...")
        
        # Проверяем существует ли таблица
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'kp_items'
            )
        """))
        exists = result.scalar()
        
        if exists:
            print("⚠️  Таблица kp_items уже существует")
            confirm = input("Пересоздать? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Отменено")
                return
            
            print("🗑️  Удаляем старую таблицу...")
            conn.execute(text("DROP TABLE IF EXISTS kp_items CASCADE"))
        
        print("\n2️⃣  Создание таблицы kp_items...")
        
        conn.execute(text("""
            CREATE TABLE kp_items (
                id SERIAL PRIMARY KEY,
                
                -- Привязка к сессии пользователя
                session_id VARCHAR(255) NOT NULL,
                
                -- Связь с товаром и конкретным вариантом цены
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                price_offer_id INTEGER NOT NULL REFERENCES price_offers(id) ON DELETE CASCADE,
                
                -- Количество (на будущее, пока всегда 1)
                quantity INTEGER DEFAULT 1,
                
                -- Комментарий пользователя (опционально)
                user_comment TEXT,
                
                -- Метаданные
                added_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                
                -- Уникальность: один вариант цены может быть добавлен только один раз в КП
                UNIQUE(session_id, price_offer_id)
            )
        """))
        
        print("✅ Таблица kp_items создана")
        
        print("\n3️⃣  Создание индексов...")
        
        # Индекс для быстрого выбора всех товаров КП по сессии
        conn.execute(text("""
            CREATE INDEX idx_kp_items_session_id ON kp_items(session_id)
        """))
        
        # Индекс для быстрой проверки "товар в КП?"
        conn.execute(text("""
            CREATE INDEX idx_kp_items_session_price ON kp_items(session_id, price_offer_id)
        """))
        
        print("✅ Индексы созданы")
        
        print("\n4️⃣  Проверка структуры...")
        
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'kp_items'
            ORDER BY ordinal_position
        """))
        
        print("\n📋 Структура таблицы kp_items:")
        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            print(f"   • {row[0]:20s} {row[1]:20s} {nullable}")
    
    print("\n" + "="*80)
    print("✅ ТАБЛИЦА kp_items УСПЕШНО СОЗДАНА!")
    print("="*80)
    print("\n📝 Что дальше:")
    print("1. Создать API эндпоинты (/api/kp/*)")
    print("2. Добавить кнопки 'Добавить в КП' на странице товара")
    print("3. Создать страницу /kp для просмотра КП")
    print()

if __name__ == "__main__":
    create_kp_items_table()

