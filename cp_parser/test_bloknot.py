#!/usr/bin/env python3
"""
Тест конкретного запроса "блокнот"
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
RESET = '\033[0m'

query = "блокнот"
threshold = 0.25

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
    # Определяем это блокнот/ежедневник или брелок/мусор
    is_notebook = any(word in pname.lower() for word in [
        'блокнот', 'ежедневник', 'записн', 'notepad', 'notebook', 'diary', 'planner'
    ])
    
    is_keychain = any(word in pname.lower() for word in [
        'брелок', 'брелк', 'keychain', 'key ring'
    ])
    
    if is_notebook:
        color = GREEN
        emoji = "✅"
        label = "ПРАВИЛЬНО"
    elif is_keychain:
        color = RED
        emoji = "❌"
        label = "БРЕЛОК (МУСОР!)"
    else:
        color = BLUE
        emoji = "❓"
        label = "ДРУГОЕ"
    
    print(f"   {i:3d}. {color}[{sim:.3f}] {emoji} {label:20s} {pname}{RESET}")

# Подсчет правильных/неправильных
notebooks = sum(1 for r in results if any(word in r[1].lower() for word in [
    'блокнот', 'ежедневник', 'записн', 'notepad', 'notebook', 'diary', 'planner'
]))

keychains = sum(1 for r in results if any(word in r[1].lower() for word in [
    'брелок', 'брелк', 'keychain', 'key ring'
]))

other = len(results) - notebooks - keychains

print(f"\n{BLUE}📊 ИТОГО:{RESET}")
print(f"   {GREEN}✅ Блокноты/Ежедневники: {notebooks} ({notebooks/len(results)*100:.1f}%){RESET}")
print(f"   {RED}❌ Брелоки (мусор): {keychains} ({keychains/len(results)*100:.1f}%){RESET}")
print(f"   ❓ Другое: {other} ({other/len(results)*100:.1f}%)")

# Анализ брелоков
if keychains > 0:
    print(f"\n{RED}🔍 АНАЛИЗ БРЕЛОКОВ:{RESET}")
    keychains_list = [r for r in results if any(word in r[1].lower() for word in [
        'брелок', 'брелк', 'keychain', 'key ring'
    ])]
    
    for pid, pname, sim in keychains_list[:10]:
        print(f"   [{sim:.3f}] {pname}")
    
    # Минимальный similarity брелока
    min_keychain_sim = min(r[2] for r in keychains_list)
    print(f"\n   Минимальный similarity брелока: {min_keychain_sim:.3f}")
    print(f"   {GREEN}💡 Рекомендация: поднять порог до {min_keychain_sim + 0.01:.2f}{RESET}")

print(f"\n{BLUE}{'=' * 80}{RESET}\n")

