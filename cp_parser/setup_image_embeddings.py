#!/usr/bin/env python3
"""
Настройка таблицы image_embeddings в pgvector БД
для поиска по изображениям
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Цвета для вывода
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def main():
    print_header("НАСТРОЙКА IMAGE EMBEDDINGS В pgvector БД")
    
    # Получение URL векторной БД
    vector_db_url = os.getenv('VECTOR_DATABASE_URL')
    
    if not vector_db_url:
        print_error("Не найден VECTOR_DATABASE_URL")
        print_info("Добавь в .env файл:")
        print("VECTOR_DATABASE_URL=postgresql://postgres:Q3Kq3SG...@switchback.proxy.rlwy.net:53625/railway")
        sys.exit(1)
    
    print_info(f"Векторная БД: {vector_db_url[:50]}...")
    
    try:
        # Подключение к pgvector БД
        print_info("\n1️⃣  Подключение к pgvector БД...")
        engine = create_engine(vector_db_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Проверка подключения
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print_success(f"Подключено! PostgreSQL: {version[:50]}...")
            
            # Проверка pgvector
            result = conn.execute(text("""
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname = 'vector'
            """))
            ext_info = result.fetchone()
            
            if ext_info:
                print_success(f"pgvector версия: {ext_info[1]}")
            else:
                print_error("pgvector НЕ установлен!")
                sys.exit(1)
            
            # Создание таблицы image_embeddings
            print_info("\n2️⃣  Создание таблицы image_embeddings...")
            
            # Проверка существования таблицы
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'image_embeddings'
            """))
            
            if result.fetchone():
                print_warning("Таблица image_embeddings уже существует")
                confirm = input(f"\n{YELLOW}Пересоздать таблицу? (все данные будут удалены) (y/n): {RESET}").strip().lower()
                
                if confirm == 'y':
                    conn.execute(text("DROP TABLE IF EXISTS image_embeddings CASCADE"))
                    conn.commit()
                    print_success("Старая таблица удалена")
                else:
                    print_info("Пропускаем создание таблицы")
                    print_header("✅ НАСТРОЙКА ЗАВЕРШЕНА (без изменений)")
                    return
            
            # Создаем таблицу
            conn.execute(text("""
                CREATE TABLE image_embeddings (
                    id SERIAL PRIMARY KEY,
                    
                    -- Связь с основной БД
                    image_id INTEGER NOT NULL UNIQUE,       -- product_images.id
                    product_id INTEGER NOT NULL,            -- products.id
                    
                    -- Векторное представление изображения (pgvector тип!)
                    image_embedding vector(512),            -- CLIP модель = 512 размерность
                    
                    -- Метаданные
                    image_url TEXT,                         -- URL изображения (для проверки)
                    model_version VARCHAR(50) DEFAULT 'clip-vit-base-patch32',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()
            print_success("Таблица image_embeddings создана")
            
            # Создание индекса
            print_info("\n3️⃣  Создание индекса для быстрого поиска...")
            print_info("   Это может занять несколько минут для больших БД...")
            
            try:
                # ivfflat индекс для средних БД
                conn.execute(text("""
                    CREATE INDEX image_embeddings_ivfflat_idx 
                    ON image_embeddings 
                    USING ivfflat (image_embedding vector_cosine_ops)
                    WITH (lists = 100)
                """))
                conn.commit()
                print_success("Индекс ivfflat создан (оптимален для 10K-100K векторов)")
            except Exception as e:
                print_warning(f"Индекс не создан: {e}")
                print_info("   Индекс можно создать позже после загрузки данных")
            
            # Проверка структуры
            print_info("\n4️⃣  Проверка структуры таблицы...")
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'image_embeddings'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print_success("Структура таблицы:")
            for col_name, col_type in columns:
                print(f"   • {col_name}: {col_type}")
            
            # Проверка индексов
            result = conn.execute(text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'image_embeddings'
            """))
            indexes = result.fetchall()
            
            if indexes:
                print_success("\nИндексы:")
                for idx_name, idx_def in indexes:
                    print(f"   • {idx_name}")
        
        print_header("✅ НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
        
        print_info("\n📝 Что дальше:")
        print("1. Запусти: py generate_image_embeddings.py")
        print("   (генерирует embeddings для главных изображений)")
        print("")
        print("2. Интегрируй поиск по изображениям в веб-интерфейс")
        print("")
        print("3. Протестируй загрузку фото и поиск похожих товаров!")
        
    except Exception as e:
        print_error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

