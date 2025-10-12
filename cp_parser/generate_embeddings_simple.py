#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Генерация embeddings БЕЗ pgvector - сохраняем в TEXT колонку
"""

import os
import time
import json
from dotenv import load_dotenv
from database.postgresql_manager import db_manager
from sqlalchemy import text

load_dotenv()

# Проверяем наличие OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
except:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI не доступен. Установите: pip3 install --break-system-packages openai")

def generate_embedding(text: str):
    """Генерирует embedding для текста"""
    if not OPENAI_AVAILABLE:
        return None
    
    try:
        response = client.embeddings.create(
            input=text[:8000],  # Ограничение OpenAI
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"   ⚠️  Ошибка генерации embedding: {e}")
        return None

def count_products_without_embeddings():
    """Подсчитывает товары без embeddings"""
    with db_manager.get_session() as session:
        try:
            count = session.execute(text("""
                SELECT COUNT(*) 
                FROM products 
                WHERE name_embedding_text IS NULL
            """)).scalar()
            return count
        except:
            return None

def generate_all_embeddings(batch_size=10, limit=None):
    """Генерирует embeddings для всех товаров"""
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI недоступен. Установите: pip3 install --break-system-packages openai")
        print("   И добавьте OPENAI_API_KEY в .env")
        return
    
    print("="*80)
    print("ГЕНЕРАЦИЯ EMBEDDINGS (ПРОСТАЯ ВЕРСИЯ)")
    print("="*80)
    print()
    
    with db_manager.get_session() as session:
        try:
            # Проверяем существует ли колонка
            check = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                AND column_name = 'name_embedding_text'
            """)).fetchone()
            
            if not check:
                print("❌ Колонка name_embedding_text не существует")
                print("   Запустите сначала: python3 setup_embeddings_simple.py")
                return
            
        except Exception as e:
            print(f"❌ Ошибка проверки колонки: {e}")
            return
    
    # Получаем товары для обработки
    with db_manager.get_session() as session:
        query = """
            SELECT id, name, description
            FROM products
            WHERE name_embedding_text IS NULL
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
        
        products = session.execute(text(query)).fetchall()
        
        total = len(products)
        if total == 0:
            print("✅ Все товары уже имеют embeddings!")
            return
        
        print(f"📊 Найдено товаров для обработки: {total}")
        print(f"⏱️  Примерное время: {total * 0.2:.1f} секунд")
        print()
        
        success_count = 0
        error_count = 0
        
        for i, (product_id, name, description) in enumerate(products, 1):
            try:
                # Формируем текст для embedding
                text_for_embedding = name or ""
                if description:
                    text_for_embedding += f" {description[:200]}"
                
                if not text_for_embedding.strip():
                    print(f"   ⚠️  [{i}/{total}] ID {product_id}: пустое название, пропускаем")
                    error_count += 1
                    continue
                
                # Генерируем embedding
                embedding = generate_embedding(text_for_embedding)
                
                if embedding is None:
                    error_count += 1
                    continue
                
                # Сохраняем в БД как JSON строку
                embedding_json = json.dumps(embedding)
                
                session.execute(text("""
                    UPDATE products 
                    SET name_embedding_text = :embedding
                    WHERE id = :product_id
                """), {
                    'embedding': embedding_json,
                    'product_id': product_id
                })
                
                success_count += 1
                
                # Коммитим батчами
                if i % batch_size == 0:
                    session.commit()
                    print(f"✅ [{i}/{total}] Обработано: {success_count} успешно, {error_count} ошибок")
                    time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ [{i}/{total}] ID {product_id}: {e}")
                error_count += 1
                continue
        
        # Финальный коммит
        try:
            session.commit()
        except Exception as e:
            print(f"❌ Ошибка финального коммита: {e}")
        
        print()
        print("="*80)
        print("РЕЗУЛЬТАТЫ")
        print("="*80)
        print(f"✅ Успешно обработано: {success_count}")
        print(f"❌ Ошибок: {error_count}")
        print(f"📊 Процент успеха: {success_count/total*100:.1f}%")
        print()

def generate_test_embeddings():
    """Генерирует embeddings для первых 10 товаров (тест)"""
    print("="*80)
    print("ТЕСТОВАЯ ГЕНЕРАЦИЯ (10 товаров)")
    print("="*80)
    print()
    generate_all_embeddings(batch_size=5, limit=10)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        generate_test_embeddings()
    else:
        # Показываем статистику
        count = count_products_without_embeddings()
        if count is not None:
            print(f"Товаров без embeddings: {count}")
            print()
            if count > 0:
                answer = input(f"Сгенерировать embeddings для {count} товаров? (y/n): ")
                if answer.lower() == 'y':
                    generate_all_embeddings()
            else:
                print("✅ Все embeddings уже сгенерированы!")
        else:
            print("⚠️  Не удалось проверить статус. Запустите setup_embeddings_simple.py сначала")






