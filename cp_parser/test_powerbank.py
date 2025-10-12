#!/usr/bin/env python3
"""
Тест запроса "повербанк"
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from openai import OpenAI
import httpx

load_dotenv()

GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

query = "повербанк"
threshold = 0.55

print(f"\n{BLUE}{'=' * 80}{RESET}")
print(f"{BLUE}Тест запроса: '{query}' (порог: {threshold}){RESET}")
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
        LIMIT 100
    """
    results = conn.execute(text(sql_query)).fetchall()

print(f"{GREEN}✅ Найдено: {len(results)} товаров{RESET}\n")

# Статистика
if results:
    similarities = [r[2] for r in results]
    avg_sim = sum(similarities) / len(similarities)
    min_sim = min(similarities)
    max_sim = max(similarities)

    print(f"{BLUE}📊 СТАТИСТИКА:{RESET}")
    print(f"   Минимум: {min_sim:.3f}")
    print(f"   Средний: {avg_sim:.3f}")
    print(f"   Максимум: {max_sim:.3f}\n")

# Все результаты
print(f"{BLUE}📝 ВСЕ РЕЗУЛЬТАТЫ:{RESET}\n")

for i, (pid, pname, sim) in enumerate(results, 1):
    # Определяем это повербанк или банка/другое
    is_powerbank = any(word in pname.lower() for word in [
        'повербанк', 'power bank', 'powerbank', 'power-bank', 'павербанк'
    ])
    
    is_jar = any(word in pname.lower() for word in [
        'банка', 'банк ', ' банк', 'jar', 'can', 'контейнер'
    ])
    
    if is_powerbank:
        color = GREEN
        emoji = "✅"
        label = "ПОВЕРБАНК"
    elif is_jar:
        color = RED
        emoji = "❌"
        label = "БАНКА (МУСОР!)"
    else:
        color = YELLOW
        emoji = "❓"
        label = "ДРУГОЕ"
    
    print(f"   {i:3d}. {color}[{sim:.3f}] {emoji} {label:20s} {pname}{RESET}")

# Подсчет правильных/неправильных
powerbanks = sum(1 for r in results if any(word in r[1].lower() for word in [
    'повербанк', 'power bank', 'powerbank', 'power-bank', 'павербанк'
]))

jars = sum(1 for r in results if any(word in r[1].lower() for word in [
    'банка', 'банк ', ' банк', 'jar', 'can', 'контейнер'
]))

other = len(results) - powerbanks - jars

print(f"\n{BLUE}📊 ИТОГО:{RESET}")
print(f"   {GREEN}✅ Повербанки: {powerbanks} ({powerbanks/len(results)*100 if results else 0:.1f}%){RESET}")
print(f"   {RED}❌ Банки/Банки (мусор): {jars} ({jars/len(results)*100 if results else 0:.1f}%){RESET}")
print(f"   {YELLOW}❓ Другое: {other} ({other/len(results)*100 if results else 0:.1f}%){RESET}")

# Анализ банок
if jars > 0:
    print(f"\n{RED}🔍 АНАЛИЗ БАНОК:{RESET}")
    jars_list = [r for r in results if any(word in r[1].lower() for word in [
        'банка', 'банк ', ' банк', 'jar', 'can', 'контейнер'
    ])]
    
    for pid, pname, sim in jars_list[:10]:
        print(f"   [{sim:.3f}] {pname}")
    
    # Минимальный similarity банки
    min_jar_sim = min(r[2] for r in jars_list)
    max_jar_sim = max(r[2] for r in jars_list)
    print(f"\n   Минимальный similarity банки: {min_jar_sim:.3f}")
    print(f"   Максимальный similarity банки: {max_jar_sim:.3f}")
    print(f"   {GREEN}💡 Рекомендация: поднять порог до {max_jar_sim + 0.01:.2f}{RESET}")

print(f"\n{BLUE}{'=' * 80}{RESET}\n")

