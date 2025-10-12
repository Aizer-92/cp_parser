#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Регенерация embeddings ТОЛЬКО из названий товаров (БЕЗ описаний)
Это исправит проблему с неточным векторным поиском
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
    import httpx
    OPENAI_AVAILABLE = True
    api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(
        api_key=api_key,
        timeout=httpx.Timeout(10.0, connect=5.0)
    )
except Exception as e:
    OPENAI_AVAILABLE = False
    print(f"⚠️  OpenAI не доступен: {e}")
    print("   Установите: pip3 install openai httpx")

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

def regenerate_all_embeddings(batch_size=20, limit=None):
    """
    Регенерирует embeddings для ВСЕХ товаров (перезаписывает существующие)
    Использует ТОЛЬКО название товара (БЕЗ описания)
    """
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI недоступен. Проверьте .env и установите библиотеки")
        return
    
    print("="*80)
    print("РЕГЕНЕРАЦИЯ EMBEDDINGS (ТОЛЬКО НАЗВАНИЯ)")
    print("="*80)
    print()
    print("⚠️  ВАЖНО: Этот скрипт перезапишет ВСЕ существующие embeddings!")
    print("   Старые embeddings (название + описание) будут заменены")
    print("   Новые embeddings будут ТОЛЬКО из названий товаров")
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
    
    # Получаем ВСЕ товары (не только без embeddings)
    with db_manager.get_session() as session:
        query = """
            SELECT id, name
            FROM products
            WHERE name IS NOT NULL AND name != ''
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
        
        products = session.execute(text(query)).fetchall()
        
        total = len(products)
        if total == 0:
            print("❌ Товаров не найдено!")
            return
        
        print(f"📊 Найдено товаров для обработки: {total:,}")
        print(f"⏱️  Примерное время: {total * 0.3:.1f} секунд (~{total * 0.3 / 60:.1f} минут)")
        print()
        
        # Подтверждение
        answer = input(f"Начать регенерацию embeddings для {total:,} товаров? (y/n): ")
        if answer.lower() != 'y':
            print("❌ Отменено пользователем")
            return
        
        print()
        print("🚀 Начинаем регенерацию...")
        print()
        
        success_count = 0
        error_count = 0
        start_time = time.time()
        
        for i, (product_id, name) in enumerate(products, 1):
            try:
                # КРИТИЧЕСКИ ВАЖНО: Используем ТОЛЬКО название (БЕЗ описания!)
                text_for_embedding = name.strip()
                
                if not text_for_embedding:
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
                    elapsed = time.time() - start_time
                    speed = i / elapsed
                    eta = (total - i) / speed
                    print(f"✅ [{i}/{total}] Обработано: {success_count} успешно, {error_count} ошибок | ETA: {eta:.0f}с")
                    time.sleep(0.3)  # Rate limiting для OpenAI
                
            except Exception as e:
                print(f"   ❌ [{i}/{total}] ID {product_id}: {e}")
                error_count += 1
                continue
        
        # Финальный коммит
        try:
            session.commit()
        except Exception as e:
            print(f"❌ Ошибка финального коммита: {e}")
        
        elapsed = time.time() - start_time
        
        print()
        print("="*80)
        print("РЕЗУЛЬТАТЫ")
        print("="*80)
        print(f"✅ Успешно обработано: {success_count:,}")
        print(f"❌ Ошибок: {error_count:,}")
        print(f"📊 Процент успеха: {success_count/total*100:.1f}%")
        print(f"⏱️  Затрачено времени: {elapsed:.1f}с ({elapsed/60:.1f} мин)")
        print()
        print("🎯 Embeddings теперь содержат ТОЛЬКО названия товаров!")
        print("   Это должно улучшить точность векторного поиска")
        print()

def test_regeneration():
    """Тестовая регенерация для первых 10 товаров"""
    print("="*80)
    print("ТЕСТОВАЯ РЕГЕНЕРАЦИЯ (10 товаров)")
    print("="*80)
    print()
    
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI недоступен")
        return
    
    with db_manager.get_session() as session:
        query = """
            SELECT id, name
            FROM products
            WHERE name IS NOT NULL AND name != ''
            ORDER BY id
            LIMIT 10
        """
        
        products = session.execute(text(query)).fetchall()
        
        print(f"📊 Тестируем на {len(products)} товарах")
        print()
        
        for i, (product_id, name) in enumerate(products, 1):
            print(f"[{i}/10] ID {product_id}: {name[:60]}")
            
            embedding = generate_embedding(name.strip())
            
            if embedding:
                print(f"   ✅ Embedding сгенерирован ({len(embedding)} размерность)")
            else:
                print(f"   ❌ Ошибка генерации")
            
            print()
        
        print("✅ Тест завершен (данные НЕ записаны в БД)")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_regeneration()
    else:
        regenerate_all_embeddings()


