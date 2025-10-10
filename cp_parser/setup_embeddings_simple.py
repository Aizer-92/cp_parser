#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Установка embeddings БЕЗ pgvector - используем TEXT колонку
Простое решение, которое работает прямо сейчас!
"""

from database.postgresql_manager import db_manager
from sqlalchemy import text

def main():
    print("="*80)
    print("УСТАНОВКА EMBEDDINGS (ПРОСТАЯ ВЕРСИЯ БЕЗ PGVECTOR)")
    print("="*80)
    print()
    print("✅ Преимущества:")
    print("   - Работает прямо сейчас (без pgvector)")
    print("   - Одна БД (не нужен отдельный сервис)")
    print("   - Легко апгрейдить на pgvector потом")
    print()
    
    with db_manager.get_session() as session:
        # Шаг 1: Добавление TEXT колонки для embeddings
        print("Шаг 1: Добавление колонки name_embedding_text...")
        try:
            # Проверяем существует ли колонка
            check = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                AND column_name = 'name_embedding_text'
            """)).fetchone()
            
            if check:
                print("✅ Колонка name_embedding_text уже существует")
            else:
                session.execute(text("""
                    ALTER TABLE products 
                    ADD COLUMN name_embedding_text TEXT
                """))
                session.commit()
                print("✅ Колонка name_embedding_text добавлена!")
        except Exception as e:
            session.rollback()
            print(f"❌ Ошибка добавления колонки: {e}")
            return
        
        # Шаг 2: Статистика
        print()
        print("Шаг 2: Проверка товаров...")
        try:
            total = session.execute(text("""
                SELECT COUNT(*) FROM products
            """)).scalar()
            
            with_embeddings = session.execute(text("""
                SELECT COUNT(*) FROM products 
                WHERE name_embedding_text IS NOT NULL
            """)).scalar()
            
            without_embeddings = total - with_embeddings
            
            print(f"📊 Всего товаров: {total}")
            print(f"✅ С embeddings: {with_embeddings}")
            print(f"⏳ Без embeddings: {without_embeddings}")
        except Exception as e:
            print(f"⚠️  Ошибка получения статистики: {e}")
        
        # Итог
        print()
        print("="*80)
        print("УСТАНОВКА ЗАВЕРШЕНА!")
        print("="*80)
        print()
        print("✅ База данных готова к векторному поиску")
        print()
        print("Следующий шаг:")
        print("  python3 generate_embeddings_simple.py test")
        print()

if __name__ == '__main__':
    main()


