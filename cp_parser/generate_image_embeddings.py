#!/usr/bin/env python3
"""
Генерация embeddings для изображений товаров.

Использует CLIP модель для генерации векторных представлений изображений.
Обрабатывает только главные изображения (is_main_image = TRUE).
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
        # Пытаемся использовать sentence-transformers (проще и быстрее)
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('clip-ViT-B-32')
        print_success("CLIP модель загружена (sentence-transformers)")
        return model, "sentence-transformers"
    except ImportError:
        print_warning("sentence-transformers не установлен")
        print_info("Установка: pip install sentence-transformers")
        print_info("Или: pip install transformers pillow torch")
        
        try:
            # Fallback на transformers
            from transformers import CLIPProcessor, CLIPModel
            import torch
            
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            print_success("CLIP модель загружена (transformers)")
            return (model, processor), "transformers"
        except ImportError:
            print_error("Нет доступных библиотек для CLIP!")
            print_info("Установи одну из:")
            print("  pip install sentence-transformers")
            print("  pip install transformers pillow torch")
            sys.exit(1)

def generate_embedding(image_source, model, model_type, is_local=False):
    """Генерирует embedding для изображения (из URL или локального файла)"""
    
    try:
        # Загружаем изображение
        if is_local:
            # Локальный файл
            image = Image.open(image_source).convert('RGB')
        else:
            # URL
            response = requests.get(image_source, timeout=10)
            image = Image.open(BytesIO(response.content)).convert('RGB')
        
        if model_type == "sentence-transformers":
            # sentence-transformers
            embedding = model.encode(image)
            return embedding.tolist()
        
        elif model_type == "transformers":
            # transformers (более сложный)
            import torch
            clip_model, processor = model
            
            inputs = processor(images=image, return_tensors="pt")
            with torch.no_grad():
                image_features = clip_model.get_image_features(**inputs)
            
            # Нормализация
            embedding = image_features / image_features.norm(dim=-1, keepdim=True)
            return embedding[0].tolist()
        
    except Exception as e:
        return None

def main():
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{'ГЕНЕРАЦИЯ IMAGE EMBEDDINGS'.center(80)}{RESET}")
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
    
    with main_engine.connect() as conn:
        # Получаем одно изображение для каждого товара (с URL или local_path)
        result = conn.execute(text("""
            SELECT COUNT(DISTINCT product_id)
            FROM product_images 
            WHERE product_id IS NOT NULL
            AND (
                (image_url IS NOT NULL AND image_url != '')
                OR (image_filename IS NOT NULL AND image_filename != '')
            )
        """))
        total_images = result.scalar()
    
    print_success(f"Найдено {total_images} главных изображений")
    
    # Подключение к pgvector БД
    print_info("\n2️⃣  Подключение к pgvector БД...")
    vector_engine = create_engine(vector_db_url, pool_pre_ping=True)
    
    with vector_engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM image_embeddings"))
        existing_count = result.scalar()
    
    print_info(f"В pgvector БД уже есть {existing_count} embeddings")
    
    # Генерация embeddings
    print_info("\n3️⃣  Генерация embeddings...")
    print_warning("   Это займет примерно 2-3 секунды на изображение")
    print_warning(f"   Ожидаемое время: ~{total_images * 2.5 / 60:.0f} минут")
    print_success(f"   Начинаем генерацию для {total_images} изображений!\n")
    
    # Обрабатываем батчами
    batch_size = 100
    offset = 0
    success_count = 0
    error_count = 0
    
    start_time = time.time()
    
    while offset < total_images:
        # Читаем batch из основной БД (одно изображение на товар, приоритет столбцу А)
        with main_engine.connect() as conn:
            images = conn.execute(text("""
                SELECT DISTINCT ON (pi.product_id) 
                    pi.id, 
                    pi.product_id, 
                    pi.image_url,
                    pi.image_filename
                FROM product_images pi
                WHERE pi.product_id IS NOT NULL
                AND (
                    (pi.image_url IS NOT NULL AND pi.image_url != '')
                    OR (pi.image_filename IS NOT NULL AND pi.image_filename != '')
                )
                ORDER BY pi.product_id, 
                         CASE WHEN pi.column_number = 1 THEN 0 ELSE 1 END,
                         pi.id
                LIMIT :limit OFFSET :offset
            """), {"limit": batch_size, "offset": offset}).fetchall()
        
        if not images:
            break
        
        print(f"\n   📦 Batch {offset // batch_size + 1}: обрабатываем {len(images)} изображений...")
        
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
                embedding = generate_embedding(final_url, model, model_type, is_local=False)
                
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
                        "url": final_url[:200],  # Обрезаем длинные URL
                        "model": f"{model_type}/clip-vit-base-patch32"
                    })
                
                success_count += 1
                
                # Прогресс
                if success_count % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = success_count / elapsed if elapsed > 0 else 0
                    remaining = (total_images - success_count) / rate if rate > 0 else 0
                    print(f"      Обработано: {success_count}/{total_images} | "
                          f"Скорость: {rate:.1f}/сек | ETA: {remaining/60:.0f}мин")
                
            except Exception as e:
                print_error(f"   Ошибка для image_id={image_id}: {e}")
                error_count += 1
                continue
        
        offset += batch_size
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{GREEN}{'=' * 80}{RESET}")
    print_success(f"Генерация завершена!")
    print_success(f"   Успешно: {success_count}")
    print(f"   {RED}Ошибок: {error_count}{RESET}")
    print_success(f"   Время: {elapsed_time / 60:.1f} минут")
    print_success(f"   Скорость: {success_count / elapsed_time:.1f} embeddings/сек")
    print(f"{GREEN}{'=' * 80}{RESET}\n")
    
    print_info("📝 Что дальше:")
    print("1. Интегрируй поиск по изображениям в веб-интерфейс")
    print("2. Протестируй загрузку фото и поиск похожих товаров")
    print("3. Оцени качество результатов")

if __name__ == "__main__":
    main()

