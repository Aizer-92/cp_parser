#!/usr/bin/env python3
"""
Скрипт для запуска быстрого многопоточного парсера
"""
import sys
import argparse
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.append(str(Path(__file__).parent))

from fast_parser import FastParser

def main():
    parser = argparse.ArgumentParser(description='Быстрый многопоточный парсер OTAPI')
    parser.add_argument('--limit', type=int, default=1000, 
                       help='Количество товаров для парсинга (по умолчанию: 1000)')
    parser.add_argument('--threads', type=int, default=12, 
                       help='Количество потоков (по умолчанию: 12)')
    parser.add_argument('--start-from', type=int, default=0, 
                       help='Начать с позиции (по умолчанию: 0)')
    parser.add_argument('--merge-sqlite', action='store_true', 
                       help='Объединить чанки в SQLite после парсинга')
    
    args = parser.parse_args()
    
    print("🚀 Запускаем быстрый парсер OTAPI")
    print(f"   Лимит: {args.limit} товаров")
    print(f"   Потоков: {args.threads}")
    print(f"   Начать с: {args.start_from}")
    print(f"   Объединить в SQLite: {args.merge_sqlite}")
    print("=" * 60)
    
    # Создаем парсер
    parser_instance = FastParser(max_workers=args.threads)
    
    # Запускаем парсинг
    success = parser_instance.parse_products_batch(
        limit=args.limit,
        start_from=args.start_from
    )
    
    if success and args.merge_sqlite:
        print("\n🔄 Объединяем чанки в SQLite...")
        parser_instance.merge_chunks_to_sqlite()
    
    print("\n✅ Готово!")

if __name__ == "__main__":
    main()
