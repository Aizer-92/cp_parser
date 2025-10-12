#!/usr/bin/env python3
"""
Диагностика pgvector результатов - показывает что именно находит поиск
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from openai import OpenAI
import httpx

load_dotenv()

# Цвета
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test_search(query, threshold=0.25, limit=50):
    """
    Тестирует поиск и показывает детальные результаты
    """
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}Поиск: '{query}' | Порог: {threshold} | Лимит: {limit}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")
    
    # Подключение
    vector_db = os.getenv('VECTOR_DATABASE_URL')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    engine = create_engine(vector_db, pool_pre_ping=True)
    client = OpenAI(api_key=openai_key)
    
    # Генерация embedding
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
        timeout=httpx.Timeout(10.0)
    )
    embedding = response.data[0].embedding
    
    # Поиск
    query_vector_str = '[' + ','.join(map(str, embedding)) + ']'
    
    with engine.connect() as conn:
        sql_query = f"""
            SELECT 
                product_id,
                product_name,
                1 - (name_embedding <=> '{query_vector_str}'::vector) as similarity
            FROM product_embeddings
            WHERE 1 - (name_embedding <=> '{query_vector_str}'::vector) >= {threshold}
            ORDER BY name_embedding <=> '{query_vector_str}'::vector
            LIMIT {limit}
        """
        results = conn.execute(text(sql_query)).fetchall()
    
    # Анализ результатов
    print(f"{GREEN}✅ Найдено: {len(results)} товаров{RESET}\n")
    
    if not results:
        print(f"{RED}❌ Ничего не найдено! Попробуй понизить порог.{RESET}")
        return
    
    # Статистика similarity
    similarities = [r[2] for r in results]
    avg_sim = sum(similarities) / len(similarities)
    min_sim = min(similarities)
    max_sim = max(similarities)
    
    print(f"{BLUE}📊 СТАТИСТИКА SIMILARITY:{RESET}")
    print(f"   Минимум: {min_sim:.3f}")
    print(f"   Средний: {avg_sim:.3f}")
    print(f"   Максимум: {max_sim:.3f}")
    
    # Распределение по диапазонам
    ranges = {
        '0.90-1.00': 0,
        '0.70-0.89': 0,
        '0.50-0.69': 0,
        '0.40-0.49': 0,
        '0.25-0.39': 0,
    }
    
    for sim in similarities:
        if sim >= 0.90:
            ranges['0.90-1.00'] += 1
        elif sim >= 0.70:
            ranges['0.70-0.89'] += 1
        elif sim >= 0.50:
            ranges['0.50-0.69'] += 1
        elif sim >= 0.40:
            ranges['0.40-0.49'] += 1
        else:
            ranges['0.25-0.39'] += 1
    
    print(f"\n{BLUE}📊 РАСПРЕДЕЛЕНИЕ:{RESET}")
    for range_name, count in ranges.items():
        if count > 0:
            percent = count / len(results) * 100
            bar = '█' * int(percent / 5)
            print(f"   {range_name}: {count:3d} товаров ({percent:5.1f}%) {bar}")
    
    # Топ результаты
    print(f"\n{BLUE}🔝 ТОП-15 РЕЗУЛЬТАТОВ:{RESET}")
    for i, (pid, pname, sim) in enumerate(results[:15], 1):
        # Цвет в зависимости от similarity
        if sim >= 0.90:
            color = GREEN
            emoji = "🎯"
        elif sim >= 0.70:
            color = BLUE
            emoji = "✅"
        elif sim >= 0.50:
            color = YELLOW
            emoji = "⚠️ "
        else:
            color = RED
            emoji = "❌"
        
        print(f"   {i:2d}. {color}[{sim:.3f}] {emoji} {pname}{RESET}")
    
    # Последние результаты (вероятный "мусор")
    if len(results) > 15:
        print(f"\n{RED}🗑️  ПОСЛЕДНИЕ 5 РЕЗУЛЬТАТОВ (вероятный мусор):{RESET}")
        for i, (pid, pname, sim) in enumerate(results[-5:], len(results)-4):
            print(f"   {i:2d}. {RED}[{sim:.3f}] ❌ {pname}{RESET}")
    
    # Рекомендации
    print(f"\n{YELLOW}💡 РЕКОМЕНДАЦИИ:{RESET}")
    
    if min_sim < 0.30:
        print(f"   ⚠️  Порог {threshold} слишком низкий - много мусора")
        print(f"   ✅ Рекомендую поднять до 0.40 или 0.50")
    
    if len(results) == limit:
        print(f"   ⚠️  Достигнут LIMIT {limit} - возможно есть ещё результаты")
        print(f"   ✅ Можно уменьшить LIMIT до 50 или поднять порог")
    
    if avg_sim < 0.50:
        print(f"   ⚠️  Средний similarity {avg_sim:.3f} низкий")
        print(f"   ✅ Рекомендую порог 0.40-0.50 для качественных результатов")
    
    # Предложение оптимального порога
    good_results = [r for r in results if r[2] >= 0.40]
    if len(good_results) > 0:
        print(f"\n{GREEN}✨ ОПТИМАЛЬНЫЙ ПОРОГ: 0.40{RESET}")
        print(f"   • Качественных результатов: {len(good_results)}")
        print(f"   • Мусора: {len(results) - len(good_results)}")

def main():
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{'ДИАГНОСТИКА pgvector РЕЗУЛЬТАТОВ'.center(80)}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")
    
    # Тесты с разными запросами
    queries = [
        ("рюкзак", 0.25, 50),
        ("кружка", 0.25, 50),
        ("ручка", 0.25, 50),
    ]
    
    for query, threshold, limit in queries:
        test_search(query, threshold, limit)
    
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{GREEN}✅ ДИАГНОСТИКА ЗАВЕРШЕНА{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")
    
    print(f"{YELLOW}📝 РЕКОМЕНДАЦИИ ДЛЯ УЛУЧШЕНИЯ:{RESET}")
    print("1. Поднять порог similarity: 0.25 → 0.40 или 0.50")
    print("2. Уменьшить LIMIT: 200 → 50 или 75")
    print("3. Добавить логирование similarity в app.py")
    print("")

if __name__ == "__main__":
    main()



