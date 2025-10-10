#!/usr/bin/env python3
"""
Скрипт для копирования embeddings из локальной БД в Railway БД.

Быстрее чем генерировать заново (~2 минуты vs 50 минут) и не тратит API вызовы.

Использование:
    python3 copy_embeddings_to_railway.py
    
Требования:
    - DATABASE_URL локальной БД (по умолчанию из .env)
    - RAILWAY_DATABASE_URL для production БД
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Загрузка переменных окружения
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


def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_error(text):
    print(f"{RED}❌ {text}{RESET}")


def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")


def main():
    print_header("КОПИРОВАНИЕ EMBEDDINGS В RAILWAY")
    
    # Получение URL баз данных
    local_db_url = os.getenv('DATABASE_URL')
    railway_db_url = os.getenv('RAILWAY_DATABASE_URL')
    
    if not local_db_url:
        print_error("Не найден DATABASE_URL для локальной БД")
        print_info("Добавь в .env файл:")
        print("DATABASE_URL=postgresql://user:password@localhost:5432/dbname")
        sys.exit(1)
    
    if not railway_db_url:
        print_error("Не найден RAILWAY_DATABASE_URL")
        print_info("Добавь в .env файл или экспортируй переменную:")
        print("export RAILWAY_DATABASE_URL='postgresql://...railway.app/railway'")
        print_info("\nПолучить URL можно здесь:")
        print("Railway Dashboard → PostgreSQL → Connect → Connection URL")
        sys.exit(1)
    
    print_info(f"Локальная БД: {local_db_url[:50]}...")
    print_info(f"Railway БД: {railway_db_url[:50]}...")
    
    try:
        # Подключение к локальной БД
        print_info("\n1️⃣  Подключение к локальной БД...")
        local_engine = create_engine(local_db_url)
        
        with local_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(name_embedding_text) as with_embeddings
                FROM products
            """))
            row = result.fetchone()
            total_local = row[0]
            with_embeddings_local = row[1]
        
        print_success(f"Локальная БД: {total_local} товаров, {with_embeddings_local} с embeddings")
        
        if with_embeddings_local == 0:
            print_error("В локальной БД нет embeddings!")
            print_info("Сначала запусти: python3 generate_embeddings_simple.py")
            sys.exit(1)
        
        # Подключение к Railway БД
        print_info("\n2️⃣  Подключение к Railway БД...")
        railway_engine = create_engine(railway_db_url)
        
        with railway_engine.connect() as conn:
            # Проверка существования колонки
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                  AND column_name = 'name_embedding_text'
            """))
            
            if not result.fetchone():
                print_error("Колонка name_embedding_text не существует в Railway БД!")
                print_info("Сначала запусти: python3 setup_embeddings_simple.py")
                print_info("Или выполни SQL:")
                print("ALTER TABLE products ADD COLUMN name_embedding_text TEXT;")
                sys.exit(1)
            
            # Статистика Railway БД
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(name_embedding_text) as with_embeddings
                FROM products
            """))
            row = result.fetchone()
            total_railway = row[0]
            with_embeddings_railway = row[1]
        
        print_success(f"Railway БД: {total_railway} товаров, {with_embeddings_railway} с embeddings")
        
        # Подтверждение
        print_info("\n3️⃣  Готовы к копированию:")
        print(f"   • Из локальной БД: {with_embeddings_local} embeddings")
        print(f"   • В Railway БД: обновить {total_railway} товаров")
        
        if with_embeddings_railway > 0:
            print_warning(f"   • В Railway уже есть {with_embeddings_railway} embeddings (будут перезаписаны)")
        
        confirm = input(f"\n{YELLOW}Продолжить? (y/n): {RESET}").strip().lower()
        
        if confirm != 'y':
            print_info("Отменено пользователем")
            sys.exit(0)
        
        # Экспорт данных из локальной БД
        print_info("\n4️⃣  Экспорт embeddings из локальной БД...")
        
        with local_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name_embedding_text
                FROM products
                WHERE name_embedding_text IS NOT NULL
                ORDER BY id
            """))
            embeddings_data = result.fetchall()
        
        print_success(f"Экспортировано {len(embeddings_data)} embeddings")
        
        # Импорт в Railway БД
        print_info("\n5️⃣  Импорт embeddings в Railway БД...")
        
        updated_count = 0
        batch_size = 100
        
        with railway_engine.begin() as conn:
            for i in range(0, len(embeddings_data), batch_size):
                batch = embeddings_data[i:i + batch_size]
                
                # Batch update
                for product_id, embedding_text in batch:
                    conn.execute(text("""
                        UPDATE products
                        SET name_embedding_text = :embedding
                        WHERE id = :id
                    """), {"id": product_id, "embedding": embedding_text})
                    updated_count += 1
                
                # Progress
                progress = (i + len(batch)) / len(embeddings_data) * 100
                print(f"\r   Обработано: {i + len(batch)}/{len(embeddings_data)} ({progress:.1f}%)", end="")
        
        print()  # Новая строка после progress bar
        print_success(f"Обновлено {updated_count} товаров в Railway БД")
        
        # Финальная проверка
        print_info("\n6️⃣  Проверка результата...")
        
        with railway_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(name_embedding_text) as with_embeddings
                FROM products
            """))
            row = result.fetchone()
            total_final = row[0]
            with_embeddings_final = row[1]
        
        print_success(f"Railway БД после импорта:")
        print(f"   • Всего товаров: {total_final}")
        print(f"   • С embeddings: {with_embeddings_final}")
        print(f"   • Покрытие: {with_embeddings_final / total_final * 100:.1f}%")
        
        print_header("✅ КОПИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        
        print_info("\n📝 Что дальше:")
        print("1. Проверь веб-интерфейс на Railway")
        print("2. Попробуй поиск: 'кружка', 'ручка', 'USB'")
        print("3. Проверь логи Railway на наличие: '✅ Vector search enabled'")
        
    except Exception as e:
        print_error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

