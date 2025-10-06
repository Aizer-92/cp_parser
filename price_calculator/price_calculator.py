#!/usr/bin/env python3
"""
Модуль расчета стоимости товаров
"""

import json
from typing import Dict, Optional, List
import os
import sys
from pathlib import Path

# Добавляем config директорию в путь
config_dir = Path(__file__).parent / "config"
if str(config_dir) not in sys.path:
    sys.path.insert(0, str(config_dir))

try:
    from config_loader import get_config_loader
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    CONFIG_LOADER_AVAILABLE = False
    get_config_loader = None

try:
    from database import load_categories_from_db, upsert_category
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    def load_categories_from_db():
        return []
    def upsert_category(_: Dict[str, any]):
        return None

class PriceCalculator:
    """Класс для расчета стоимости товаров"""
    
    def __init__(self):
        if CONFIG_LOADER_AVAILABLE:
            # Новый способ - загрузка через ConfigLoader
            self.config_loader = get_config_loader()
            config = self.config_loader.load_full_config()
            self.currencies = {
                "yuan_to_usd": config.currencies.yuan_to_usd,
                "usd_to_rub": config.currencies.usd_to_rub,
                "yuan_to_rub": config.currencies.yuan_to_rub
            }
            self.formula_config = config.formula
            # Пробуем загрузить категории из БД если доступно
            db_categories = []
            try:
                db_categories = load_categories_from_db() if DATABASE_AVAILABLE else []
            except Exception as e:
                print(f"⚠️ Ошибка загрузки категорий из БД: {e}")
                db_categories = []
                
            if db_categories:
                self.categories = db_categories
                print(f"✅ Загружено {len(self.categories)} категорий из БД")
            else:
                self.categories = config.categories if config.categories else []
                print(f"✅ Категории загружены из конфигурации ({len(self.categories)})")
                if DATABASE_AVAILABLE and self.categories:
                    try:
                        for cat in self.categories:
                            upsert_category(cat)
                    except Exception as e:
                        print(f"⚠️ Ошибка сохранения категорий в БД: {e}")
                        
            print(f"✅ Итого загружено категорий: {len(self.categories) if self.categories else 0}")
        else:
            # Старый способ - fallback
            self.currencies = {
                "yuan_to_usd": 1 / 7.2,      # 7.2 юаня за $1, значит юань к доллару = 1/7.2
                "usd_to_rub": 84,            # 84 руб за $1
                "yuan_to_rub": 84 / 7.2      # 84 руб за $1 / 7.2 юаня за $1 = 11.67 руб за юань
            }
            self.load_categories_legacy()
            self.formula_config = None
        
        # Загружаем таблицу надбавок за плотность
        self.density_surcharges = self.load_density_surcharges()
    
    def load_categories_legacy(self):
        """Загружает категории товаров"""
        try:
            # Сначала пробуем загрузить из встроенного модуля
            from categories_data import CATEGORIES_DATA
            self.categories = CATEGORIES_DATA
            print(f"Загружено {len(self.categories)} встроенных категорий с рекомендациями")
            return
        except ImportError:
            print("❌ Встроенные категории не найдены")
        
        # Резервный способ - загрузка из JSON файла
        import os
        possible_paths = [
            'product_categories_v2.json',
            '/app/product_categories_v2.json',
            os.path.join(os.path.dirname(__file__), 'product_categories_v2.json'),
            'product_categories.json',
            '/app/product_categories.json',
            os.path.join(os.path.dirname(__file__), 'product_categories.json')
        ]
        
        for path in possible_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.categories = json.load(f)
                    print(f"Загружено {len(self.categories)} категорий из файла {path}")
                    return
            except FileNotFoundError:
                continue
        
        print("Категории не найдены, используем пустой список")
        self.categories = []
    
    def load_density_surcharges(self) -> Dict:
        """
        Загружает таблицу надбавок за плотность из YAML конфига
        
        Returns:
            Dict с надбавками для rail и air
        """
        try:
            import yaml
            config_path = Path(__file__).parent / "config" / "density_surcharges.yaml"
            
            if not config_path.exists():
                print(f"⚠️ Файл надбавок за плотность не найден: {config_path}")
                return {"rail": {}, "air": {}}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            surcharges = data.get('density_surcharges', {})
            print(f"✅ Загружены надбавки за плотность: ЖД={len(surcharges.get('rail', {}))} точек, Авиа={len(surcharges.get('air', {}))} точек")
            return surcharges
            
        except Exception as e:
            print(f"❌ Ошибка загрузки надбавок за плотность: {e}")
            return {"rail": {}, "air": {}}
    
    def get_density_surcharge(self, density_kg_m3: float, delivery_type: str) -> float:
        """
        Рассчитывает надбавку к базовой ставке за плотность товара
        Использует линейную интерполяцию между табличными значениями
        
        Args:
            density_kg_m3: Плотность товара в кг/м³
            delivery_type: Тип доставки - "rail" или "air"
            
        Returns:
            Надбавка в $/кг
            
        Example:
            >>> calc.get_density_surcharge(85, "rail")
            2.01  # При плотности 85 кг/м³ надбавка +$2.01/кг
        """
        if not self.density_surcharges or delivery_type not in self.density_surcharges:
            return 0.0
        
        surcharge_table = self.density_surcharges[delivery_type]
        
        if not surcharge_table:
            return 0.0
        
        # Получаем список плотностей (ключи таблицы)
        densities = sorted([float(d) for d in surcharge_table.keys()])
        
        # Если плотность больше максимальной в таблице - надбавка = 0
        if density_kg_m3 >= densities[-1]:
            return float(surcharge_table[densities[-1]])
        
        # Если плотность меньше минимальной - берем максимальную надбавку
        if density_kg_m3 <= densities[0]:
            return float(surcharge_table[densities[0]])
        
        # Находим ближайшие точки для интерполяции
        lower_density = None
        upper_density = None
        
        for i in range(len(densities) - 1):
            if densities[i] <= density_kg_m3 <= densities[i + 1]:
                lower_density = densities[i]
                upper_density = densities[i + 1]
                break
        
        if lower_density is None or upper_density is None:
            # Не должно случиться, но на всякий случай
            return 0.0
        
        # Точное совпадение
        if lower_density == upper_density:
            return float(surcharge_table[lower_density])
        
        # Линейная интерполяция
        lower_surcharge = float(surcharge_table[lower_density])
        upper_surcharge = float(surcharge_table[upper_density])
        
        ratio = (density_kg_m3 - lower_density) / (upper_density - lower_density)
        interpolated = lower_surcharge + ratio * (upper_surcharge - lower_surcharge)
        
        return round(interpolated, 2)
    
    def find_category_by_name(self, product_name: str) -> Dict:
        """Находит категорию товара по названию с приоритетами и синонимами"""
        product_name_lower = product_name.lower()
        
        # Словарь синонимов для категорий (приоритет: точное совпадение > синонимы > частичное совпадение)
        category_synonyms = self._get_synonym_mapping()
        
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
            # Добавляем приоритет для базовых материалов при одинаковом скоре
            def sort_key(match):
                category, score, match_type = match
                material_lower = category["material"].lower()
                
                # Бонус для базовых материалов (полиэстер, нейлон, хлопок)
                base_materials = ["полиэстер", "нейлон", "хлопок", "оксфорд", "плюш", "фетр", "акрил"]
                material_bonus = 0
                for base_mat in base_materials:
                    if base_mat in material_lower:
                        material_bonus = 5
                        break
                
                # Штраф для премиальных материалов (кожа, металл)
                premium_materials = ["кожа", "металл", "сталь"]
                for premium_mat in premium_materials:
                    if premium_mat in material_lower:
                        material_bonus = -5
                        break
                
                return score + material_bonus
            
            matches.sort(key=sort_key, reverse=True)
            top_category = matches[0][0]

            # Гарантируем наличие блока рекомендаций для UI
            recommendations = self.build_recommendations(top_category)
            top_category = {
                **top_category,
                "recommendations": recommendations
            }
            return top_category
        
        # Возвращаем дефолтную категорию если не найдено
        return {
            "category": "Общая категория",
            "material": "",
            "tnved_code": "",
            "density": 200,
            "rates": {
                "rail_base": 5.0,
                "air_base": 7.0,
                "rail_density": 5.0,
                "air_density": 7.0
            },
            "recommendations": self.get_recommendations_defaults()
        }
    
    def get_recommendations(self, product_name: str) -> Dict:
        """Получает рекомендации по цене, количеству и весу для товара"""
        category = self.find_category_by_name(product_name)

        return self.build_recommendations(category)

    def get_recommendations_defaults(self) -> Dict:
        """Возвращает стандартный набор рекомендаций."""
        return {
            "price_yuan_min": 1.0,
            "price_yuan_max": 100.0,
            "price_rub_min": 50.0,
            "price_rub_max": 5000.0,
            "median_price_yuan": 15.0,
            "median_price_rub": 750.0,
            "quantity_min": 100.0,
            "quantity_max": 10000.0,
            "avg_quantity": 1500.0,
            "weight_min": 50.0,
            "weight_max": 500.0
        }

    def build_recommendations(self, category: Dict) -> Dict:
        """Формирует рекомендации из доступных диапазонов категории."""

        existing = category.get("recommendations")
        if existing:
            return existing

        defaults = self.get_recommendations_defaults()
        price_ranges = category.get("price_ranges", {})
        quantity_ranges = category.get("quantity_ranges", {})
        weight_ranges = category.get("weight_ranges", {})

        return {
            "price_yuan_min": price_ranges.get("price_yuan_min", defaults["price_yuan_min"]),
            "price_yuan_max": price_ranges.get("price_yuan_max", defaults["price_yuan_max"]),
            "price_rub_min": price_ranges.get("price_rub_min", defaults["price_rub_min"]),
            "price_rub_max": price_ranges.get("price_rub_max", defaults["price_rub_max"]),
            "median_price_yuan": category.get("median_price_yuan", defaults["median_price_yuan"]),
            "median_price_rub": category.get("median_price_rub", defaults["median_price_rub"]),
            "quantity_min": quantity_ranges.get("quantity_min", defaults["quantity_min"]),
            "quantity_max": quantity_ranges.get("quantity_max", defaults["quantity_max"]),
            "avg_quantity": category.get("avg_quantity", defaults["avg_quantity"]),
            "weight_min": weight_ranges.get("weight_min", defaults["weight_min"]),
            "weight_max": weight_ranges.get("weight_max", defaults["weight_max"])
        }
    
    def calculate_cost(self, 
                      price_yuan: float,
                      weight_kg: float,
                      quantity: int,
                      product_name: str,
                      custom_rate: Optional[float] = None,
                      delivery_type: str = "rail",  # rail или air
                      markup: float = 1.7,
                      product_url: Optional[str] = None) -> Dict:
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
            product_url: URL товара (опционально)
            
        Returns:
            Словарь с результатами расчета
        """
        
        # 1. Стоимость товара с комиссиями (5% Тони + 18% переводы)
        # Сначала базовая стоимость
        base_goods_cost_yuan = price_yuan * quantity
        
        # + 5% комиссия Тони
        commission_percent = self.formula_config.toni_commission_percent if self.formula_config else 5.0
        goods_with_toni_yuan = base_goods_cost_yuan * (1 + commission_percent / 100)
        
        # + 18% процент переводов  
        transfer_percent = self.formula_config.transfer_percent if self.formula_config else 18.0
        goods_with_commissions_yuan = goods_with_toni_yuan * (1 + transfer_percent / 100)
        
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
        local_delivery_rate_yuan_per_kg = self.formula_config.local_delivery_rate_yuan_per_kg if self.formula_config else 2.0
        local_delivery_total_yuan = local_delivery_rate_yuan_per_kg * weight_kg * quantity
        local_delivery_per_unit_yuan = local_delivery_rate_yuan_per_kg * weight_kg  
        local_delivery_per_unit_rub = local_delivery_per_unit_yuan * self.currencies["yuan_to_rub"]
        
        # 5. Забор в МСК (фиксированная сумма на весь тираж)
        msk_pickup_total_rub = self.formula_config.msk_pickup_total_rub if self.formula_config else 1000
        msk_pickup_per_unit_rub = msk_pickup_total_rub / quantity
        
        # 6. Прочие расходы (теперь только дополнительные расходы, без комиссий)
        other_costs_percent = self.formula_config.other_costs_percent if self.formula_config else 2.5
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
        
        # 10. Расчет себестоимости под контракт
        # ВАЖНО: Расчет возможен только при наличии данных по пошлинам
        contract_cost_data = None
        cost_difference_data = None
        
        # Проверяем наличие обязательных данных для контракта
        has_customs_data = (
            category and 
            category.get('duty_rate') and 
            category.get('vat_rate') and
            category.get('tnved_code')
        )
        
        if has_customs_data:
            # Получаем данные по пошлинам прямо из категории
            duty_rate_str = category.get('duty_rate', '0%')
            vat_rate_str = category.get('vat_rate', '20%')
            
            print(f"✅ Найдены данные по пошлинам: {duty_rate_str} пошлина, {vat_rate_str} НДС")
            
            # Конвертируем проценты в числа для расчетов
            try:
                duty_rate = float(duty_rate_str.replace('%', '')) / 100
                vat_rate = float(vat_rate_str.replace('%', '')) / 100
            except (ValueError, AttributeError):
                print(f"⚠️ Ошибка парсинга пошлин: duty_rate={duty_rate_str}, vat_rate={vat_rate_str}")
                duty_rate = 0.0
                vat_rate = 0.2
            
            # Получаем данные по пошлинам (создаем совместимый объект)
            customs_info = {
                'duty_rate': duty_rate_str,
                'vat_rate': vat_rate_str
            }
            
            if customs_info and customs_info.get('duty_rate') and customs_info.get('vat_rate'):
                # Формула: (Стоимость товара в юанях * пошлина тони * курс юань в рубли + сумма пошлин переведенная в рубли + 
                # вес товара * (3,4$ если ЖД или 5,5$ если авиа) * курс в рубли + 25000 рублей + локальная доставка + забор в москве + прочие расходы) / кол-во (тираж)
                
                # Стоимость товара с пошлиной Тони в рублях
                goods_with_toni_rub = base_goods_cost_yuan * (1 + commission_percent / 100) * self.currencies["yuan_to_rub"]
                
                # Логистика под контракт (фиксированные ставки)
                contract_logistics_rate_usd = 3.4 if delivery_type == "rail" else 5.5
                contract_logistics_cost_usd = weight_kg * contract_logistics_rate_usd * quantity
                contract_logistics_cost_rub = contract_logistics_cost_usd * self.currencies["usd_to_rub"]
                
                # Фиксированная сумма 25000 рублей
                contract_fixed_cost_rub = 25000.0
                
                # Общая себестоимость под контракт
                contract_total_cost_rub = (goods_with_toni_rub + 
                                        contract_logistics_cost_rub + 
                                        local_delivery_total_yuan * self.currencies["yuan_to_rub"] + 
                                        msk_pickup_total_rub + 
                                        total_other_costs_rub + 
                                        contract_fixed_cost_rub)
                
                contract_cost_per_unit_rub = contract_total_cost_rub / quantity
                contract_cost_per_unit_usd = contract_cost_per_unit_rub / self.currencies["usd_to_rub"]
                
                # Разница между обычной себестоимостью и себестоимостью под контракт
                cost_difference_per_unit_rub = contract_cost_per_unit_rub - cost_per_unit_rub
                cost_difference_total_rub = cost_difference_per_unit_rub * quantity
                cost_difference_per_unit_usd = cost_difference_per_unit_rub / self.currencies["usd_to_rub"]
                cost_difference_total_usd = cost_difference_total_rub / self.currencies["usd_to_rub"]
                
                # Формируем данные контракта
                contract_cost_data = {
                    "total": {
                        "rub": round(contract_total_cost_rub, 2),
                        "usd": round(contract_total_cost_rub / self.currencies["usd_to_rub"], 2)
                    },
                    "per_unit": {
                        "rub": round(contract_cost_per_unit_rub, 2),
                        "usd": round(contract_cost_per_unit_usd, 2)
                    },
                    "logistics_rate_usd": contract_logistics_rate_usd,
                    "fixed_cost_rub": contract_fixed_cost_rub
                }
                
                cost_difference_data = {
                    "total": {
                        "rub": round(cost_difference_total_rub, 2),
                        "usd": round(cost_difference_total_usd, 2)
                    },
                    "per_unit": {
                        "rub": round(cost_difference_per_unit_rub, 2),
                        "usd": round(cost_difference_per_unit_usd, 2)
                    }
                }
        
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
            "contract_cost": contract_cost_data,
            "cost_difference": cost_difference_data,
            # Добавляем информацию по пошлинам для отображения в интерфейсе
            "customs_info": {
                "tnved_code": category.get('tnved_code', ''),
                "duty_rate": category.get('duty_rate', ''),
                "vat_rate": category.get('vat_rate', ''),
                "certificates": category.get('certificates', [])
            } if has_customs_data else None,
            "weight_kg": weight_kg,
            "estimated_weight": weight_kg * quantity,
            "product_url": product_url or ""
        }

    def _get_synonym_mapping(self) -> Dict[str, Dict[str, List[str]]]:
        """Формирует карту синонимов из конфигурации."""
        mapping = {}
        for category in getattr(self, 'categories', []):
            name = category.get('category')
            synonyms = category.get('synonyms', [])
            if not name or not synonyms:
                continue
            mapping[name] = {
                "exact": [syn.lower() for syn in synonyms],
                "partial": []
            }
        return mapping

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
    
    print("Пример расчета:")
    print(f"Товар: {result['product_name']}")
    print(f"Категория: {result['category']}")
    print(f"Себестоимость за единицу: ${result['cost_price']['per_unit']['usd']} / {result['cost_price']['per_unit']['rub']} руб")
    print(f"Себестоимость всего тиража: ${result['cost_price']['total']['usd']} / {result['cost_price']['total']['rub']} руб")
    print(f"Цена продажи за единицу: ${result['sale_price']['per_unit']['usd']} / {result['sale_price']['per_unit']['rub']} руб")
    print(f"Прибыль всего: ${result['profit']['total']['usd']} / {result['profit']['total']['rub']} руб")
