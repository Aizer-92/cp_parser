#!/usr/bin/env python3
"""
Скрипт миграции текстовых embeddings из основной БД в pgvector БД.

Копирует:
- products.name_embedding_text (JSON TEXT) → product_embeddings.name_embedding (vector)

Процесс:
1. Читает embeddings из основной БД (батчами)
2. Парсит JSON и проверяет размерность
3. Записывает в pgvector БД как vector(1536)
"""

import os
import sys
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import time

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
    print_header("МИГРАЦИЯ EMBEDDINGS: TEXT → pgvector")
    
    # Получение URL баз данных
    main_db_url = (os.getenv('DATABASE_URL_PRIVATE') or 
                   os.getenv('DATABASE_URL') or 
                   os.getenv('DATABASE_PUBLIC_URL'))
    vector_db_url = os.getenv('VECTOR_DATABASE_URL')
    
    if not main_db_url:
        print_error("Не найден DATABASE_URL для основной БД")
        print_info("Проверь .env файл или переменные окружения")
        sys.exit(1)
    
    if not vector_db_url:
        print_error("Не найден VECTOR_DATABASE_URL")
        print_info("Добавь в .env файл:")
        print("VECTOR_DATABASE_URL=postgresql://postgres:Q3Kq3SG...@switchback.proxy.rlwy.net:53625/railway")
        sys.exit(1)
    
    print_info(f"Основная БД: {main_db_url[:50]}...")
    print_info(f"Векторная БД: {vector_db_url[:50]}...")
    
    try:
        # Подключение к основной БД
        print_info("\n1️⃣  Подключение к основной БД...")
        main_engine = create_engine(main_db_url, pool_pre_ping=True)
        
        with main_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(name_embedding_text) as with_embeddings
                FROM products
            """))
            row = result.fetchone()
            total_products = row[0]
            with_embeddings = row[1]
        
        print_success(f"Основная БД: {total_products} товаров, {with_embeddings} с embeddings")
        
        if with_embeddings == 0:
            print_error("В основной БД нет embeddings!")
            print_info("Сначала запусти: py regenerate_embeddings_names_only.py")
            sys.exit(1)
        
        # Подключение к pgvector БД
        print_info("\n2️⃣  Подключение к pgvector БД...")
        vector_engine = create_engine(vector_db_url, pool_pre_ping=True)
        
        with vector_engine.connect() as conn:
            # Проверка существования таблицы
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'product_embeddings'
            """))
            
            if not result.fetchone():
                print_error("Таблица product_embeddings не существует!")
                print_info("Сначала запусти: py setup_pgvector_db.py")
                sys.exit(1)
            
            # Проверка pgvector расширения
            result = conn.execute(text("""
                SELECT extname FROM pg_extension WHERE extname = 'vector'
            """))
            
            if not result.fetchone():
                print_error("pgvector расширение не установлено!")
                print_info("Сначала запусти: py setup_pgvector_db.py")
                sys.exit(1)
            
            # Статистика pgvector БД
            result = conn.execute(text("""
                SELECT COUNT(*) FROM product_embeddings
            """))
            existing_count = result.scalar()
        
        print_success(f"pgvector БД: {existing_count} записей уже есть")
        
        # Подтверждение
        print_info("\n3️⃣  Готовы к миграции:")
        print(f"   • Из основной БД: {with_embeddings} embeddings")
        print(f"   • В pgvector БД: будет добавлено/обновлено")
        
        if existing_count > 0:
            print_warning(f"   • Существующие {existing_count} записей будут обновлены")
        
        confirm = input(f"\n{YELLOW}Продолжить миграцию? (y/n): {RESET}").strip().lower()
        
        if confirm != 'y':
            print_info("Отменено пользователем")
            sys.exit(0)
        
        # Миграция данных
        print_info("\n4️⃣  Копирование embeddings...")
        print_info("   Это может занять 2-5 минут для 13,710 товаров...")
        
        # Читаем из основной БД батчами
        batch_size = 500
        offset = 0
        total_migrated = 0
        total_errors = 0
        total_skipped = 0
        
        start_time = time.time()
        
        while True:
            # Читаем batch
            with main_engine.connect() as conn:
                products = conn.execute(text("""
                    SELECT id, name, name_embedding_text
                    FROM products
                    WHERE name_embedding_text IS NOT NULL
                    ORDER BY id
                    LIMIT :limit OFFSET :offset
                """), {"limit": batch_size, "offset": offset}).fetchall()
            
            if not products:
                break  # Все обработали
            
            print(f"\r   Обрабатываем товары {offset + 1}-{offset + len(products)}...", end="", flush=True)
            
            # Записываем batch в pgvector БД
            with vector_engine.begin() as conn:
                for product_id, product_name, embedding_text in products:
                    try:
                        # Парсим JSON embedding
                        if not embedding_text or embedding_text.strip() == '':
                            total_skipped += 1
                            continue
                        
                        embedding = json.loads(embedding_text)
                        
                        # Проверка размерности
                        if len(embedding) != 1536:
                            print(f"\n   ⚠️  Товар {product_id}: неверная размерность ({len(embedding)})")
                            total_errors += 1
                            continue
                        
                        # Проверка валидности (все числа)
                        if not all(isinstance(x, (int, float)) for x in embedding):
                            print(f"\n   ⚠️  Товар {product_id}: невалидные данные")
                            total_errors += 1
                            continue
                        
                        # Вставка/обновление в pgvector БД
                        conn.execute(text("""
                            INSERT INTO product_embeddings 
                                (product_id, product_name, name_embedding, model_version)
                            VALUES 
                                (:product_id, :product_name, :embedding, :model)
                            ON CONFLICT (product_id) DO UPDATE
                            SET name_embedding = EXCLUDED.name_embedding,
                                product_name = EXCLUDED.product_name,
                                updated_at = NOW()
                        """), {
                            "product_id": product_id,
                            "product_name": product_name[:500] if product_name else "",  # Обрезаем длинные названия
                            "embedding": embedding,  # pgvector принимает list[float]
                            "model": "text-embedding-3-small"
                        })
                        
                        total_migrated += 1
                        
                    except json.JSONDecodeError as e:
                        print(f"\n   ❌ JSON ошибка для товара {product_id}: {e}")
                        total_errors += 1
                        continue
                    except Exception as e:
                        print(f"\n   ❌ Ошибка для товара {product_id}: {e}")
                        total_errors += 1
                        continue
            
            offset += batch_size
            
            # Показываем прогресс каждые 2500 товаров
            if total_migrated % 2500 == 0 and total_migrated > 0:
                elapsed = time.time() - start_time
                rate = total_migrated / elapsed
                remaining = (with_embeddings - total_migrated) / rate if rate > 0 else 0
                print(f"\n   📊 Прогресс: {total_migrated}/{with_embeddings} ({total_migrated/with_embeddings*100:.1f}%) | ETA: {remaining:.0f}с")
        
        elapsed_time = time.time() - start_time
        
        print()  # Новая строка после progress
        print_success(f"Мигрировано {total_migrated} embeddings за {elapsed_time:.1f} сек")
        
        if total_errors > 0:
            print_warning(f"   Ошибок: {total_errors}")
        if total_skipped > 0:
            print_warning(f"   Пропущено (пустые): {total_skipped}")
        
        # Финальная проверка
        print_info("\n5️⃣  Проверка результата...")
        
        with vector_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM product_embeddings
            """))
            final_count = result.scalar()
        
        print_success(f"pgvector БД после миграции:")
        print(f"   • Всего embeddings: {final_count}")
        print(f"   • Покрытие: {final_count / total_products * 100:.1f}% товаров")
        print(f"   • Скорость: {total_migrated / elapsed_time:.0f} embeddings/сек")
        
        # Тестовый поиск
        print_info("\n6️⃣  Тестовый поиск...")
        
        with vector_engine.connect() as conn:
            # Берем случайный embedding для теста
            test_product = conn.execute(text("""
                SELECT product_id, product_name, name_embedding
                FROM product_embeddings
                ORDER BY RANDOM()
                LIMIT 1
            """)).fetchone()
            
            if test_product:
                test_id, test_name, test_emb = test_product
                
                # Ищем похожие (ВЕКТОРНЫЙ ПОИСК!)
                search_start = time.time()
                similar = conn.execute(text("""
                    SELECT product_id, product_name,
                           1 - (name_embedding <=> :query) as similarity
                    FROM product_embeddings
                    WHERE product_id != :exclude_id
                    ORDER BY name_embedding <=> :query
                    LIMIT 5
                """), {
                    "query": test_emb,
                    "exclude_id": test_id
                }).fetchall()
                search_time = time.time() - search_start
                
                print_success(f"Похожие товары для '{test_name}' (поиск за {search_time*1000:.0f}мс):")
                for pid, pname, sim in similar:
                    print(f"   • [{sim:.3f}] {pname}")
        
        print_header("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        
        print_info("\n📝 Что дальше:")
        print("1. Модифицируй web_interface/app.py:")
        print("   - Добавь подключение к VECTOR_DATABASE_URL")
        print("   - Замени vector_search_products на поиск через pgvector")
        print("")
        print("2. Протестируй поиск локально:")
        print("   - Запусти: cd web_interface && py app.py")
        print("   - Попробуй поиск: 'рюкзак', 'кружка', 'ручка'")
        print("   - Проверь скорость (должно быть 0.1-0.5 сек)")
        print("")
        print("3. Если работает хорошо:")
        print("   - Задеплой на Railway")
        print("   - Добавь VECTOR_DATABASE_URL в Railway Variables")
        print("   - Делай image embeddings по тому же принципу!")
        
    except Exception as e:
        print_error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

