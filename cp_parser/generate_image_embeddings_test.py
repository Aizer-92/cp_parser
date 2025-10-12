#!/usr/bin/env python3
"""
ТЕСТОВАЯ генерация embeddings для изображений товаров.
Обрабатывает только первые 100 изображений для теста.
"""

import os
import sys
import time
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

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def load_clip_model():
    """Загружает CLIP модель для генерации embeddings"""
    print_info("Загрузка CLIP модели...")
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('clip-ViT-B-32')
        print_success("CLIP модель загружена (sentence-transformers)")
        print_info("   Модель: clip-ViT-B-32")
        print_info("   Размерность: 512")
        return model, "sentence-transformers"
    except ImportError:
        print_error("sentence-transformers не установлен")
        print_info("Установка: pip install sentence-transformers")
        sys.exit(1)

def generate_embedding(image_url, model, model_type):
    """Генерирует embedding для изображения"""
    
    try:
        # Загружаем изображение
        response = requests.get(image_url, timeout=10)
        image = Image.open(BytesIO(response.content)).convert('RGB')
        
        if model_type == "sentence-transformers":
            embedding = model.encode(image)
            return embedding.tolist()
        
    except Exception as e:
        return None

def main():
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{'ТЕСТОВАЯ ГЕНЕРАЦИЯ IMAGE EMBEDDINGS (100 изображений)'.center(80)}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")
    
    # Подключение к БД
    main_db_url = os.getenv('DATABASE_URL_PRIVATE') or os.getenv('DATABASE_URL')
    vector_db_url = os.getenv('VECTOR_DATABASE_URL')
    
    if not main_db_url or not vector_db_url:
        print_error("Не найдены DATABASE_URL и/или VECTOR_DATABASE_URL")
        sys.exit(1)
    
    print_info(f"Основная БД: {main_db_url[:50]}...")
    print_info(f"Векторная БД: {vector_db_url[:50]}...")
    
    # Загрузка модели
    model, model_type = load_clip_model()
    
    # Подключение к основной БД
    print_info("\n1️⃣  Подключение к основной БД...")
    main_engine = create_engine(main_db_url, pool_pre_ping=True)
    
    # Подключение к pgvector БД
    print_info("\n2️⃣  Подключение к pgvector БД...")
    vector_engine = create_engine(vector_db_url, pool_pre_ping=True)
    
    # Генерация embeddings для первых 100 изображений
    print_info("\n3️⃣  Генерация embeddings для первых 100 изображений...")
    print_warning("   Это займет ~4-5 минут\n")
    
    TEST_LIMIT = 100
    success_count = 0
    error_count = 0
    
    start_time = time.time()
    
    # Читаем первые 100 изображений (одно на товар, приоритет столбцу А)
    with main_engine.connect() as conn:
        images = conn.execute(text("""
            SELECT DISTINCT ON (pi.product_id) 
                pi.id, pi.product_id, pi.image_url, pi.image_filename
            FROM product_images pi
            WHERE pi.product_id IS NOT NULL
            AND (
                (pi.image_url IS NOT NULL AND pi.image_url != '')
                OR (pi.image_filename IS NOT NULL AND pi.image_filename != '')
            )
            ORDER BY pi.product_id, 
                     CASE WHEN pi.column_number = 1 THEN 0 ELSE 1 END,
                     pi.id
            LIMIT :limit
        """), {"limit": TEST_LIMIT}).fetchall()
    
    print_success(f"Загружено {len(images)} изображений для обработки")
    
    # Генерируем embeddings
    for i, (image_id, product_id, image_url, image_filename) in enumerate(images, 1):
        try:
            # Формируем URL (если есть прямой URL - используем его, иначе формируем из filename)
            if image_url and image_url.strip():
                final_url = image_url
            elif image_filename and image_filename.strip():
                # Формируем облачный URL из filename
                final_url = f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{image_filename}"
            else:
                error_count += 1
                continue
            
            # Генерация embedding
            embedding = generate_embedding(final_url, model, model_type)
            
            if embedding is None:
                error_count += 1
                continue
            
            # Сохранение в pgvector БД
            with vector_engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO image_embeddings 
                        (image_id, product_id, image_embedding, image_url, model_version)
                    VALUES 
                        (:image_id, :product_id, :embedding, :url, :model)
                    ON CONFLICT (image_id) DO UPDATE
                    SET image_embedding = EXCLUDED.image_embedding,
                        updated_at = NOW()
                """), {
                    "image_id": image_id,
                    "product_id": product_id,
                    "embedding": embedding,
                    "url": final_url[:200],
                    "model": f"{model_type}/clip-vit-base-patch32"
                })
            
            success_count += 1
            
            # Прогресс каждые 10 изображений
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (len(images) - i) / rate if rate > 0 else 0
                print(f"      ✅ Обработано: {i}/{len(images)} | "
                      f"Скорость: {rate:.1f}/сек | ETA: {remaining:.0f}сек")
        
        except Exception as e:
            print_error(f"   [{i}/{len(images)}] ID {image_id}: {e}")
            error_count += 1
            continue
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{GREEN}{'=' * 80}{RESET}")
    print_success(f"ТЕСТ ЗАВЕРШЕН!")
    print_success(f"   Успешно: {success_count}/{len(images)}")
    print(f"   {RED}Ошибок: {error_count}/{len(images)}{RESET}")
    print_success(f"   Время: {elapsed_time:.0f} секунд ({elapsed_time / 60:.1f} минут)")
    print_success(f"   Скорость: {success_count / elapsed_time:.1f} embeddings/сек")
    print(f"{GREEN}{'=' * 80}{RESET}\n")
    
    if success_count > 0:
        print_info("📝 Что дальше:")
        print("1. Протестируй поиск по изображениям: py test_image_search.py")
        print("2. Если качество хорошее - запусти полную генерацию:")
        print("   py generate_image_embeddings.py")
    else:
        print_error("❌ Ни одного embedding не создано!")
        print_info("   Проверь доступность изображений по URL")

if __name__ == "__main__":
    main()

