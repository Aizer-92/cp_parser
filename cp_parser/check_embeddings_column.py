#!/usr/bin/env python3
"""
Проверка наличия колонки name_embedding_text в БД.
Работает как для локальной, так и для Railway БД.

Использование:
    # Локальная БД
    python3 check_embeddings_column.py
    
    # Railway БД
    export DATABASE_URL="postgresql://postgres:...railway.app/railway"
    python3 check_embeddings_column.py
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

# Цвета
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def main():
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print(f"{RED}❌ DATABASE_URL не найден в .env{RESET}")
        sys.exit(1)
    
    # Определяем тип БД
    if 'railway.app' in db_url:
        db_type = "🚂 Railway БД"
    else:
        db_type = "💻 Локальная БД"
    
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}Проверка колонки name_embedding_text - {db_type}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")
    
    try:
        engine = create_engine(db_url)
        
        # Проверка подключения
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"{GREEN}✅ Подключение успешно{RESET}")
            print(f"   PostgreSQL: {version[:50]}...\n")
        
        # Получаем список колонок
        inspector = inspect(engine)
        
        # Проверяем существование таблицы
        if 'products' not in inspector.get_table_names():
            print(f"{RED}❌ Таблица 'products' не найдена!{RESET}")
            sys.exit(1)
        
        columns = inspector.get_columns('products')
        
        print(f"{BOLD}📊 Колонки таблицы products:{RESET}")
        print("-" * 80)
        
        has_embedding_col = False
        
        for col in columns:
            if col['name'] == 'name_embedding_text':
                has_embedding_col = True
                print(f"{GREEN}🟢 {col['name']:30} {str(col['type']):20} {'NULL' if col['nullable'] else 'NOT NULL'}{RESET}")
            elif col['name'] in ['id', 'name', 'category']:
                print(f"{BLUE}   {col['name']:30} {str(col['type']):20} {'NULL' if col['nullable'] else 'NOT NULL'}{RESET}")
        
        print("-" * 80)
        
        if has_embedding_col:
            print(f"\n{GREEN}✅ Колонка name_embedding_text СУЩЕСТВУЕТ!{RESET}")
            
            # Проверяем данные
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(name_embedding_text) as with_embeddings,
                        COUNT(*) - COUNT(name_embedding_text) as without_embeddings
                    FROM products
                """))
                row = result.fetchone()
                
                total = row[0]
                with_emb = row[1]
                without_emb = row[2]
                coverage = (with_emb / total * 100) if total > 0 else 0
                
                print(f"\n{BOLD}📈 Статистика embeddings:{RESET}")
                print(f"   Всего товаров:       {total:,}")
                print(f"   С embeddings:        {with_emb:,} ({coverage:.1f}%)")
                print(f"   Без embeddings:      {without_emb:,}")
                
                if coverage == 100:
                    print(f"\n{GREEN}🎉 ВСЕ товары имеют embeddings! Векторный поиск готов!{RESET}")
                elif coverage > 0:
                    print(f"\n{YELLOW}⚠️  Embeddings заполнены частично. Запусти:{RESET}")
                    print(f"   python3 generate_embeddings_simple.py")
                else:
                    print(f"\n{RED}⚠️  Embeddings НЕ сгенерированы! Запусти:{RESET}")
                    print(f"   python3 generate_embeddings_simple.py")
        else:
            print(f"\n{RED}❌ Колонка name_embedding_text НЕ СУЩЕСТВУЕТ!{RESET}")
            print(f"\n{YELLOW}📝 Для добавления колонки выполни:{RESET}")
            print(f"   python3 setup_embeddings_simple.py")
            print(f"\n{YELLOW}   Или через SQL:{RESET}")
            print(f"   ALTER TABLE products ADD COLUMN name_embedding_text TEXT;")
    
    except Exception as e:
        print(f"{RED}❌ Ошибка: {e}{RESET}")
        sys.exit(1)
    
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}\n")

if __name__ == "__main__":
    main()





