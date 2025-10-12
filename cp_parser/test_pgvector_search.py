#!/usr/bin/env python3
"""
Быстрый тест pgvector поиска перед запуском веб-интерфейса
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Цвета
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

print(f"\n{BLUE}{'=' * 80}{RESET}")
print(f"{BLUE}{'ТЕСТ pgvector ПОИСКА'.center(80)}{RESET}")
print(f"{BLUE}{'=' * 80}{RESET}\n")

# Проверка переменных окружения
print("1️⃣  Проверка переменных окружения...")
vector_db = os.getenv('VECTOR_DATABASE_URL')
openai_key = os.getenv('OPENAI_API_KEY')

if not vector_db:
    print(f"{RED}❌ VECTOR_DATABASE_URL не настроен{RESET}")
    sys.exit(1)
else:
    print(f"{GREEN}✅ VECTOR_DATABASE_URL: {vector_db[:50]}...{RESET}")

if not openai_key:
    print(f"{RED}❌ OPENAI_API_KEY не настроен{RESET}")
    sys.exit(1)
else:
    print(f"{GREEN}✅ OPENAI_API_KEY: sk-proj-...{openai_key[-10:]}{RESET}")

# Подключение к БД
print("\n2️⃣  Подключение к pgvector БД...")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(vector_db, pool_pre_ping=True)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM product_embeddings"))
        count = result.scalar()
    
    print(f"{GREEN}✅ Подключено! Найдено {count} embeddings{RESET}")
    
except Exception as e:
    print(f"{RED}❌ Ошибка подключения: {e}{RESET}")
    sys.exit(1)

# Тестовый поиск
print("\n3️⃣  Тестовый поиск...")
test_queries = ["рюкзак", "кружка", "ручка"]

try:
    from openai import OpenAI
    import httpx
    import time
    
    client = OpenAI(api_key=openai_key)
    
    for query in test_queries:
        print(f"\n   🔍 Поиск: '{query}'")
        
        start_time = time.time()
        
        # Генерируем embedding
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
            timeout=httpx.Timeout(10.0)
        )
        embedding = response.data[0].embedding
        
        embedding_time = time.time() - start_time
        
        # Поиск в БД
        # Преобразуем list в строку для pgvector
        query_vector_str = '[' + ','.join(map(str, embedding)) + ']'
        
        search_start = time.time()
        with engine.connect() as conn:
            # Используем format SQL так как SQLAlchemy text() конфликтует с ::vector cast
            sql_query = f"""
                SELECT product_id, product_name,
                       1 - (name_embedding <=> '{query_vector_str}'::vector) as similarity
                FROM product_embeddings
                WHERE 1 - (name_embedding <=> '{query_vector_str}'::vector) >= 0.25
                ORDER BY name_embedding <=> '{query_vector_str}'::vector
                LIMIT 5
            """
            results = conn.execute(text(sql_query)).fetchall()
        
        search_time = time.time() - search_start
        total_time = time.time() - start_time
        
        print(f"      ⏱️  Embedding: {embedding_time:.2f}с | Поиск: {search_time:.2f}с | Всего: {total_time:.2f}с")
        print(f"      📊 Найдено: {len(results)} товаров")
        
        if results:
            print(f"      {GREEN}✅ Топ-3 результата:{RESET}")
            for i, (pid, pname, sim) in enumerate(results[:3], 1):
                print(f"         {i}. [{sim:.3f}] {pname}")
        else:
            print(f"      {YELLOW}⚠️  Ничего не найдено{RESET}")

except Exception as e:
    print(f"{RED}❌ Ошибка поиска: {e}{RESET}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Итого
print(f"\n{BLUE}{'=' * 80}{RESET}")
print(f"{GREEN}✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!{RESET}")
print(f"{BLUE}{'=' * 80}{RESET}\n")

print("📝 Следующие шаги:")
print("1. Запусти веб-интерфейс:")
print("   cd web_interface && python3 app.py")
print("")
print("2. Открой http://localhost:5000 и протестируй поиск")
print("")
print("3. Если работает хорошо - деплой на Railway!")
print("")

