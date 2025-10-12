#!/usr/bin/env python3
"""
Тест поиска похожих товаров по изображению
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from PIL import Image
import requests
from io import BytesIO

load_dotenv()

# Цвета
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def load_clip_model():
    """Загружает CLIP модель"""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('clip-ViT-B-32')
    return model, "sentence-transformers"

def generate_embedding(image_url, model, model_type):
    """Генерирует embedding для изображения"""
    try:
        response = requests.get(image_url, timeout=10)
        image = Image.open(BytesIO(response.content)).convert('RGB')
        
        if model_type == "sentence-transformers":
            embedding = model.encode(image)
            return embedding.tolist()
    except Exception as e:
        print(f"{RED}❌ Ошибка: {e}{RESET}")
        return None

def search_similar_images(query_embedding, vector_engine, limit=10):
    """Ищет похожие изображения в pgvector БД"""
    
    query_vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    with vector_engine.connect() as conn:
        sql_query = f"""
            SELECT 
                ie.product_id,
                ie.image_url,
                1 - (ie.image_embedding <=> '{query_vector_str}'::vector) as similarity
            FROM image_embeddings ie
            ORDER BY ie.image_embedding <=> '{query_vector_str}'::vector
            LIMIT {limit}
        """
        results = conn.execute(text(sql_query)).fetchall()
    
    return results

def get_product_info(product_ids, main_engine):
    """Получает информацию о товарах"""
    
    if not product_ids:
        return []
    
    with main_engine.connect() as conn:
        placeholders = ','.join([f':id{i}' for i in range(len(product_ids))])
        params = {f'id{i}': pid for i, pid in enumerate(product_ids)}
        
        result = conn.execute(text(f"""
            SELECT id, name, description, article_number
            FROM products
            WHERE id IN ({placeholders})
        """), params)
        
        products = {row[0]: row for row in result.fetchall()}
    
    return products

def main():
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{'ТЕСТ ПОИСКА ПО ИЗОБРАЖЕНИЯМ'.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")
    
    # Подключение к БД
    main_db_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URL_PRIVATE')
    vector_db_url = os.getenv('VECTOR_DATABASE_URL')
    
    if not main_db_url or not vector_db_url:
        print(f"{RED}❌ Не найдены DATABASE_URL и/или VECTOR_DATABASE_URL{RESET}")
        sys.exit(1)
    
    # Загрузка модели
    print(f"{BLUE}ℹ️  Загрузка CLIP модели...{RESET}")
    model, model_type = load_clip_model()
    print(f"{GREEN}✅ Модель загружена{RESET}\n")
    
    # Подключение к БД
    main_engine = create_engine(main_db_url, pool_pre_ping=True)
    vector_engine = create_engine(vector_db_url, pool_pre_ping=True)
    
    # Получаем product_id из pgvector БД
    with vector_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT product_id FROM image_embeddings LIMIT 100
        """))
        product_ids_with_embeddings = [r[0] for r in result.fetchall()]
    
    if not product_ids_with_embeddings:
        print(f"{RED}❌ Нет embeddings в БД! Запусти сначала генерацию.{RESET}")
        sys.exit(1)
    
    # Получаем информацию о товарах из основной БД
    with main_engine.connect() as conn:
        placeholders = ','.join([f':id{i}' for i in range(min(100, len(product_ids_with_embeddings)))])
        params = {f'id{i}': pid for i, pid in enumerate(product_ids_with_embeddings[:100])}
        
        test_products = conn.execute(text(f"""
            SELECT DISTINCT ON (pi.product_id)
                pi.product_id,
                p.name,
                pi.image_url,
                pi.image_filename
            FROM product_images pi
            JOIN products p ON p.id = pi.product_id
            WHERE pi.product_id IN ({placeholders})
            ORDER BY pi.product_id, 
                     CASE WHEN pi.column_number = 1 THEN 0 ELSE 1 END
            LIMIT 5
        """), params).fetchall()
    
    if not test_products:
        print(f"{RED}❌ Нет товаров для теста!{RESET}")
        sys.exit(1)
    
    print(f"{BLUE}📝 Доступно {len(test_products)} товаров для теста:{RESET}\n")
    for i, (pid, name, url, filename) in enumerate(test_products, 1):
        print(f"   {i}. [{pid}] {name[:50]}...")
    
    print(f"\n{YELLOW}Выбери номер товара (1-{len(test_products)}) или 0 для выхода: {RESET}", end='')
    try:
        choice = int(input().strip())
        if choice == 0:
            print(f"{BLUE}👋 Выход{RESET}")
            sys.exit(0)
        if choice < 1 or choice > len(test_products):
            print(f"{RED}❌ Неверный выбор!{RESET}")
            sys.exit(1)
    except ValueError:
        print(f"{RED}❌ Неверный ввод!{RESET}")
        sys.exit(1)
    
    # Выбранный товар
    selected = test_products[choice - 1]
    product_id, product_name, image_url, image_filename = selected
    
    # Формируем URL
    if image_url and image_url.strip():
        final_url = image_url
    elif image_filename and image_filename.strip():
        final_url = f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{image_filename}"
    else:
        print(f"{RED}❌ Нет URL для изображения!{RESET}")
        sys.exit(1)
    
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}🔍 ТЕСТИРУЕМ ПОИСК ПО ИЗОБРАЖЕНИЮ:{RESET}")
    print(f"   ID: {product_id}")
    print(f"   Название: {product_name}")
    print(f"   URL: {final_url[:70]}...")
    print(f"{BLUE}{'=' * 80}{RESET}\n")
    
    # Генерация embedding
    print(f"{BLUE}⏳ Генерация embedding...{RESET}")
    query_embedding = generate_embedding(final_url, model, model_type)
    
    if not query_embedding:
        print(f"{RED}❌ Не удалось сгенерировать embedding!{RESET}")
        sys.exit(1)
    
    print(f"{GREEN}✅ Embedding сгенерирован ({len(query_embedding)} размерность){RESET}\n")
    
    # Поиск похожих
    print(f"{BLUE}🔍 Поиск похожих товаров...{RESET}\n")
    similar = search_similar_images(query_embedding, vector_engine, limit=20)
    
    # Получаем информацию о товарах
    product_ids = [r[0] for r in similar]
    products_info = get_product_info(product_ids, main_engine)
    
    # Выводим результаты
    print(f"{BOLD}{GREEN}📊 РЕЗУЛЬТАТЫ ПОИСКА:{RESET}\n")
    
    for i, (pid, img_url, similarity) in enumerate(similar, 1):
        product_info = products_info.get(pid)
        
        if not product_info:
            continue
        
        pname = product_info[1] or "N/A"
        article = product_info[3] or "N/A"
        
        # Цвет в зависимости от similarity
        if similarity >= 0.95:
            color = GREEN
            emoji = "🎯"
            label = "ОЧЕНЬ ПОХОЖ"
        elif similarity >= 0.85:
            color = BLUE
            emoji = "✅"
            label = "ПОХОЖ"
        elif similarity >= 0.75:
            color = YELLOW
            emoji = "⚠️"
            label = "МОЖЕТ БЫТЬ"
        else:
            color = RED
            emoji = "❌"
            label = "НЕ ПОХОЖ"
        
        # Отмечаем исходный товар
        if pid == product_id:
            marker = f"{BOLD}[ИСХОДНЫЙ ТОВАР]{RESET}"
        else:
            marker = ""
        
        print(f"{i:3d}. {color}[{similarity:.3f}] {emoji} {label:15s}{RESET} {marker}")
        print(f"      ID: {pid} | Артикул: {article}")
        print(f"      {pname[:70]}")
        print(f"      {img_url[:70] if img_url else 'N/A'}...")
        print()
    
    # Статистика
    similarities = [r[2] for r in similar]
    avg_sim = sum(similarities) / len(similarities)
    
    print(f"{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}📊 СТАТИСТИКА:{RESET}")
    print(f"   Найдено: {len(similar)} товаров")
    print(f"   Минимум: {min(similarities):.3f}")
    print(f"   Средний: {avg_sim:.3f}")
    print(f"   Максимум: {max(similarities):.3f}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")
    
    # Анализ качества
    very_similar = sum(1 for s in similarities if s >= 0.95)
    similar_count = sum(1 for s in similarities if 0.85 <= s < 0.95)
    maybe_count = sum(1 for s in similarities if 0.75 <= s < 0.85)
    not_similar = sum(1 for s in similarities if s < 0.75)
    
    print(f"{BOLD}🎯 ОЦЕНКА КАЧЕСТВА:{RESET}")
    print(f"   {GREEN}Очень похожие (>0.95): {very_similar}{RESET}")
    print(f"   {BLUE}Похожие (0.85-0.95): {similar_count}{RESET}")
    print(f"   {YELLOW}Может быть (0.75-0.85): {maybe_count}{RESET}")
    print(f"   {RED}Не похожие (<0.75): {not_similar}{RESET}")
    print()
    
    if very_similar >= 10:
        print(f"{GREEN}✅ ОТЛИЧНО! Много очень похожих товаров{RESET}")
    elif similar_count >= 10:
        print(f"{BLUE}✅ ХОРОШО! Находит похожие товары{RESET}")
    elif maybe_count >= 10:
        print(f"{YELLOW}⚠️  СРЕДНЕ. Результаты не очень точные{RESET}")
    else:
        print(f"{RED}❌ ПЛОХО. Поиск не находит похожие товары{RESET}")
    
    print(f"\n{BLUE}💡 Хочешь протестировать другой товар? Запусти снова: py test_image_search.py{RESET}\n")

if __name__ == "__main__":
    main()

