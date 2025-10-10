#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт установки векторного поиска
С graceful fallback - если что-то не работает, игнорируем
"""

from database.postgresql_manager import db_manager
from sqlalchemy import text
import sys

def setup_pgvector():
    """Установка расширения pgvector"""
    print("="*80)
    print("ШАГ 1: Установка pgvector")
    print("="*80)
    
    with db_manager.get_session() as session:
        try:
            # Проверяем доступность pgvector
            result = session.execute(text("""
                SELECT * FROM pg_available_extensions WHERE name = 'vector'
            """)).fetchone()
            
            if not result:
                print("⚠️  pgvector не доступен на сервере")
                print("   Нужно установить на Railway через команду:")
                print("   CREATE EXTENSION vector;")
                return False
            
            # Пытаемся создать расширение
            session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            session.commit()
            
            # Проверяем что создалось
            check = session.execute(text("""
                SELECT extname FROM pg_extension WHERE extname = 'vector'
            """)).fetchone()
            
            if check:
                print("✅ pgvector успешно установлен!")
                return True
            else:
                print("⚠️  pgvector не удалось установить")
                return False
                
        except Exception as e:
            session.rollback()
            print(f"⚠️  Ошибка при установке pgvector: {e}")
            print("   Векторный поиск будет недоступен, но проект продолжит работать")
            return False

def add_embedding_column():
    """Добавление колонки для embeddings"""
    print()
    print("="*80)
    print("ШАГ 2: Добавление колонки для embeddings")
    print("="*80)
    
    with db_manager.get_session() as session:
        try:
            # Проверяем существует ли колонка
            check = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                AND column_name = 'name_embedding'
            """)).fetchone()
            
            if check:
                print("✅ Колонка name_embedding уже существует")
                return True
            
            # Добавляем колонку
            session.execute(text("""
                ALTER TABLE products 
                ADD COLUMN name_embedding vector(1536)
            """))
            session.commit()
            
            print("✅ Колонка name_embedding добавлена!")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"⚠️  Ошибка при добавлении колонки: {e}")
            print("   Векторный поиск будет недоступен, но проект продолжит работать")
            return False

def create_index():
    """Создание HNSW индекса для быстрого поиска"""
    print()
    print("="*80)
    print("ШАГ 3: Создание индекса для векторного поиска")
    print("="*80)
    
    with db_manager.get_session() as session:
        try:
            # Проверяем существует ли индекс
            check = session.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE indexname = 'products_name_embedding_idx'
            """)).fetchone()
            
            if check:
                print("✅ Индекс products_name_embedding_idx уже существует")
                return True
            
            # Создаем HNSW индекс
            print("   Создание индекса (может занять 1-2 минуты)...")
            session.execute(text("""
                CREATE INDEX products_name_embedding_idx 
                ON products 
                USING hnsw (name_embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """))
            session.commit()
            
            print("✅ Индекс создан!")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"⚠️  Ошибка при создании индекса: {e}")
            print("   Поиск будет медленнее, но будет работать")
            return False

def check_openai_key():
    """Проверка наличия OpenAI API ключа"""
    print()
    print("="*80)
    print("ШАГ 4: Проверка OpenAI API ключа")
    print("="*80)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY не найден в .env")
        print("   Добавьте в .env файл:")
        print("   OPENAI_API_KEY=your_key_here")
        print()
        print("   Генерация embeddings будет недоступна")
        return False
    
    print(f"✅ OPENAI_API_KEY найден: {api_key[:10]}...")
    return True

def main():
    print("\n")
    print("="*80)
    print("УСТАНОВКА ВЕКТОРНОГО ПОИСКА")
    print("="*80)
    print()
    print("⚠️  ВАЖНО: Если что-то не работает - проект продолжит работать как раньше")
    print()
    
    # Шаг 1: pgvector
    pgvector_ok = setup_pgvector()
    
    if not pgvector_ok:
        print()
        print("="*80)
        print("ИТОГ: Векторный поиск не установлен")
        print("="*80)
        print("Причина: pgvector не доступен")
        print("Решение: Установите pgvector на Railway вручную")
        print()
        print("Текущий поиск продолжает работать как раньше ✅")
        return
    
    # Шаг 2: Колонка для embeddings
    column_ok = add_embedding_column()
    
    if not column_ok:
        print()
        print("="*80)
        print("ИТОГ: Векторный поиск частично установлен")
        print("="*80)
        print("pgvector установлен, но колонка не создана")
        print("Текущий поиск продолжает работать как раньше ✅")
        return
    
    # Шаг 3: Индекс
    index_ok = create_index()
    
    # Шаг 4: OpenAI ключ
    openai_ok = check_openai_key()
    
    # Итоговая статистика
    print()
    print("="*80)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("="*80)
    print(f"pgvector: {'✅' if pgvector_ok else '❌'}")
    print(f"Колонка name_embedding: {'✅' if column_ok else '❌'}")
    print(f"HNSW индекс: {'✅' if index_ok else '⚠️  (необязательно)'}")
    print(f"OpenAI API ключ: {'✅' if openai_ok else '⚠️  (для генерации embeddings)'}")
    print()
    
    if pgvector_ok and column_ok:
        print("🎉 Векторный поиск готов к использованию!")
        print()
        print("Следующие шаги:")
        if openai_ok:
            print("1. Запустите: python3 generate_embeddings.py")
            print("2. Векторный поиск заработает автоматически")
        else:
            print("1. Добавьте OPENAI_API_KEY в .env")
            print("2. Запустите: python3 generate_embeddings.py")
    else:
        print("⚠️  Векторный поиск не полностью настроен")
        print("Текущий поиск продолжает работать как раньше ✅")
    
    print()
    print("="*80)

if __name__ == '__main__':
    main()


