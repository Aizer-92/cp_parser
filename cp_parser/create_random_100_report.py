#!/usr/bin/env python3
"""
Отчет с 100 случайными товарами для проверки качества парсинга
"""

import sys
from pathlib import Path
from sqlalchemy import text
import json

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import db_manager

def main():
    db = db_manager
    
    # Читаем список последних 97 pending проектов
    import re
    valid_list = Path('valid_pending_files.txt')
    if not valid_list.exists():
        print("❌ Файл valid_pending_files.txt не найден!")
        print("💡 Используем valid_files_list.txt как fallback...")
        valid_list = Path('valid_files_list.txt')
        if not valid_list.exists():
            print("❌ Файл valid_files_list.txt тоже не найден!")
            return
    
    with open(valid_list, 'r') as f:
        files = [line.strip() for line in f if line.strip()]
    
    print(f"📁 Используем файл: {valid_list.name}")
    print(f"📊 Найдено файлов: {len(files)}")
    
    project_ids = []
    for filename in files:
        match = re.search(r'project_(\d+)_', filename)
        if match:
            project_ids.append(int(match.group(1)))
    
    with db.get_session() as session:
        # Создаем параметры
        placeholders = ','.join([f':{i}' for i in range(len(project_ids))])
        params = {str(i): pid for i, pid in enumerate(project_ids)}
        
        # Получаем 100 случайных товаров с их предложениями и изображениями
        result = session.execute(text(f"""
            SELECT 
                p.id,
                p.project_id,
                p.name,
                p.description,
                p.custom_field,
                (
                    SELECT json_agg(
                        json_build_object(
                            'quantity', po.quantity,
                            'price_usd', po.price_usd,
                            'price_rub', po.price_rub,
                            'route', po.route,
                            'delivery_time_days', po.delivery_time_days
                        )
                    )
                    FROM price_offers po
                    WHERE po.product_id = p.id
                ) as offers,
                (
                    SELECT COUNT(*)
                    FROM product_images pi
                    WHERE pi.product_id = p.id
                ) as images_count
            FROM products p
            WHERE p.project_id IN ({placeholders})
            ORDER BY RANDOM()
            LIMIT 100
        """), params).fetchall()
        
        # Формируем данные
        products = []
        for row in result:
            product = {
                'id': row[0],
                'project_id': row[1],
                'name': row[2],
                'description': row[3],
                'custom_field': row[4],
                'offers': row[5] if row[5] else [],
                'images_count': row[6]
            }
            products.append(product)
        
        # Сохраняем JSON
        output_file = Path('random_100_products.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON сохранен: {output_file.name}")
        
        # Создаем читаемый отчет
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append(f"📊 СЛУЧАЙНАЯ ВЫБОРКА: 100 ТОВАРОВ ИЗ {len(project_ids)} ПОСЛЕДНИХ ПРОЕКТОВ")
        report_lines.append("=" * 100)
        report_lines.append("")
        
        for i, product in enumerate(products, 1):
            report_lines.append(f"{'─' * 100}")
            report_lines.append(f"#{i}. ТОВАР ID: {product['id']} | PROJECT: {product['project_id']}")
            report_lines.append(f"{'─' * 100}")
            report_lines.append("")
            
            report_lines.append(f"📦 Название: {product['name']}")
            if product['description']:
                report_lines.append(f"📝 Описание: {product['description']}")
            if product['custom_field']:
                report_lines.append(f"🏷️  Доп. поле: {product['custom_field']}")
            
            report_lines.append(f"🖼️  Изображений: {product['images_count']}")
            report_lines.append("")
            
            # Предложения
            offers = product['offers']
            if offers:
                report_lines.append(f"💰 Предложения ({len(offers)}):")
                report_lines.append("")
                
                for j, offer in enumerate(offers, 1):
                    qty = offer.get('quantity', 'N/A')
                    price_usd = offer.get('price_usd')
                    price_rub = offer.get('price_rub')
                    route = offer.get('route', 'N/A')
                    delivery = offer.get('delivery_time_days', 'N/A')
                    
                    # Конвертируем в float если нужно
                    try:
                        price_usd_str = f"${float(price_usd):.2f}" if price_usd else "N/A"
                    except:
                        price_usd_str = "N/A"
                    
                    try:
                        price_rub_str = f"{float(price_rub):,.0f}₽" if price_rub else "N/A"
                    except:
                        price_rub_str = "N/A"
                    
                    report_lines.append(f"   {j}. Тираж: {qty:>6} | USD: {price_usd_str:>10} | RUB: {price_rub_str:>12} | "
                                      f"Маршрут: {route:<5} | Доставка: {delivery:>3} дн")
            else:
                report_lines.append("⚠️  Предложения: НЕТ")
            
            report_lines.append("")
        
        report_lines.append("=" * 100)
        report_lines.append("📊 СТАТИСТИКА")
        report_lines.append("=" * 100)
        
        # Подсчитываем статистику
        total_offers = sum(len(p['offers']) for p in products)
        with_images = sum(1 for p in products if p['images_count'] > 0)
        avg_offers = total_offers / len(products) if products else 0
        avg_images = sum(p['images_count'] for p in products) / len(products) if products else 0
        
        report_lines.append("")
        report_lines.append(f"Товаров: {len(products)}")
        report_lines.append(f"Предложений: {total_offers} (в среднем {avg_offers:.2f} на товар)")
        report_lines.append(f"С изображениями: {with_images} ({with_images/len(products)*100:.1f}%)")
        report_lines.append(f"Среднее изображений на товар: {avg_images:.2f}")
        report_lines.append("")
        report_lines.append("=" * 100)
        
        # Сохраняем отчет
        report_file = Path('RANDOM_100_PRODUCTS_REPORT.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"✅ Отчет сохранен: {report_file.name}")
        print()
        print("📊 Краткая статистика:")
        print(f"  • Товаров: {len(products)}")
        print(f"  • Предложений: {total_offers} (среднее: {avg_offers:.2f})")
        print(f"  • С изображениями: {with_images} ({with_images/len(products)*100:.1f}%)")
        print(f"  • Среднее изображений: {avg_images:.2f}")

if __name__ == '__main__':
    main()


Отчет с 100 случайными товарами для проверки качества парсинга
"""

import sys
from pathlib import Path
from sqlalchemy import text
import json

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import db_manager

def main():
    db = db_manager
    
    # Читаем список последних 97 pending проектов
    import re
    valid_list = Path('valid_pending_files.txt')
    if not valid_list.exists():
        print("❌ Файл valid_pending_files.txt не найден!")
        print("💡 Используем valid_files_list.txt как fallback...")
        valid_list = Path('valid_files_list.txt')
        if not valid_list.exists():
            print("❌ Файл valid_files_list.txt тоже не найден!")
            return
    
    with open(valid_list, 'r') as f:
        files = [line.strip() for line in f if line.strip()]
    
    print(f"📁 Используем файл: {valid_list.name}")
    print(f"📊 Найдено файлов: {len(files)}")
    
    project_ids = []
    for filename in files:
        match = re.search(r'project_(\d+)_', filename)
        if match:
            project_ids.append(int(match.group(1)))
    
    with db.get_session() as session:
        # Создаем параметры
        placeholders = ','.join([f':{i}' for i in range(len(project_ids))])
        params = {str(i): pid for i, pid in enumerate(project_ids)}
        
        # Получаем 100 случайных товаров с их предложениями и изображениями
        result = session.execute(text(f"""
            SELECT 
                p.id,
                p.project_id,
                p.name,
                p.description,
                p.custom_field,
                (
                    SELECT json_agg(
                        json_build_object(
                            'quantity', po.quantity,
                            'price_usd', po.price_usd,
                            'price_rub', po.price_rub,
                            'route', po.route,
                            'delivery_time_days', po.delivery_time_days
                        )
                    )
                    FROM price_offers po
                    WHERE po.product_id = p.id
                ) as offers,
                (
                    SELECT COUNT(*)
                    FROM product_images pi
                    WHERE pi.product_id = p.id
                ) as images_count
            FROM products p
            WHERE p.project_id IN ({placeholders})
            ORDER BY RANDOM()
            LIMIT 100
        """), params).fetchall()
        
        # Формируем данные
        products = []
        for row in result:
            product = {
                'id': row[0],
                'project_id': row[1],
                'name': row[2],
                'description': row[3],
                'custom_field': row[4],
                'offers': row[5] if row[5] else [],
                'images_count': row[6]
            }
            products.append(product)
        
        # Сохраняем JSON
        output_file = Path('random_100_products.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON сохранен: {output_file.name}")
        
        # Создаем читаемый отчет
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append(f"📊 СЛУЧАЙНАЯ ВЫБОРКА: 100 ТОВАРОВ ИЗ {len(project_ids)} ПОСЛЕДНИХ ПРОЕКТОВ")
        report_lines.append("=" * 100)
        report_lines.append("")
        
        for i, product in enumerate(products, 1):
            report_lines.append(f"{'─' * 100}")
            report_lines.append(f"#{i}. ТОВАР ID: {product['id']} | PROJECT: {product['project_id']}")
            report_lines.append(f"{'─' * 100}")
            report_lines.append("")
            
            report_lines.append(f"📦 Название: {product['name']}")
            if product['description']:
                report_lines.append(f"📝 Описание: {product['description']}")
            if product['custom_field']:
                report_lines.append(f"🏷️  Доп. поле: {product['custom_field']}")
            
            report_lines.append(f"🖼️  Изображений: {product['images_count']}")
            report_lines.append("")
            
            # Предложения
            offers = product['offers']
            if offers:
                report_lines.append(f"💰 Предложения ({len(offers)}):")
                report_lines.append("")
                
                for j, offer in enumerate(offers, 1):
                    qty = offer.get('quantity', 'N/A')
                    price_usd = offer.get('price_usd')
                    price_rub = offer.get('price_rub')
                    route = offer.get('route', 'N/A')
                    delivery = offer.get('delivery_time_days', 'N/A')
                    
                    # Конвертируем в float если нужно
                    try:
                        price_usd_str = f"${float(price_usd):.2f}" if price_usd else "N/A"
                    except:
                        price_usd_str = "N/A"
                    
                    try:
                        price_rub_str = f"{float(price_rub):,.0f}₽" if price_rub else "N/A"
                    except:
                        price_rub_str = "N/A"
                    
                    report_lines.append(f"   {j}. Тираж: {qty:>6} | USD: {price_usd_str:>10} | RUB: {price_rub_str:>12} | "
                                      f"Маршрут: {route:<5} | Доставка: {delivery:>3} дн")
            else:
                report_lines.append("⚠️  Предложения: НЕТ")
            
            report_lines.append("")
        
        report_lines.append("=" * 100)
        report_lines.append("📊 СТАТИСТИКА")
        report_lines.append("=" * 100)
        
        # Подсчитываем статистику
        total_offers = sum(len(p['offers']) for p in products)
        with_images = sum(1 for p in products if p['images_count'] > 0)
        avg_offers = total_offers / len(products) if products else 0
        avg_images = sum(p['images_count'] for p in products) / len(products) if products else 0
        
        report_lines.append("")
        report_lines.append(f"Товаров: {len(products)}")
        report_lines.append(f"Предложений: {total_offers} (в среднем {avg_offers:.2f} на товар)")
        report_lines.append(f"С изображениями: {with_images} ({with_images/len(products)*100:.1f}%)")
        report_lines.append(f"Среднее изображений на товар: {avg_images:.2f}")
        report_lines.append("")
        report_lines.append("=" * 100)
        
        # Сохраняем отчет
        report_file = Path('RANDOM_100_PRODUCTS_REPORT.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"✅ Отчет сохранен: {report_file.name}")
        print()
        print("📊 Краткая статистика:")
        print(f"  • Товаров: {len(products)}")
        print(f"  • Предложений: {total_offers} (среднее: {avg_offers:.2f})")
        print(f"  • С изображениями: {with_images} ({with_images/len(products)*100:.1f}%)")
        print(f"  • Среднее изображений: {avg_images:.2f}")

if __name__ == '__main__':
    main()

