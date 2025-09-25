#!/usr/bin/env python3
"""
Модуль расчета стоимости товаров
"""

import json
from typing import Dict, Optional

class PriceCalculator:
    """Класс для расчета стоимости товаров"""
    
    def __init__(self):
        # Курсы валют (обновленные)
        self.currencies = {
            "yuan_to_usd": 1 / 7.2,      # 7.2 юаня за $1, значит юань к доллару = 1/7.2
            "usd_to_rub": 84,            # 84 руб за $1
            "yuan_to_rub": 84 / 7.2      # 84 руб за $1 / 7.2 юаня за $1 = 11.67 руб за юань
        }
        self.load_categories()
    
    def load_categories(self):
        """Загружает категории товаров"""
        try:
            # Сначала пробуем загрузить из встроенного модуля
            from categories_data import CATEGORIES
            self.categories = CATEGORIES
            print(f"✅ Загружено {len(self.categories)} встроенных категорий")
            return
        except ImportError:
            print("❌ Встроенные категории не найдены")
        
        # Резервный способ - загрузка из JSON файла
        import os
        possible_paths = [
            'product_categories.json',
            '/app/product_categories.json',
            os.path.join(os.path.dirname(__file__), 'product_categories.json')
        ]
        
        for path in possible_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.categories = json.load(f)
                    print(f"✅ Загружено {len(self.categories)} категорий из файла {path}")
                    return
            except FileNotFoundError:
                continue
        
        print("⚠️ Категории не найдены, используем пустой список")
        self.categories = []
    
    def find_category_by_name(self, product_name: str) -> Optional[Dict]:
        """Находит категорию товара по названию с приоритетами и синонимами"""
        product_name_lower = product_name.lower()
        
        # Словарь синонимов для категорий (приоритет: точное совпадение > синонимы > частичное совпадение)
        category_synonyms = {
            "Ежедневники, блокноты": {
                "exact": ["ежедневник", "блокнот", "записная книжка", "планер"],
                "partial": ["дневник", "тетрадь", "записи", "планирование"]
            },
            "Пакеты - не бумага\nПакет, пакет фольгированный": {
                "exact": ["пакет", "мешок", "сумка пакет"],
                "partial": ["упаковка", "фольга"]
            },
            "Рюкзак": {
                "exact": ["рюкзак", "backpack"],
                "partial": ["школьный рюкзак", "спортивный рюкзак"]
            },
            "Картхолдер + ланьярд + ретрактор": {
                "exact": ["картхолдер", "кардхолдер", "ланьярд", "ретрактор"],
                "partial": ["карт", "держатель карт"]
            },
            "Поясная сумка": {
                "exact": ["поясная сумка", "бананка", "belt bag"],
                "partial": ["сумка на пояс"]
            },
            "Стикеры, наклейки": {
                "exact": ["стикер", "наклейка", "стикер pack", "наклейки"],
                "partial": ["клейкий", "липкий"]
            }
        }
        
        # Поиск с приоритетами
        matches = []
        
        for category in self.categories:
            category_name = category["category"]
            score = 0
            match_type = ""
            
            # Проверяем синонимы если они есть для категории
            if category_name in category_synonyms:
                synonyms = category_synonyms[category_name]
                
                # Точное совпадение с основными синонимами (высокий приоритет)
                for exact_word in synonyms["exact"]:
                    if exact_word in product_name_lower:
                        score += 100
                        match_type = "exact_synonym"
                        break
                
                # Частичное совпадение с дополнительными синонимами
                for partial_word in synonyms["partial"]:
                    if partial_word in product_name_lower:
                        score += 50
                        match_type = "partial_synonym"
            
            # Поиск по названию категории (средний приоритет) 
            category_name_lower = category_name.lower()
            category_words = [word for word in category_name_lower.replace(',', ' ').split() if len(word) > 2]
            
            # Проверяем как точные совпадения, так и вхождения подстрок
            for word in category_words:
                if word in product_name_lower or product_name_lower in word:
                    score += 70
                    if not match_type:
                        match_type = "category_name"
                # Также проверяем по корням слов (убираем окончания)
                elif len(word) > 4 and len(product_name_lower) > 4:
                    word_root = word[:6]  # Первые 6 символов как корень
                    product_root = product_name_lower[:6] 
                    if word_root == product_root:
                        score += 50
                        if not match_type:
                            match_type = "category_name_root"
            
            # Поиск по материалу (низкий приоритет)
            material_lower = category["material"].lower()
            material_words = [word for word in material_lower.split() if len(word) > 2]
            for word in material_words:
                if word in product_name_lower:
                    score += 30
                    if not match_type:
                        match_type = "material"
            
            if score > 0:
                matches.append((category, score, match_type))
        
        # Сортируем по убыванию скора и возвращаем лучший результат
        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[0][0]
        
        # Возвращаем дефолтную категорию если не найдено
        return {
            "category": "Общая категория",
            "material": "",
            "density": 200,
            "rates": {
                "rail_base": 5.0,
                "air_base": 7.0,
                "rail_density": 5.0,
                "air_density": 7.0
            }
        }
    
    def calculate_cost(self, 
                      price_yuan: float,
                      weight_kg: float,
                      quantity: int,
                      product_name: str,
                      custom_rate: Optional[float] = None,
                      delivery_type: str = "rail",  # rail или air
                      markup: float = 1.7) -> Dict:
        """
        Рассчитывает себестоимость и цену продажи
        
        Args:
            price_yuan: Цена за единицу в юанях
            weight_kg: Вес товара в кг
            quantity: Количество
            product_name: Название товара для определения категории
            custom_rate: Пользовательская ставка (если None, используется автоматическая)
            delivery_type: Тип доставки - "rail" или "air"
            markup: Наценка (1.5 = 50% наценка)
            
        Returns:
            Словарь с результатами расчета
        """
        
        # 1. Стоимость товара с комиссиями (5% Тони + 18% переводы)
        # Сначала базовая стоимость
        base_goods_cost_yuan = price_yuan * quantity
        
        # + 5% комиссия Тони
        goods_with_toni_yuan = base_goods_cost_yuan * (1 + 5/100)
        
        # + 18% процент переводов  
        goods_with_commissions_yuan = goods_with_toni_yuan * (1 + 18/100)
        
        # Итоговая стоимость товара за единицу с комиссиями
        goods_cost_per_unit_yuan = goods_with_commissions_yuan / quantity
        goods_cost_per_unit_rub = goods_cost_per_unit_yuan * self.currencies["yuan_to_rub"]
        
        total_goods_cost_rub = goods_cost_per_unit_rub * quantity
        total_goods_cost_usd = total_goods_cost_rub / self.currencies["usd_to_rub"]
        
        # 2. Определяем категорию и логистическую ставку
        category = self.find_category_by_name(product_name)
        
        if custom_rate is not None:
            logistics_rate_usd_per_kg = custom_rate
        else:
            if delivery_type == "air":
                logistics_rate_usd_per_kg = category["rates"]["air_base"]
            else:
                logistics_rate_usd_per_kg = category["rates"]["rail_base"]
        
        # 3. Стоимость логистики (ставка за кг × вес единицы × количество)
        logistics_cost_per_unit_usd = logistics_rate_usd_per_kg * weight_kg
        logistics_cost_per_unit_rub = logistics_cost_per_unit_usd * self.currencies["usd_to_rub"]
        total_logistics_cost_rub = logistics_cost_per_unit_rub * quantity
        total_logistics_cost_usd = logistics_cost_per_unit_usd * quantity
        
        # 4. Локальная доставка (2 юаня за кг)
        local_delivery_rate_yuan_per_kg = 2.0  # 2 юаня за кг
        local_delivery_total_yuan = local_delivery_rate_yuan_per_kg * weight_kg * quantity
        local_delivery_per_unit_yuan = local_delivery_rate_yuan_per_kg * weight_kg  
        local_delivery_per_unit_rub = local_delivery_per_unit_yuan * self.currencies["yuan_to_rub"]
        
        # 5. Забор в МСК (фиксированная сумма на весь тираж)
        msk_pickup_total_rub = 1000  # По Excel данным
        msk_pickup_per_unit_rub = msk_pickup_total_rub / quantity
        
        # 6. Прочие расходы (теперь только дополнительные расходы, без комиссий)
        # Комиссии Тони и переводов уже включены в стоимость товара
        # Остаются только: НДС, банковские комиссии, прочие мелкие расходы
        other_costs_percent = 2.5  # Уменьшенный процент без комиссий переводов и Тони
        base_cost_for_percent = goods_cost_per_unit_rub + local_delivery_per_unit_rub
        other_costs_per_unit_rub = base_cost_for_percent * (other_costs_percent / 100)
        total_other_costs_rub = other_costs_per_unit_rub * quantity
        
        # 7. Общая себестоимость
        cost_per_unit_rub = (goods_cost_per_unit_rub + 
                            logistics_cost_per_unit_rub + 
                            local_delivery_per_unit_rub +
                            msk_pickup_per_unit_rub + 
                            other_costs_per_unit_rub)
        cost_per_unit_usd = cost_per_unit_rub / self.currencies["usd_to_rub"]
        
        total_cost_rub = cost_per_unit_rub * quantity
        total_cost_usd = cost_per_unit_usd * quantity
        
        # 8. Цена продажи
        sale_price_per_unit_rub = cost_per_unit_rub * markup
        sale_price_per_unit_usd = sale_price_per_unit_rub / self.currencies["usd_to_rub"]
        
        total_sale_price_rub = sale_price_per_unit_rub * quantity
        total_sale_price_usd = sale_price_per_unit_usd * quantity
        
        # 9. Прибыль
        profit_per_unit_rub = sale_price_per_unit_rub - cost_per_unit_rub
        profit_per_unit_usd = sale_price_per_unit_usd - cost_per_unit_usd
        
        total_profit_rub = profit_per_unit_rub * quantity
        total_profit_usd = profit_per_unit_usd * quantity
        
        return {
            "product_name": product_name,
            "category": category["category"],
            "quantity": quantity,
            "unit_price_yuan": price_yuan,
            "total_price": {
                "yuan": round(price_yuan * quantity, 2),
                "usd": round(total_goods_cost_usd, 2),
                "rub": round(total_goods_cost_rub, 2)
            },
            "logistics": {
                "rate_usd": logistics_rate_usd_per_kg,
                "cost_usd": round(total_logistics_cost_usd, 2),
                "cost_rub": round(total_logistics_cost_rub, 2),
                "delivery_type": delivery_type
            },
            "additional_costs": {
                "local_delivery_rub": round(local_delivery_per_unit_rub * quantity, 2),
                "msk_pickup_rub": round(msk_pickup_total_rub, 2),
                "other_costs_rub": round(total_other_costs_rub, 2),
                "total_rub": round(local_delivery_per_unit_rub * quantity + msk_pickup_total_rub + total_other_costs_rub, 2)
            },
            "cost_price": {
                "total": {
                    "usd": round(total_cost_usd, 2),
                    "rub": round(total_cost_rub, 2)
                },
                "per_unit": {
                    "usd": round(cost_per_unit_usd, 2),
                    "rub": round(cost_per_unit_rub, 2)
                }
            },
            "sale_price": {
                "total": {
                    "usd": round(total_sale_price_usd, 2),
                    "rub": round(total_sale_price_rub, 2)
                },
                "per_unit": {
                    "usd": round(sale_price_per_unit_usd, 2),
                    "rub": round(sale_price_per_unit_rub, 2)
                }
            },
            "markup": markup,
            "profit": {
                "total": {
                    "usd": round(total_profit_usd, 2),
                    "rub": round(total_profit_rub, 2)
                },
                "per_unit": {
                    "usd": round(profit_per_unit_usd, 2),
                    "rub": round(profit_per_unit_rub, 2)
                }
            },
            "weight_kg": weight_kg,
            "estimated_weight": weight_kg * quantity
        }

# Тестовая функция
if __name__ == "__main__":
    calc = PriceCalculator()
    
    # Пример расчета
    result = calc.calculate_cost(
        price_yuan=7.414,
        weight_kg=0.4,
        quantity=15000,
        product_name="ежедневник пятерочка жесткая обложка",
        markup=1.7
    )
    
    print("🧮 Пример расчета:")
    print(f"Товар: {result['product_name']}")
    print(f"Категория: {result['category']}")
    print(f"Себестоимость за единицу: ${result['cost_price']['per_unit']['usd']} / {result['cost_price']['per_unit']['rub']} руб")
    print(f"Себестоимость всего тиража: ${result['cost_price']['total']['usd']} / {result['cost_price']['total']['rub']} руб")
    print(f"Цена продажи за единицу: ${result['sale_price']['per_unit']['usd']} / {result['sale_price']['per_unit']['rub']} руб")
    print(f"Прибыль всего: ${result['profit']['total']['usd']} / {result['profit']['total']['rub']} руб")
