#!/usr/bin/env python3
"""
Исправление критических багов в извлечении ценовых вариантов
"""

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

def fix_enhanced_parser_price_extraction():
    """Исправляем баги в EnhancedParser"""
    
    parser_file = Path("scripts/complete_parsing_pipeline_v5.py")
    content = parser_file.read_text(encoding='utf-8')
    
    # Заменяем проблемную логику извлечения цен
    old_code = '''    def extract_price_variants_enhanced(self, worksheet, columns: Dict[str, int], start_row: int, end_row: int, data: Dict[str, Any]):
        """Улучшенное извлечение вариантов цен"""
        # Ищем строки с ценами
        for row in range(start_row, end_row + 1):
            price_data = {}
            
            # Тираж
            if 'quantity' in columns:
                qty_value = worksheet.cell(row=row, column=columns['quantity']).value
                qty = self.validate_quantity_enhanced(qty_value)
                if qty:
                    price_data['quantity'] = qty
            
            # Цена в USD
            if 'price_usd' in columns:
                price_value = worksheet.cell(row=row, column=columns['price_usd']).value
                price = self.validate_price_enhanced(price_value)
                if price:
                    price_data['price_usd'] = price
            
            # Цена в RUB  
            if 'price_rub' in columns:
                price_value = worksheet.cell(row=row, column=columns['price_rub']).value
                price = self.validate_price_enhanced(price_value)
                if price:
                    # Конвертируем в USD (текущий курс 1 USD ≈ 95 RUB)
                    price_data['price_usd'] = round(price / 95, 2)
                    logger.info(f"Конвертирована цена: {price} RUB → ${price_data['price_usd']} USD")
            
            # Цена в AED (трактуется как USD - в таблицах знак $ используется для AED)'''

    new_code = '''    def extract_price_variants_enhanced(self, worksheet, columns: Dict[str, int], start_row: int, end_row: int, data: Dict[str, Any]):
        """Улучшенное извлечение вариантов цен - ИСПРАВЛЕНО"""
        
        # Для каждой строки в диапазоне товара создаем отдельные ценовые варианты
        for row in range(start_row, end_row + 1):
            
            # Получаем тираж для этой строки
            quantity = None
            if 'quantity' in columns:
                qty_value = worksheet.cell(row=row, column=columns['quantity']).value
                quantity = self.validate_quantity_enhanced(qty_value)
            
            if not quantity:  # Пропускаем строки без тиража
                continue
            
            # Создаем варианты для разных валют ОТДЕЛЬНО
            variants = []
            
            # Вариант 1: USD цена
            if 'price_usd' in columns:
                price_value = worksheet.cell(row=row, column=columns['price_usd']).value
                price_usd = self.validate_price_enhanced(price_value)
                if price_usd:
                    usd_variant = {
                        'quantity': quantity,
                        'price_usd': price_usd,
                        'price_rub': None,
                        'currency': 'USD',
                        'route': 'Стандарт'
                    }
                    variants.append(usd_variant)
            
            # Вариант 2: RUB цена (отдельный вариант!)
            if 'price_rub' in columns:
                price_value = worksheet.cell(row=row, column=columns['price_rub']).value
                price_rub = self.validate_price_enhanced(price_value)
                if price_rub:
                    rub_variant = {
                        'quantity': quantity,
                        'price_usd': round(price_rub / 95, 2),  # Для совместимости с БД
                        'price_rub': price_rub,  # Сохраняем оригинал
                        'currency': 'RUB', 
                        'route': 'Стандарт',
                        'notes': f'Оригинальная цена: {price_rub} RUB'
                    }
                    variants.append(rub_variant)
                    logger.info(f"RUB цена: {price_rub} ₽ = ${rub_variant['price_usd']} (тираж {quantity})")
            
            # Вариант 3: AED цена (трактуется как USD)'''

    # Также исправляем сохранение ценовых вариантов
    old_save_code = '''            # Добавляем вариант цены если есть основные данные
            if price_data.get('price_usd'):
                data['prices'].append(price_data)'''

    new_save_code = '''            # Добавляем ВСЕ найденные варианты
            data['prices'].extend(variants)'''
    
    if old_code in content and old_save_code in content:
        content = content.replace(old_code, new_code)
        content = content.replace(old_save_code, new_save_code)
        
        parser_file.write_text(content, encoding='utf-8')
        print("✅ Исправлен EnhancedParser - теперь создает отдельные варианты для USD и RUB")
        return True
    else:
        print("❌ Не удалось найти код для замены")
        return False

def fix_price_offer_saving():
    """Исправляем сохранение ценовых предложений"""
    
    parser_file = Path("scripts/complete_parsing_pipeline_v5.py")
    content = parser_file.read_text(encoding='utf-8')
    
    # Исправляем метод сохранения
    old_save_method = '''                    # Добавляем варианты цен
                    for price_data in product_data['prices']:
                        price_offer = PriceOffer(
                            product_id=product.id,
                            quantity=price_data['quantity'],
                            price_usd=price_data['price_usd'],
                            route_name=price_data.get('route', 'Стандарт'),
                            delivery_time=price_data.get('delivery_time')
                        )
                        self.session.add(price_offer)'''
    
    new_save_method = '''                    # Добавляем варианты цен (ИСПРАВЛЕНО)
                    for price_data in product_data['prices']:
                        price_offer = PriceOffer(
                            product_id=product.id,
                            quantity=price_data['quantity'],
                            price_usd=price_data['price_usd'],
                            price_rub=price_data.get('price_rub'),  # Добавлено!
                            route_name=price_data.get('route', 'Стандарт'),
                            delivery_time=price_data.get('delivery_time'),
                            notes=price_data.get('notes')  # Добавлено!
                        )
                        self.session.add(price_offer)'''
    
    if old_save_method in content:
        content = content.replace(old_save_method, new_save_method)
        parser_file.write_text(content, encoding='utf-8')
        print("✅ Исправлено сохранение ценовых предложений - теперь сохраняет price_rub")
        return True
    else:
        print("❌ Не удалось найти код сохранения для замены")
        return False

if __name__ == "__main__":
    print("🔧 ИСПРАВЛЕНИЕ КРИТИЧЕСКИХ БАГОВ В ИЗВЛЕЧЕНИИ ЦЕН")
    print("=" * 70)
    
    success1 = fix_enhanced_parser_price_extraction()
    success2 = fix_price_offer_saving()
    
    if success1 and success2:
        print("\n🎉 ВСЕ БАГИ ИСПРАВЛЕНЫ!")
        print("   Теперь парсер будет:")
        print("   ✅ Создавать отдельные варианты для USD и RUB")
        print("   ✅ Не перезаписывать цены")
        print("   ✅ Сохранять оригинальные цены в рублях")
        print("   ✅ Создавать множественные ценовые предложения")
    else:
        print("\n❌ Не все баги исправлены, нужна ручная проверка")


