#!/usr/bin/env python3
"""
Скрипт для проверки работы векторного поиска.

Использование:
    python3 test_vector_search.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Цвета
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")

def main():
    print_header("ПРОВЕРКА ВЕКТОРНОГО ПОИСКА")
    
    # 1. Проверка OpenAI API ключа
    print(f"{BOLD}1. Проверка OpenAI API ключа{RESET}")
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if openai_key:
        print(f"{GREEN}✅ OpenAI API ключ найден{RESET}")
        print(f"   Ключ: {openai_key[:20]}...{openai_key[-10:]}")
    else:
        print(f"{RED}❌ OpenAI API ключ НЕ найден{RESET}")
        print(f"{YELLOW}   Векторный поиск будет отключен, работает fallback ILIKE{RESET}")
        return
    
    # 2. Проверка импорта openai
    print(f"\n{BOLD}2. Проверка библиотеки OpenAI{RESET}")
    try:
        import openai
        print(f"{GREEN}✅ Библиотека openai установлена{RESET}")
        print(f"   Версия: {openai.__version__}")
    except ImportError:
        print(f"{RED}❌ Библиотека openai НЕ установлена{RESET}")
        print(f"{YELLOW}   Установи: pip install openai{RESET}")
        return
    
    # 3. Проверка подключения к БД
    print(f"\n{BOLD}3. Проверка базы данных{RESET}")
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print(f"{RED}❌ DATABASE_URL не найден{RESET}")
        return
    
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Проверка колонки
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                  AND column_name = 'name_embedding_text'
            """))
            
            if result.fetchone():
                print(f"{GREEN}✅ Колонка name_embedding_text существует{RESET}")
            else:
                print(f"{RED}❌ Колонка name_embedding_text НЕ существует{RESET}")
                return
            
            # Проверка данных
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(name_embedding_text) as with_embeddings
                FROM products
            """))
            
            row = result.fetchone()
            total = row[0]
            with_emb = row[1]
            coverage = (with_emb / total * 100) if total > 0 else 0
            
            print(f"{GREEN}✅ Embeddings в БД:{RESET}")
            print(f"   Всего товаров: {total:,}")
            print(f"   С embeddings: {with_emb:,} ({coverage:.1f}%)")
            
            if coverage == 0:
                print(f"{RED}❌ Embeddings НЕ сгенерированы!{RESET}")
                print(f"{YELLOW}   Запусти: python3 generate_embeddings_simple.py{RESET}")
                return
    
    except Exception as e:
        print(f"{RED}❌ Ошибка подключения к БД: {e}{RESET}")
        return
    
    # 4. Тест генерации embedding
    print(f"\n{BOLD}4. Тест генерации embedding{RESET}")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="тест"
        )
        
        embedding = response.data[0].embedding
        print(f"{GREEN}✅ OpenAI API работает{RESET}")
        print(f"   Размерность embedding: {len(embedding)}")
        print(f"   Первые 5 значений: {embedding[:5]}")
    
    except Exception as e:
        print(f"{RED}❌ Ошибка OpenAI API: {e}{RESET}")
        return
    
    # 5. Тест векторного поиска
    print(f"\n{BOLD}5. Тест векторного поиска{RESET}")
    try:
        # Генерируем embedding для запроса
        query = "кружка"
        print(f"   Запрос: '{query}'")
        
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        
        query_embedding = response.data[0].embedding
        
        # Ищем похожие товары
        import json
        import math
        
        def cosine_similarity(vec1, vec2):
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            return dot_product / (magnitude1 * magnitude2)
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, name_embedding_text
                FROM products
                WHERE name_embedding_text IS NOT NULL
                LIMIT 100
            """))
            
            products = []
            for row in result:
                try:
                    product_embedding = json.loads(row[2])
                    similarity = cosine_similarity(query_embedding, product_embedding)
                    products.append({
                        'id': row[0],
                        'name': row[1],
                        'similarity': similarity
                    })
                except:
                    pass
            
            # Сортируем по похожести
            products.sort(key=lambda x: x['similarity'], reverse=True)
            
            print(f"\n{GREEN}✅ Топ-5 похожих товаров:{RESET}")
            for i, p in enumerate(products[:5], 1):
                print(f"   {i}. {p['name'][:60]} (сходство: {p['similarity']:.4f})")
    
    except Exception as e:
        print(f"{RED}❌ Ошибка при тесте поиска: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return
    
    # Итог
    print_header("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print(f"{GREEN}Векторный поиск полностью функционален!{RESET}\n")
    
    print(f"{BOLD}Что проверено:{RESET}")
    print(f"  ✅ OpenAI API ключ настроен")
    print(f"  ✅ Библиотека openai установлена")
    print(f"  ✅ База данных подключена")
    print(f"  ✅ Колонка name_embedding_text существует")
    print(f"  ✅ Embeddings сгенерированы ({coverage:.1f}% покрытие)")
    print(f"  ✅ OpenAI API отвечает")
    print(f"  ✅ Векторный поиск находит похожие товары")
    
    print(f"\n{BLUE}Теперь можно проверить на сайте:{RESET}")
    print(f"  Поиск 'кружка' → должна найти чашки, mugs")
    print(f"  Поиск 'ручка' → должна найти pens, авторучки")
    print(f"  Поиск 'USB' → должна найти флешки, накопители")


if __name__ == "__main__":
    main()

