#!/usr/bin/env python3
"""
Скрипт настройки pgvector БД:
1. Устанавливает pgvector расширение
2. Создает таблицу product_embeddings
3. Создает индекс для быстрого поиска
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
    print_header("НАСТРОЙКА pgvector БД")
    
    # Получение URL векторной БД
    vector_db_url = os.getenv('VECTOR_DATABASE_URL')
    
    if not vector_db_url:
        print_error("Не найден VECTOR_DATABASE_URL")
        print_info("Добавь в .env файл:")
        print("VECTOR_DATABASE_URL=postgresql://postgres:Q3Kq3SG.LCSQYpWcc333JlUpsUfJOxfG@switchback.proxy.rlwy.net:53625/railway")
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
            
            # 1. Установка pgvector расширения
            print_info("\n2️⃣  Установка pgvector расширения...")
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                print_success("pgvector расширение установлено")
            except Exception as e:
                print_warning(f"pgvector уже установлен или ошибка: {e}")
            
            # Проверка установки
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
            
            # 2. Создание таблицы product_embeddings
            print_info("\n3️⃣  Создание таблицы product_embeddings...")
            
            # Проверка существования таблицы
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'product_embeddings'
            """))
            
            if result.fetchone():
                print_warning("Таблица product_embeddings уже существует")
                confirm = input(f"\n{YELLOW}Пересоздать таблицу? (все данные будут удалены) (y/n): {RESET}").strip().lower()
                
                if confirm == 'y':
                    conn.execute(text("DROP TABLE IF EXISTS product_embeddings CASCADE"))
                    conn.commit()
                    print_success("Старая таблица удалена")
                else:
                    print_info("Пропускаем создание таблицы")
                    # Проверяем индекс
                    print_info("\n4️⃣  Проверка индекса...")
                    result = conn.execute(text("""
                        SELECT indexname 
                        FROM pg_indexes 
                        WHERE tablename = 'product_embeddings'
                    """))
                    indexes = result.fetchall()
                    
                    if indexes:
                        print_success(f"Найдены индексы: {[idx[0] for idx in indexes]}")
                    else:
                        print_warning("Индексы не найдены")
                    
                    print_header("✅ НАСТРОЙКА ЗАВЕРШЕНА (без изменений)")
                    return
            
            # Создаем таблицу
            conn.execute(text("""
                CREATE TABLE product_embeddings (
                    id SERIAL PRIMARY KEY,
                    
                    -- Связь с основной БД
                    product_id INTEGER NOT NULL UNIQUE,
                    
                    -- Векторное представление (pgvector тип!)
                    name_embedding vector(1536),
                    
                    -- Метаданные
                    product_name TEXT,
                    model_version VARCHAR(50) DEFAULT 'text-embedding-3-small',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()
            print_success("Таблица product_embeddings создана")
            
            # 3. Создание индекса
            print_info("\n4️⃣  Создание индекса для быстрого поиска...")
            print_info("   Это может занять несколько минут для больших БД...")
            
            try:
                # ivfflat индекс для средних БД (10K-100K записей)
                conn.execute(text("""
                    CREATE INDEX product_embeddings_ivfflat_idx 
                    ON product_embeddings 
                    USING ivfflat (name_embedding vector_cosine_ops)
                    WITH (lists = 100)
                """))
                conn.commit()
                print_success("Индекс ivfflat создан (оптимален для 10K-100K векторов)")
            except Exception as e:
                print_warning(f"Индекс не создан: {e}")
                print_info("   Индекс можно создать позже после загрузки данных")
            
            # Проверка структуры
            print_info("\n5️⃣  Проверка структуры таблицы...")
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'product_embeddings'
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
                WHERE tablename = 'product_embeddings'
            """))
            indexes = result.fetchall()
            
            if indexes:
                print_success("\nИндексы:")
                for idx_name, idx_def in indexes:
                    print(f"   • {idx_name}")
            
            # Тестовый запрос
            print_info("\n6️⃣  Тестовый запрос...")
            try:
                # Вставляем тестовую запись
                test_embedding = [0.1] * 1536  # Тестовый вектор
                conn.execute(text("""
                    INSERT INTO product_embeddings 
                        (product_id, product_name, name_embedding, model_version)
                    VALUES 
                        (-1, 'TEST PRODUCT', :embedding, 'test')
                """), {"embedding": test_embedding})
                conn.commit()
                
                # Тестовый поиск
                result = conn.execute(text("""
                    SELECT product_id, product_name,
                           1 - (name_embedding <=> :query) as similarity
                    FROM product_embeddings
                    WHERE product_id = -1
                """), {"query": test_embedding})
                
                test_row = result.fetchone()
                if test_row:
                    print_success(f"Тестовый поиск работает! Similarity: {test_row[2]:.3f}")
                
                # Удаляем тестовую запись
                conn.execute(text("DELETE FROM product_embeddings WHERE product_id = -1"))
                conn.commit()
                
            except Exception as e:
                print_warning(f"Тестовый запрос не выполнен: {e}")
        
        print_header("✅ НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
        
        print_info("\n📝 Что дальше:")
        print("1. Запусти: py migrate_embeddings_to_pgvector.py")
        print("   (скопирует 13,710 embeddings из основной БД)")
        print("")
        print("2. Модифицируй web_interface/app.py для использования pgvector")
        print("")
        print("3. Протестируй поиск через веб-интерфейс")
        
    except Exception as e:
        print_error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()



