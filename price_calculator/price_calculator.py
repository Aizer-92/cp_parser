#!/usr/bin/env python3
"""
Модуль расчета стоимости товаров
"""

import json
from typing import Dict, Optional, List, Any
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
                "yuan_to_rub": config.currencies.yuan_to_rub,
                "eur_to_rub": getattr(config.currencies, 'eur_to_rub', 100.0)  # По умолчанию 100₽
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
                "yuan_to_rub": 84 / 7.2,     # 84 руб за $1 / 7.2 юаня за $1 = 11.67 руб за юань
                "eur_to_rub": 100.0          # 100 руб за €1 (по умолчанию)
            }
            self.load_categories_legacy()
            self.formula_config = None
        
        # Загружаем таблицу надбавок за плотность
        self.density_surcharges = self.load_density_surcharges()
        
        # Загружаем тарифы Prologix
        self.prologix_rates = self.load_prologix_rates()
    
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
    
    def load_prologix_rates(self) -> Dict:
        """
        Загружает тарифы Prologix из YAML конфига
        
        Returns:
            Dict с тарифами и параметрами Prologix
        """
        try:
            import yaml
            config_path = Path(__file__).parent / "config" / "prologix_rates.yaml"
            
            if not config_path.exists():
                print(f"⚠️ Файл тарифов Prologix не найден: {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            rates = data.get('prologix_rates', {})
            tiers = rates.get('volume_tiers', [])
            print(f"✅ Загружены тарифы Prologix: {len(tiers)} тарифных диапазонов")
            return rates
            
        except Exception as e:
            print(f"❌ Ошибка загрузки тарифов Prologix: {e}")
            return {}
    
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
    
    def calculate_prologix_cost(self, 
                                volume_m3: float,
                                weight_kg: float,
                                quantity: int,
                                base_goods_cost_yuan: float,
                                local_delivery_total_yuan: float,
                                msk_pickup_total_rub: float,
                                other_costs_total_rub: float,
                                category: Optional[Dict] = None,
                                custom_logistics_params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        """
        Рассчитывает стоимость доставки Prologix
        
        Логика: как контракт, но логистика рассчитывается по кубометрам
        
        Args:
            volume_m3: Общий объем груза в м³
            weight_kg: Общий вес в кг
            quantity: Количество единиц
            base_goods_cost_yuan: Базовая стоимость товара в юанях
            local_delivery_total_yuan: Локальная доставка в юанях
            msk_pickup_total_rub: Забор в МСК в рублях
            other_costs_total_rub: Прочие расходы в рублях
            
        Returns:
            Dict с результатами расчета или None если данные недоступны
        """
        if not self.prologix_rates or not self.prologix_rates.get('volume_tiers'):
            return None
        
        # Определяем ставку по объему
        rate_rub_per_m3 = None
        for tier in self.prologix_rates['volume_tiers']:
            min_vol = tier.get('min_volume', 0)
            max_vol = tier.get('max_volume', 999999)
            
            if min_vol <= volume_m3 < max_vol:
                rate_rub_per_m3 = tier.get('rate_rub_per_m3')
                break
        
        if rate_rub_per_m3 is None:
            print(f"⚠️ Prologix: не найдена ставка для объема {volume_m3} м³")
            return None
        
        # Применяем кастомную ставку если указана
        if custom_logistics_params and 'prologix' in custom_logistics_params:
            custom_rate = custom_logistics_params['prologix'].get('custom_rate')
            if custom_rate is not None:
                print(f"🔧 Применяем кастомную ставку для Prologix: {rate_rub_per_m3} → {custom_rate} ₽/м³")
                rate_rub_per_m3 = float(custom_rate)
        
        # Проверка минимального объема
        if volume_m3 < 2.0:
            print(f"⚠️ Prologix: объем {volume_m3} м³ меньше минимального (2 м³)")
            return None
        
        print(f"📦 Prologix: {volume_m3:.2f} м³ → {rate_rub_per_m3:,} руб/м³")
        
        # Стоимость логистики Prologix (в рублях)
        prologix_logistics_cost_rub = volume_m3 * rate_rub_per_m3
        prologix_logistics_cost_usd = prologix_logistics_cost_rub / self.currencies["usd_to_rub"]
        
        # Комиссия Тони (как в контракте)
        commission_percent = self.prologix_rates.get('toni_commission_percent', 5.0)
        goods_with_toni_rub = base_goods_cost_yuan * (1 + commission_percent / 100) * self.currencies["yuan_to_rub"]
        
        # Фиксированная сумма (как в контракте)
        fixed_cost_rub = self.prologix_rates.get('fixed_cost_rub', 25000.0)
        
        # Расчет пошлин и НДС (если есть данные категории)
        duty_cost_rub = 0.0
        vat_cost_rub = 0.0
        duty_rate = 0.0
        vat_rate = 0.0
        duty_result = {}
        
        if category and category.get('duty_rate') and category.get('vat_rate'):
            # Парсим проценты из строк типа "10%" или "0.1"
            duty_rate_str = str(category.get('duty_rate', '0'))
            vat_rate_str = str(category.get('vat_rate', '0'))
            
            try:
                duty_rate = float(duty_rate_str.strip('%')) / 100 if '%' in duty_rate_str else float(duty_rate_str)
                vat_rate = float(vat_rate_str.strip('%')) / 100 if '%' in vat_rate_str else float(vat_rate_str)
            except (ValueError, AttributeError):
                print(f"⚠️ Prologix: ошибка парсинга пошлин: duty={duty_rate_str}, vat={vat_rate_str}")
                duty_rate = 0.0
                vat_rate = 0.2
            
            # Применяем кастомные пошлины/НДС если указаны
            if custom_logistics_params and 'prologix' in custom_logistics_params:
                custom_duty = custom_logistics_params['prologix'].get('duty_rate')
                custom_vat = custom_logistics_params['prologix'].get('vat_rate')
                
                if custom_duty is not None:
                    duty_rate = float(custom_duty) / 100
                    print(f"🔧 Применяем кастомную пошлину для Prologix: {custom_duty}%")
                
                if custom_vat is not None:
                    vat_rate = float(custom_vat) / 100
                    print(f"🔧 Применяем кастомный НДС для Prologix: {custom_vat}%")
            
            # Таможенная стоимость = товар + локальная доставка + логистика
            customs_value_rub = (goods_with_toni_rub + 
                               local_delivery_total_yuan * self.currencies["yuan_to_rub"] + 
                               prologix_logistics_cost_rub)
            
            # Используем новый метод расчета комбинированных пошлин
            # ВАЖНО: weight_kg УЖЕ содержит общий вес (передан как total_weight из calculate())
            duty_result = self.calculate_combined_duty(
                customs_value_rub=customs_value_rub,
                weight_kg=weight_kg,  # Уже общий вес!
                category=category
            )
            
            duty_cost_rub = duty_result["duty_amount"]
            
            # НДС = (таможенная стоимость + пошлины) × vat_rate
            vat_cost_rub = (customs_value_rub + duty_cost_rub) * vat_rate
            
            print(f"💰 Пошлины и НДС для Prologix:")
            print(f"   Таможенная стоимость: {customs_value_rub:,.2f} ₽")
            print(f"   Общий вес груза: {weight_kg:,.2f} кг")
            if duty_result["duty_type"] == "combined":
                print(f"   Пошлины (комбинированные): {duty_cost_rub:,.2f} ₽")
                print(f"     - Процент ({duty_result['ad_valorem_rate']}%): {duty_result['ad_valorem_amount']:,.2f} ₽")
                print(f"     - Весовая ({duty_result['specific_rate_eur']} EUR/кг): {duty_result['specific_amount']:,.2f} ₽")
                print(f"     - Применена: {duty_result['chosen_type']}")
            else:
                print(f"   Пошлины ({duty_rate*100}%): {duty_cost_rub:,.2f} ₽")
            print(f"   НДС ({vat_rate*100}%): {vat_cost_rub:,.2f} ₽")
        
        # Общая себестоимость Prologix (с пошлинами и НДС!)
        prologix_total_cost_rub = (goods_with_toni_rub + 
                                   prologix_logistics_cost_rub + 
                                   local_delivery_total_yuan * self.currencies["yuan_to_rub"] + 
                                   duty_cost_rub +  # Добавляем пошлины
                                   vat_cost_rub +   # Добавляем НДС
                                   msk_pickup_total_rub + 
                                   other_costs_total_rub + 
                                   fixed_cost_rub)
        
        prologix_cost_per_unit_rub = prologix_total_cost_rub / quantity
        prologix_cost_per_unit_usd = prologix_cost_per_unit_rub / self.currencies["usd_to_rub"]
        
        return {
            "route_name": "Prologix",
            "total_volume_m3": round(volume_m3, 3),
            "rate_rub_per_m3": rate_rub_per_m3,
            "logistics_cost_rub": round(prologix_logistics_cost_rub, 2),
            "logistics_cost_usd": round(prologix_logistics_cost_usd, 2),
            "total_cost_rub": round(prologix_total_cost_rub, 2),
            "total_cost_usd": round(prologix_total_cost_rub / self.currencies["usd_to_rub"], 2),
            "cost_per_unit_rub": round(prologix_cost_per_unit_rub, 2),
            "cost_per_unit_usd": round(prologix_cost_per_unit_usd, 2),
            "fixed_cost_rub": fixed_cost_rub,
            "delivery_days_min": self.prologix_rates.get('delivery_days_min', 20),
            "delivery_days_max": self.prologix_rates.get('delivery_days_max', 25),
            "delivery_days_avg": self.prologix_rates.get('delivery_days_avg', 22),
            # Детальная структура затрат для Prologix  
            "breakdown": {
                # Стоимость в Китае (детализация)
                "base_price_yuan": base_goods_cost_yuan / quantity,
                "base_price_rub": round((base_goods_cost_yuan / quantity) * self.currencies["yuan_to_rub"], 2),
                "toni_commission_pct": commission_percent,
                "toni_commission_rub": round((goods_with_toni_rub - (base_goods_cost_yuan * self.currencies["yuan_to_rub"])) / quantity, 2),
                "factory_price": round(goods_with_toni_rub / quantity, 2),
                "local_delivery": round((local_delivery_total_yuan * self.currencies["yuan_to_rub"]) / quantity, 2),
                # Логистика (детализация)
                "logistics": round(prologix_logistics_cost_rub / quantity, 2),
                "prologix_volume": round(volume_m3, 1),
                "prologix_rate": rate_rub_per_m3,
                "total_weight_kg": round(weight_kg, 2),  # weight_kg уже общий вес всего груза
                # Пошлины и НДС (реальные суммы + проценты)
                "duty_type": category.get('duty_type', 'percent') if category else "percent",
                "duty_rate_pct": duty_rate * 100 if duty_rate else 0,
                "duty_cost_rub": round(duty_cost_rub / quantity, 2) if duty_cost_rub else 0,
                "vat_rate_pct": vat_rate * 100 if vat_rate else 0,
                "vat_cost_rub": round(vat_cost_rub / quantity, 2) if vat_cost_rub else 0,
                # Комбинированные и весовые пошлины (если применимо)
                "duty_ad_valorem_amount": round(duty_result.get("ad_valorem_amount", 0) / quantity, 2) if duty_result.get("duty_type") == "combined" else None,
                "duty_ad_valorem_rate": duty_result.get("ad_valorem_rate") if duty_result.get("duty_type") == "combined" else None,
                "duty_specific_amount": round(duty_result.get("specific_amount", 0) / quantity, 2) if duty_result.get("duty_type") in ["combined", "specific"] else None,
                "duty_specific_rate_eur": duty_result.get("specific_rate_eur") if duty_result.get("duty_type") in ["combined", "specific"] else None,
                "duty_specific_rate_rub": duty_result.get("specific_rate_rub") if duty_result.get("duty_type") in ["combined", "specific"] else None,
                "duty_chosen_type": duty_result.get("chosen_type") if duty_result.get("duty_type") == "combined" else None,
                # Прочие
                "msk_pickup": round(msk_pickup_total_rub / quantity, 2),
                "other_costs": round(other_costs_total_rub / quantity, 2),
                "fixed_costs": round(fixed_cost_rub / quantity, 2)
            }
        }
    
    def calculate_combined_duty(self, 
                                customs_value_rub: float,
                                weight_kg: float,
                                category: Optional[Dict] = None) -> Dict[str, float]:
        """
        Рассчитывает пошлины (процент, весовые EUR/кг или комбинированные)
        
        Поддерживаемые типы:
        1. "percent" - только процентные (например, 10%)
        2. "specific" - только весовые (например, 2.2 EUR/кг)
        3. "combined" - комбинированные (10% ИЛИ 1.75 EUR/кг, что больше)
        
        Args:
            customs_value_rub: Таможенная стоимость в рублях
            weight_kg: Вес товара в кг
            category: Категория товара с данными по пошлинам
            
        Returns:
            Dict с детализацией пошлин:
            {
                "duty_type": "combined",
                "ad_valorem_amount": 1000.0,  # Процентная пошлина
                "specific_amount": 1500.0,     # Весовая пошлина
                "duty_amount": 1500.0,         # Применяется БОЛЬШАЯ
                "chosen_type": "specific",     # Какая пошлина выбрана
                "ad_valorem_rate": 10.0,       # % ставка
                "specific_rate_eur": 1.75,     # EUR/кг ставка
                "specific_rate_rub": 147.0     # ₽/кг ставка (EUR → RUB)
            }
        """
        if not category:
            return {
                "duty_type": "percent",
                "duty_amount": 0.0,
                "ad_valorem_amount": 0.0,
                "specific_amount": 0.0
            }
        
        duty_type = category.get('duty_type', 'percent')
        
        # 1. ЧИСТО ВЕСОВЫЕ ПОШЛИНЫ (specific)
        if duty_type == 'specific':
            print(f"\n{'='*60}")
            print(f"⚖️ РАСЧЕТ ВЕСОВЫХ ПОШЛИН (только EUR/кг)")
            print(f"{'='*60}")
            
            specific_rate_raw = category.get('specific_rate', '0')
            
            # Парсим: либо число (2.2), либо строку "2.2 EUR/kg" (обратная совместимость)
            try:
                if isinstance(specific_rate_raw, (int, float)):
                    specific_rate_eur = float(specific_rate_raw)
                else:
                    # Пытаемся распарсить как "2.2 EUR/kg" или просто "2.2"
                    specific_rate_str = str(specific_rate_raw).strip()
                    specific_rate_eur = float(specific_rate_str.split()[0])
            except (ValueError, IndexError, AttributeError):
                print(f"⚠️ Ошибка парсинга specific_rate: {specific_rate_raw}")
                specific_rate_eur = 0.0
            
            eur_to_rub = self.currencies.get("eur_to_rub", 100.0)  # Курс EUR → RUB из настроек
            specific_rate_rub = specific_rate_eur * eur_to_rub
            specific_amount_rub = weight_kg * specific_rate_rub
            
            print(f"Вес товара: {weight_kg:,.2f} кг")
            print(f"Ставка: {specific_rate_eur} EUR/кг ({specific_rate_rub:.2f} ₽/кг)")
            print(f"Курс EUR: {eur_to_rub:.2f} ₽")
            print(f"Пошлина: {specific_amount_rub:,.2f} ₽")
            print(f"{'='*60}\n")
            
            return {
                "duty_type": "specific",
                "duty_amount": specific_amount_rub,
                "specific_amount": specific_amount_rub,
                "specific_rate_eur": specific_rate_eur,
                "specific_rate_rub": specific_rate_rub
            }
        
        # 2. ОБЫЧНЫЕ ПРОЦЕНТНЫЕ ПОШЛИНЫ (percent)
        if duty_type == 'percent':
            duty_rate_str = str(category.get('duty_rate', '0%'))
            duty_rate = float(duty_rate_str.strip('%')) / 100 if '%' in duty_rate_str else float(duty_rate_str)
            duty_amount = customs_value_rub * duty_rate
            
            return {
                "duty_type": "percent",
                "duty_amount": duty_amount,
                "ad_valorem_amount": duty_amount,
                "ad_valorem_rate": duty_rate * 100
            }
        
        # КОМБИНИРОВАННЫЕ ПОШЛИНЫ (текстиль)
        print(f"\n{'='*60}")
        print(f"📊 РАСЧЕТ КОМБИНИРОВАННЫХ ПОШЛИН")
        print(f"{'='*60}")
        
        # 1. Процентная ставка (ad valorem)
        ad_valorem_rate_str = category.get('ad_valorem_rate', '10%')
        ad_valorem_rate = float(ad_valorem_rate_str.strip('%')) / 100 if '%' in ad_valorem_rate_str else float(ad_valorem_rate_str)
        ad_valorem_amount_rub = customs_value_rub * ad_valorem_rate
        
        print(f"1️⃣  Процентная пошлина:")
        print(f"   Таможенная стоимость: {customs_value_rub:,.2f} ₽")
        print(f"   Ставка: {ad_valorem_rate * 100}%")
        print(f"   Сумма: {ad_valorem_amount_rub:,.2f} ₽")
        
        # 2. Весовая ставка (specific rate) в EUR/кг
        specific_rate_raw = category.get('specific_rate', '0')
        
        # Парсим: либо число (1.75), либо строку "1.75 EUR/kg" (обратная совместимость)
        try:
            if isinstance(specific_rate_raw, (int, float)):
                specific_rate_eur = float(specific_rate_raw)
            else:
                # Пытаемся распарсить как "1.75 EUR/kg" или просто "1.75"
                specific_rate_str = str(specific_rate_raw).strip()
                specific_rate_eur = float(specific_rate_str.split()[0])
        except (ValueError, IndexError, AttributeError):
            print(f"⚠️ Ошибка парсинга specific_rate: {specific_rate_raw}")
            specific_rate_eur = 0.0
        
        # Получаем курс EUR → RUB из настроек
        eur_to_rub = self.currencies.get("eur_to_rub", 100.0)
        
        specific_rate_rub = specific_rate_eur * eur_to_rub
        specific_amount_rub = weight_kg * specific_rate_rub
        
        print(f"2️⃣  Весовая пошлина:")
        print(f"   Вес товара: {weight_kg:,.2f} кг")
        print(f"   Ставка: {specific_rate_eur} EUR/кг ({specific_rate_rub:.2f} ₽/кг)")
        print(f"   Курс EUR: {eur_to_rub:.2f} ₽")
        print(f"   Сумма: {specific_amount_rub:,.2f} ₽")
        
        # 3. Выбираем БОЛЬШУЮ пошлину
        if ad_valorem_amount_rub >= specific_amount_rub:
            chosen_type = "ad_valorem"
            duty_amount = ad_valorem_amount_rub
            print(f"\n✅ ПРИМЕНЯЕТСЯ ПРОЦЕНТНАЯ пошлина: {ad_valorem_amount_rub:,.2f} ₽")
        else:
            chosen_type = "specific"
            duty_amount = specific_amount_rub
            print(f"\n✅ ПРИМЕНЯЕТСЯ ВЕСОВАЯ пошлина: {specific_amount_rub:,.2f} ₽")
        
        print(f"{'='*60}\n")
        
        return {
            "duty_type": "combined",
            "ad_valorem_amount": ad_valorem_amount_rub,
            "ad_valorem_rate": ad_valorem_rate * 100,
            "specific_amount": specific_amount_rub,
            "specific_rate_eur": specific_rate_eur,
            "specific_rate_rub": specific_rate_rub,
            "duty_amount": duty_amount,
            "chosen_type": chosen_type
        }
    
    def calculate_sea_container_cost(self, 
                                     volume_m3: float,
                                     weight_kg: float,
                                     quantity: int,
                                     base_goods_cost_yuan: float,
                                     local_delivery_total_yuan: float,
                                     msk_pickup_total_rub: float,
                                     other_costs_total_rub: float,
                                     category: Optional[Dict] = None,
                                     custom_logistics_params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        """
        Рассчитывает стоимость доставки морем контейнером
        
        Логика: 
        - Минимум 10 м³
        - 20-футовый контейнер: до 30 м³ (1500$ + пошлины + 180000₽)
        - 40-футовый контейнер: до 70 м³ (2050$ + пошлины + 225000₽)
        - Автоматически выбирает оптимальное количество контейнеров
        - Пошлины: ДА (как контракт)
        - Комиссия за перевод: 0% (как контракт)
        - Фиксированные расходы: 95000₽
        - Срок доставки: 60 дней
        
        Args:
            volume_m3: Общий объем груза в м³
            weight_kg: Общий вес в кг
            quantity: Количество единиц
            base_goods_cost_yuan: Базовая стоимость товара в юанях
            local_delivery_total_yuan: Локальная доставка в юанях
            msk_pickup_total_rub: Забор в МСК в рублях
            other_costs_total_rub: Прочие расходы в рублях
            category: Категория товара (для расчета пошлин)
            custom_logistics_params: Кастомные параметры логистики
            
        Returns:
            Dict с результатами расчета или None если объем меньше 10 м³
        """
        # Проверка минимального объема
        if volume_m3 < 10.0:
            print(f"⚠️ Море контейнером: объем {volume_m3} м³ меньше минимального (10 м³)")
            return None
        
        print(f"\n{'='*60}")
        print(f"🚢 РАСЧЕТ МОРСКОГО КОНТЕЙНЕРА")
        print(f"{'='*60}")
        print(f"📦 Объем груза: {volume_m3:.2f} м³")
        
        # Константы контейнеров
        CONTAINER_20FT = {
            "capacity_m3": 30,
            "price_usd": 1500,
            "fixed_cost_rub": 180000,
            "name": "20-футовый"
        }
        
        CONTAINER_40FT = {
            "capacity_m3": 70,
            "price_usd": 2050,
            "fixed_cost_rub": 225000,
            "name": "40-футовый"
        }
        
        # Алгоритм выбора контейнеров (оптимизация по минимальной стоимости)
        def calculate_container_combination(vol):
            """Находит оптимальную комбинацию контейнеров"""
            # Возможные комбинации: только 20ft, только 40ft, или микс
            options = []
            
            # Вариант 1: Только 40-футовые
            count_40 = int(vol / CONTAINER_40FT["capacity_m3"]) + (1 if vol % CONTAINER_40FT["capacity_m3"] > 0 else 0)
            total_capacity_40 = count_40 * CONTAINER_40FT["capacity_m3"]
            cost_40_only = (count_40 * CONTAINER_40FT["price_usd"], 
                           count_40 * CONTAINER_40FT["fixed_cost_rub"])
            options.append({
                "containers_40": count_40,
                "containers_20": 0,
                "total_capacity": total_capacity_40,
                "remaining": total_capacity_40 - vol,
                "cost_usd": cost_40_only[0],
                "cost_rub": cost_40_only[1]
            })
            
            # Вариант 2: Только 20-футовые
            count_20 = int(vol / CONTAINER_20FT["capacity_m3"]) + (1 if vol % CONTAINER_20FT["capacity_m3"] > 0 else 0)
            total_capacity_20 = count_20 * CONTAINER_20FT["capacity_m3"]
            cost_20_only = (count_20 * CONTAINER_20FT["price_usd"], 
                           count_20 * CONTAINER_20FT["fixed_cost_rub"])
            options.append({
                "containers_40": 0,
                "containers_20": count_20,
                "total_capacity": total_capacity_20,
                "remaining": total_capacity_20 - vol,
                "cost_usd": cost_20_only[0],
                "cost_rub": cost_20_only[1]
            })
            
            # Вариант 3: Микс (40ft + 20ft для остатка)
            count_40_mix = int(vol / CONTAINER_40FT["capacity_m3"])
            remaining_vol = vol - (count_40_mix * CONTAINER_40FT["capacity_m3"])
            count_20_mix = int(remaining_vol / CONTAINER_20FT["capacity_m3"]) + (1 if remaining_vol % CONTAINER_20FT["capacity_m3"] > 0 else 0)
            
            if count_40_mix > 0 and count_20_mix > 0:
                total_capacity_mix = (count_40_mix * CONTAINER_40FT["capacity_m3"]) + (count_20_mix * CONTAINER_20FT["capacity_m3"])
                cost_mix = ((count_40_mix * CONTAINER_40FT["price_usd"]) + (count_20_mix * CONTAINER_20FT["price_usd"]),
                           (count_40_mix * CONTAINER_40FT["fixed_cost_rub"]) + (count_20_mix * CONTAINER_20FT["fixed_cost_rub"]))
                options.append({
                    "containers_40": count_40_mix,
                    "containers_20": count_20_mix,
                    "total_capacity": total_capacity_mix,
                    "remaining": total_capacity_mix - vol,
                    "cost_usd": cost_mix[0],
                    "cost_rub": cost_mix[1]
                })
            
            # Выбираем вариант с минимальной стоимостью
            best_option = min(options, key=lambda x: x["cost_usd"] + (x["cost_rub"] / self.currencies["usd_to_rub"]))
            return best_option
        
        # Находим оптимальное решение
        container_config = calculate_container_combination(volume_m3)
        
        print(f"📊 Оптимальная конфигурация контейнеров:")
        if container_config["containers_40"] > 0:
            print(f"   40-футовых: {container_config['containers_40']} шт")
        if container_config["containers_20"] > 0:
            print(f"   20-футовых: {container_config['containers_20']} шт")
        print(f"   Общая вместимость: {container_config['total_capacity']:.1f} м³")
        print(f"   💡 Остается места: {container_config['remaining']:.2f} м³")
        
        # Стоимость логистики (контейнеры в USD)
        containers_cost_usd = container_config["cost_usd"]
        containers_cost_rub = containers_cost_usd * self.currencies["usd_to_rub"]
        
        # Фиксированная стоимость контейнеров в рублях
        containers_fixed_cost_rub = container_config["cost_rub"]
        
        # Комиссия Тони (5% как в контракте)
        commission_percent = 5.0
        goods_with_toni_rub = base_goods_cost_yuan * (1 + commission_percent / 100) * self.currencies["yuan_to_rub"]
        
        # Фиксированные расходы (95000₽)
        sea_fixed_cost_rub = 95000.0
        
        # Расчет пошлин и НДС (обязательно, как в контракте)
        duty_cost_rub = 0.0
        duty_on_goods_rub = 0.0
        duty_on_containers_rub = 0.0
        vat_cost_rub = 0.0
        duty_rate = 0.0
        vat_rate = 0.0
        customs_value_usd = 0.0
        
        if category and category.get('duty_rate') and category.get('vat_rate'):
            # Парсим проценты из строк типа "10%" или "0.1"
            duty_rate_str = str(category.get('duty_rate', '0'))
            vat_rate_str = str(category.get('vat_rate', '0'))
            
            try:
                duty_rate = float(duty_rate_str.strip('%')) / 100 if '%' in duty_rate_str else float(duty_rate_str)
                vat_rate = float(vat_rate_str.strip('%')) / 100 if '%' in vat_rate_str else float(vat_rate_str)
            except (ValueError, AttributeError):
                print(f"⚠️ Море: ошибка парсинга пошлин: duty={duty_rate_str}, vat={vat_rate_str}")
                duty_rate = 0.0
                vat_rate = 0.2
            
            # Применяем кастомные пошлины/НДС если указаны
            if custom_logistics_params and 'sea_container' in custom_logistics_params:
                custom_duty = custom_logistics_params['sea_container'].get('duty_rate')
                custom_vat = custom_logistics_params['sea_container'].get('vat_rate')
                
                if custom_duty is not None:
                    duty_rate = float(custom_duty) / 100
                    print(f"🔧 Применяем кастомную пошлину для Моря: {custom_duty}%")
                
                if custom_vat is not None:
                    vat_rate = float(custom_vat) / 100
                    print(f"🔧 Применяем кастомный НДС для Моря: {custom_vat}%")
            
            # Таможенная стоимость = товар + локальная доставка + логистика (контейнеры)
            customs_value_rub = (goods_with_toni_rub + 
                               local_delivery_total_yuan * self.currencies["yuan_to_rub"] + 
                               containers_cost_rub)
            
            customs_value_usd = customs_value_rub / self.currencies["usd_to_rub"]
            
            # Используем новый метод расчета комбинированных пошлин
            # ВАЖНО: weight_kg УЖЕ содержит общий вес (передан как total_weight из calculate())
            duty_result = self.calculate_combined_duty(
                customs_value_rub=customs_value_rub,
                weight_kg=weight_kg,  # Уже общий вес!
                category=category
            )
            
            duty_on_goods_rub = duty_result["duty_amount"]
            
            # 2. ДОПОЛНИТЕЛЬНО на стоимость контейнеров в USD (формула: 1500$ + 1500$ × duty_rate)
            # Для комбинированных пошлин используем процентную ставку для контейнеров
            if duty_result["duty_type"] == "combined":
                container_duty_rate = duty_result["ad_valorem_rate"] / 100
            else:
                container_duty_rate = duty_rate
            
            duty_on_containers_usd = containers_cost_usd * container_duty_rate
            duty_on_containers_rub = duty_on_containers_usd * self.currencies["usd_to_rub"]
            
            # Общие пошлины = пошлины на товар + дополнительные пошлины на контейнеры
            duty_cost_rub = duty_on_goods_rub + duty_on_containers_rub
            
            # НДС = (таможенная стоимость + пошлины) × vat_rate
            vat_cost_rub = (customs_value_rub + duty_cost_rub) * vat_rate
            
            print(f"💰 Пошлины и НДС для Моря:")
            print(f"   Таможенная стоимость: {customs_value_rub:,.2f} ₽ (${customs_value_usd:,.2f})")
            print(f"   Общий вес груза: {weight_kg:,.2f} кг")
            if duty_result["duty_type"] == "combined":
                print(f"   Пошлины на товар+логистику (комбинированные): {duty_on_goods_rub:,.2f} ₽")
                print(f"     - Процент ({duty_result['ad_valorem_rate']}%): {duty_result['ad_valorem_amount']:,.2f} ₽")
                print(f"     - Весовая ({duty_result['specific_rate_eur']} EUR/кг): {duty_result['specific_amount']:,.2f} ₽")
                print(f"     - Применена: {duty_result['chosen_type']}")
            else:
                print(f"   Пошлины на товар+логистику ({duty_rate*100}%): {duty_on_goods_rub:,.2f} ₽")
            print(f"   Пошлины ДОПОЛНИТЕЛЬНО на контейнеры ({container_duty_rate*100}%): ${duty_on_containers_usd:,.2f} ({duty_on_containers_rub:,.2f} ₽)")
            print(f"   ИТОГО пошлины: {duty_cost_rub:,.2f} ₽")
            print(f"   НДС ({vat_rate*100}%): {vat_cost_rub:,.2f} ₽")
        else:
            print(f"⚠️ Море: категория без данных по пошлинам, расчет без таможенных сборов")
        
        # Общая себестоимость (с пошлинами и НДС!)
        sea_total_cost_rub = (goods_with_toni_rub + 
                             containers_cost_rub +  # Стоимость контейнеров в USD → RUB
                             duty_cost_rub +  # Пошлины на контейнеры
                             containers_fixed_cost_rub +  # Фиксированная стоимость в RUB
                             local_delivery_total_yuan * self.currencies["yuan_to_rub"] + 
                             vat_cost_rub +   # НДС
                             msk_pickup_total_rub + 
                             other_costs_total_rub + 
                             sea_fixed_cost_rub)
        
        sea_cost_per_unit_rub = sea_total_cost_rub / quantity
        sea_cost_per_unit_usd = sea_cost_per_unit_rub / self.currencies["usd_to_rub"]
        
        print(f"✅ Море: Общая себестоимость = {sea_total_cost_rub:,.2f} ₽ ({sea_cost_per_unit_rub:.2f} ₽/шт)")
        print(f"{'='*60}\n")
        
        return {
            "route_name": "Море контейнером",
            "total_volume_m3": round(volume_m3, 3),
            "containers_40ft": container_config["containers_40"],
            "containers_20ft": container_config["containers_20"],
            "total_capacity_m3": container_config["total_capacity"],
            "remaining_capacity_m3": round(container_config["remaining"], 2),
            "containers_cost_usd": round(containers_cost_usd, 2),
            "containers_cost_rub": round(containers_cost_rub, 2),
            "containers_fixed_cost_rub": round(containers_fixed_cost_rub, 2),
            "duty_on_containers_usd": round(containers_cost_usd * duty_rate, 2) if duty_rate > 0 else 0,
            "total_cost_rub": round(sea_total_cost_rub, 2),
            "total_cost_usd": round(sea_total_cost_rub / self.currencies["usd_to_rub"], 2),
            "cost_per_unit_rub": round(sea_cost_per_unit_rub, 2),
            "cost_per_unit_usd": round(sea_cost_per_unit_usd, 2),
            "fixed_cost_rub": sea_fixed_cost_rub,
            "delivery_days": 60,
            # Детальная структура затрат для Моря
            "breakdown": {
                # Стоимость в Китае (детализация)
                "base_price_yuan": round(base_goods_cost_yuan / quantity, 2),
                "base_price_rub": round((base_goods_cost_yuan / quantity) * self.currencies["yuan_to_rub"], 2),
                "toni_commission_pct": commission_percent,
                "toni_commission_rub": round(((base_goods_cost_yuan / quantity) * self.currencies["yuan_to_rub"]) * (commission_percent / 100), 2),
                "transfer_commission_pct": 0.0,  # Как в контракте - 0%
                "transfer_commission_rub": 0.0,
                "factory_price": round(goods_with_toni_rub / quantity, 2),
                "local_delivery": round((local_delivery_total_yuan * self.currencies["yuan_to_rub"]) / quantity, 2),
                # Логистика контейнеры (детализация)
                "containers_cost": round(containers_cost_rub / quantity, 2),
                "containers_fixed_cost": round(containers_fixed_cost_rub / quantity, 2),
                "containers_count_40ft": container_config["containers_40"],
                "containers_count_20ft": container_config["containers_20"],
                # Таможня
                "duty_rate": duty_rate,
                "vat_rate": vat_rate,
                "duty_cost": round(duty_cost_rub / quantity, 2),
                "duty_on_goods": round(duty_on_goods_rub / quantity, 2),  # Пошлины на товар+логистику
                "duty_on_containers": round(duty_on_containers_rub / quantity, 2),  # Доп. пошлины на контейнеры
                "vat_cost": round(vat_cost_rub / quantity, 2),
                "customs_value_usd": round(customs_value_usd, 2),
                # Комбинированные и весовые пошлины (если применимо)
                "duty_type": category.get('duty_type', 'percent') if category else "percent",
                "duty_ad_valorem_amount": round(duty_result.get("ad_valorem_amount", 0) / quantity, 2) if category and duty_result.get("duty_type") == "combined" else None,
                "duty_ad_valorem_rate": duty_result.get("ad_valorem_rate") if category and duty_result.get("duty_type") == "combined" else None,
                "duty_specific_amount": round(duty_result.get("specific_amount", 0) / quantity, 2) if category and duty_result.get("duty_type") in ["combined", "specific"] else None,
                "duty_specific_rate_eur": duty_result.get("specific_rate_eur") if category and duty_result.get("duty_type") in ["combined", "specific"] else None,
                "duty_specific_rate_rub": duty_result.get("specific_rate_rub") if category and duty_result.get("duty_type") in ["combined", "specific"] else None,
                "duty_chosen_type": duty_result.get("chosen_type") if category and duty_result.get("duty_type") == "combined" else None,
                # Прочие
                "msk_pickup": round(msk_pickup_total_rub / quantity, 2),
                "other_costs": round(other_costs_total_rub / quantity, 2),
                "fixed_costs": round(sea_fixed_cost_rub / quantity, 2)
            }
        }
    
    def find_category_by_name(self, product_name: str) -> Dict:
        """Находит категорию товара по названию с приоритетами и синонимами"""
        product_name_lower = product_name.lower()
        
        # Словарь синонимов для категорий (приоритет: точное совпадение > синонимы > частичное совпадение)
        category_synonyms = self._get_synonym_mapping()
        
        # Поиск с приоритетами
        matches = []
        
        for category in self.categories:
            # Безопасное получение названия категории (поддержка разных структур БД)
            category_name = category.get("category") or category.get("name") or category.get("value")
            if not category_name:
                continue  # Пропускаем категории без названия
            
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
            material = category.get("material", "")
            if material:
                material_lower = material.lower()
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
                material = category.get("material", "")
                material_bonus = 0
                
                if material:
                    material_lower = material.lower()
                    
                    # Бонус для базовых материалов (полиэстер, нейлон, хлопок)
                    base_materials = ["полиэстер", "нейлон", "хлопок", "оксфорд", "плюш", "фетр", "акрил"]
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
        
        # Возвращаем "Новая категория" если товар не распознан
        print(f"⚠️ Товар '{product_name}' не распознан → используем 'Новая категория'")
        
        # Ищем "Новая категория" в загруженных категориях
        print(f"🔍 Ищем 'Новая категория' среди {len(self.categories)} категорий...")
        print(f"🔍 Первые 3 категории: {[cat.get('category', cat.get('name', '???')) for cat in self.categories[:3]]}")
        
        new_category = next((cat for cat in self.categories if cat.get('category') == 'Новая категория'), None)
        
        if new_category:
            print(f"✅ Найдена 'Новая категория' в БД")
            print(f"   Ключи в категории: {list(new_category.keys())}")
            print(f"   Rates: {new_category.get('rates', 'НЕТ ПОЛЯ rates!')}")
            return {
                **new_category,
                "recommendations": self.get_recommendations_defaults()
            }
        
        # Fallback если "Новая категория" не найдена в БД (не должно происходить)
        print("⚠️ ВНИМАНИЕ: 'Новая категория' не найдена в БД, используем дефолт")
        print(f"🔍 DEBUG: Все категории = {[cat.get('category', cat.get('name', '???')) for cat in self.categories[-5:]]}")
        return {
            "category": "Новая категория",
            "material": "",
            "tnved_code": "",
            "density": 200,
            "duty_rate": "0%",
            "vat_rate": "20%",
            "rates": {
                "rail_base": 0,  # Требует ручного ввода
                "air_base": 0    # Требует ручного ввода
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
                      product_url: Optional[str] = None,
                      # Новые параметры для расчета плотности и Prologix
                      packing_units_per_box: Optional[int] = None,
                      packing_box_weight: Optional[float] = None,
                      packing_box_length: Optional[float] = None,
                      packing_box_width: Optional[float] = None,
                      packing_box_height: Optional[float] = None,
                      # Кастомные параметры логистики для конкретных маршрутов
                      custom_logistics_params: Optional[Dict[str, Any]] = None,
                      # Принудительная категория (переопределяет автоопределение)
                      forced_category: Optional[str] = None) -> Dict:
        """
        Рассчитывает себестоимость и цену продажи
        
        Args:
            price_yuan: Цена за единицу в юанях
            weight_kg: Вес товара в кг (за единицу или вычисляется из packing)
            quantity: Количество
            product_name: Название товара для определения категории
            custom_rate: Пользовательская ставка (если None, используется автоматическая)
            delivery_type: Тип доставки - "rail" или "air"
            markup: Наценка (1.5 = 50% наценка)
            product_url: URL товара (опционально)
            packing_units_per_box: Единиц в коробке (для расчета Prologix)
            packing_box_weight: Вес коробки в кг (для расчета плотности)
            packing_box_length: Длина коробки в МЕТРАХ (для расчета плотности)
            packing_box_width: Ширина коробки в МЕТРАХ (для расчета плотности)
            packing_box_height: Высота коробки в МЕТРАХ (для расчета плотности)
            
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
        # Применяем кастомные логистические ставки ДО расчета (если есть)
        custom_rates = {}
        if custom_logistics_params:
            print(f"🔧 Обнаружены кастомные параметры логистики (будут применены ДО расчета): {custom_logistics_params}")
            print(f"   Тип: {type(custom_logistics_params)}")
            print(f"   Ключи: {list(custom_logistics_params.keys()) if isinstance(custom_logistics_params, dict) else 'не словарь!'}")
            
            for route_key, params in custom_logistics_params.items():
                print(f"   🔍 Обработка маршрута: {route_key}")
                print(f"      Параметры: {params}")
                print(f"      Тип параметров: {type(params)}")
                
                # Проверяем что custom_rate существует И не None (0 - валидное значение!)
                if 'custom_rate' in params and params['custom_rate'] is not None:
                    custom_rates[route_key] = params['custom_rate']
                    print(f"   ✅ {route_key}: custom_rate = {params['custom_rate']}")
                else:
                    print(f"   ⚠️ {route_key}: custom_rate отсутствует или None")
        else:
            print(f"⚠️ custom_logistics_params НЕ ПЕРЕДАН или пустой!")
        
        # Определяем категорию: принудительная или автоопределение
        if forced_category:
            # Используем принудительно указанную категорию
            print(f"🎯 Использована принудительная категория: {forced_category}")
            category = next((cat for cat in self.categories if cat.get('category') == forced_category), None)
            if not category:
                print(f"⚠️ Принудительная категория '{forced_category}' не найдена, используем автоопределение")
                category = self.find_category_by_name(product_name)
        else:
            category = self.find_category_by_name(product_name)
        
        # 2.1. Рассчитываем плотность если есть данные упаковки
        density_kg_m3 = None
        volume_m3 = None
        density_surcharge_usd = 0.0
        
        if (packing_box_weight and packing_box_length and 
            packing_box_width and packing_box_height):
            # Объем коробки в м³ (размеры уже в метрах!)
            volume_m3 = packing_box_length * packing_box_width * packing_box_height
            
            # Плотность = вес / объем
            if volume_m3 > 0:
                density_kg_m3 = packing_box_weight / volume_m3
                
                # Получаем надбавку за плотность
                density_surcharge_usd = self.get_density_surcharge(density_kg_m3, delivery_type)
                
                print(f"📦 Плотность товара: {density_kg_m3:.1f} кг/м³ → Надбавка: +${density_surcharge_usd:.2f}/кг")
        
        # 2.2. Определяем базовую логистическую ставку
        if custom_rate is not None:
            base_logistics_rate_usd_per_kg = custom_rate
        else:
            if delivery_type == "air":
                base_logistics_rate_usd_per_kg = category["rates"]["air_base"]
            else:
                base_logistics_rate_usd_per_kg = category["rates"]["rail_base"]
            
            # Проверка: если базовая ставка = 0, значит категория требует ручного ввода
            if base_logistics_rate_usd_per_kg == 0:
                print(f"⚠️ Категория '{category.get('category', '???')}' имеет нулевую базовую ставку ({delivery_type})")
                print(f"   Это нормально для 'Новая категория' - ставка будет применена из custom_logistics")
        
        # 2.3. Применяем надбавку за плотность к базовой ставке
        logistics_rate_usd_per_kg = base_logistics_rate_usd_per_kg + density_surcharge_usd
        
        # 3. Стоимость логистики (итоговая ставка × вес единицы × количество)
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
                
                # Логистика под контракт (фиксированные ставки + надбавка за плотность)
                # Применяем кастомную ставку если указана
                if custom_rates and 'highway_contract' in custom_rates:
                    contract_base_rate_usd = custom_rates['highway_contract']
                    print(f"🔧 Применяем кастомную ставку для Контракта: {custom_rates['highway_contract']}")
                else:
                    contract_base_rate_usd = 3.4 if delivery_type == "rail" else 5.5
                
                # Добавляем надбавку за плотность (если есть)
                contract_density_surcharge_usd = 0.0
                if density_kg_m3 and density_kg_m3 > 0:
                    contract_density_surcharge_usd = self.get_density_surcharge(density_kg_m3, delivery_type)
                    print(f"📊 Контракт: базовая ставка {contract_base_rate_usd}$/кг, надбавка за плотность {contract_density_surcharge_usd}$/кг")
                
                contract_logistics_rate_usd = contract_base_rate_usd + contract_density_surcharge_usd
                contract_logistics_cost_usd = weight_kg * contract_logistics_rate_usd * quantity
                contract_logistics_cost_rub = contract_logistics_cost_usd * self.currencies["usd_to_rub"]
                
                # Фиксированная сумма 25000 рублей
                contract_fixed_cost_rub = 25000.0
                
                # Расчет пошлин и НДС
                # Применяем кастомные пошлины/НДС если указаны
                if custom_logistics_params and 'highway_contract' in custom_logistics_params:
                    custom_duty = custom_logistics_params['highway_contract'].get('duty_rate')
                    custom_vat = custom_logistics_params['highway_contract'].get('vat_rate')
                    
                    if custom_duty is not None:
                        duty_rate = float(custom_duty) / 100
                        print(f"🔧 Применяем кастомную пошлину для Контракта: {custom_duty}%")
                    
                    if custom_vat is not None:
                        vat_rate = float(custom_vat) / 100
                        print(f"🔧 Применяем кастомный НДС для Контракта: {custom_vat}%")
                
                # Таможенная стоимость = товар + локальная доставка + логистика
                customs_value_rub = (goods_with_toni_rub + 
                                   local_delivery_total_yuan * self.currencies["yuan_to_rub"] + 
                                   contract_logistics_cost_rub)
                
                # Используем новый метод расчета комбинированных пошлин
                # ВАЖНО: weight_kg в этом контексте - вес ОДНОЙ единицы, нужно умножить на quantity
                total_weight = weight_kg * quantity
                duty_result = self.calculate_combined_duty(
                    customs_value_rub=customs_value_rub,
                    weight_kg=total_weight,
                    category=category
                )
                
                duty_cost_rub = duty_result["duty_amount"]
                
                # НДС = (таможенная стоимость + пошлины) × vat_rate
                vat_cost_rub = (customs_value_rub + duty_cost_rub) * vat_rate
                
                print(f"💰 Пошлины и НДС для контракта:")
                print(f"   Таможенная стоимость: {customs_value_rub:,.2f} ₽")
                print(f"   Вес товара: {total_weight:,.2f} кг")
                if duty_result["duty_type"] == "combined":
                    print(f"   Пошлины (комбинированные): {duty_cost_rub:,.2f} ₽")
                    print(f"     - Процент ({duty_result['ad_valorem_rate']}%): {duty_result['ad_valorem_amount']:,.2f} ₽")
                    print(f"     - Весовая ({duty_result['specific_rate_eur']} EUR/кг): {duty_result['specific_amount']:,.2f} ₽")
                    print(f"     - Применена: {duty_result['chosen_type']}")
                else:
                    print(f"   Пошлины ({duty_rate*100}%): {duty_cost_rub:,.2f} ₽")
                print(f"   НДС ({vat_rate*100}%): {vat_cost_rub:,.2f} ₽")
                
                # Общая себестоимость под контракт (с пошлинами и НДС!)
                contract_total_cost_rub = (goods_with_toni_rub + 
                                        contract_logistics_cost_rub + 
                                        local_delivery_total_yuan * self.currencies["yuan_to_rub"] + 
                                        duty_cost_rub +  # Добавляем пошлины
                                        vat_cost_rub +   # Добавляем НДС
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
                    "base_rate_usd": contract_base_rate_usd,
                    "density_surcharge_usd": contract_density_surcharge_usd,
                    "fixed_cost_rub": contract_fixed_cost_rub,
                    # Детальная структура затрат для контракта
                    "breakdown": {
                        # Стоимость в Китае (детализация)
                        "base_price_yuan": round(price_yuan, 2),
                        "base_price_rub": round(price_yuan * self.currencies["yuan_to_rub"], 2),
                        "toni_commission_pct": commission_percent,
                        "toni_commission_rub": round((price_yuan * self.currencies["yuan_to_rub"]) * (commission_percent / 100), 2),
                        "factory_price": round(goods_with_toni_rub / quantity, 2),
                        "local_delivery": round((local_delivery_total_yuan * self.currencies["yuan_to_rub"]) / quantity, 2),
                        # Логистика (детализация)
                        "logistics_delivery": round(contract_logistics_cost_rub / quantity, 2),
                        "logistics_rate": contract_logistics_rate_usd,
                        "base_rate": contract_base_rate_usd,
                        "density_surcharge": contract_density_surcharge_usd,
                        "weight_kg": weight_kg,
                        "total_weight_kg": round(weight_kg * quantity, 2),
                        # Пошлины и НДС (реальные суммы + проценты)
                        "duty_type": duty_result.get("duty_type", "percent"),
                        "duty_rate_pct": duty_rate * 100,
                        "duty_cost_rub": round(duty_cost_rub / quantity, 2),
                        "vat_rate_pct": vat_rate * 100,
                        "vat_cost_rub": round(vat_cost_rub / quantity, 2),
                        "customs_value_rub": round(customs_value_rub / quantity, 2),
                        # Комбинированные и весовые пошлины (если применимо)
                        "duty_ad_valorem_amount": round(duty_result.get("ad_valorem_amount", 0) / quantity, 2) if duty_result.get("duty_type") == "combined" else None,
                        "duty_ad_valorem_rate": duty_result.get("ad_valorem_rate") if duty_result.get("duty_type") == "combined" else None,
                        "duty_specific_amount": round(duty_result.get("specific_amount", 0) / quantity, 2) if duty_result.get("duty_type") in ["combined", "specific"] else None,
                        "duty_specific_rate_eur": duty_result.get("specific_rate_eur") if duty_result.get("duty_type") in ["combined", "specific"] else None,
                        "duty_specific_rate_rub": duty_result.get("specific_rate_rub") if duty_result.get("duty_type") in ["combined", "specific"] else None,
                        "duty_chosen_type": duty_result.get("chosen_type") if duty_result.get("duty_type") == "combined" else None,
                        # Прочие
                        "msk_pickup": round(msk_pickup_total_rub / quantity, 2),
                        "other_costs": round(total_other_costs_rub / quantity, 2),
                        "fixed_costs": round(contract_fixed_cost_rub / quantity, 2)
                    }
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
        
        # 11. Расчет стоимости Prologix (если есть данные об объеме)
        prologix_cost_data = None
        
        if volume_m3 and volume_m3 > 0 and packing_units_per_box and packing_units_per_box > 0:
            # Объем ОДНОЙ коробки
            box_volume_m3 = volume_m3
            
            # Количество коробок
            boxes_count = quantity / packing_units_per_box
            
            # Общий объем ВСЕГО груза
            total_volume_m3 = box_volume_m3 * boxes_count
            total_weight = weight_kg * quantity
            
            print(f"📦 Prologix: коробок={boxes_count:.1f}, объем коробки={box_volume_m3:.4f} м³, ОБЩИЙ объем={total_volume_m3:.3f} м³")
            
            prologix_result = self.calculate_prologix_cost(
                volume_m3=total_volume_m3,
                weight_kg=total_weight,
                quantity=quantity,
                base_goods_cost_yuan=base_goods_cost_yuan,
                local_delivery_total_yuan=local_delivery_total_yuan,
                msk_pickup_total_rub=msk_pickup_total_rub,
                other_costs_total_rub=total_other_costs_rub,
                category=category,  # Передаем категорию для расчета пошлин и НДС
                custom_logistics_params=custom_logistics_params  # Передаем кастомные параметры
            )
            
            if prologix_result:
                prologix_cost_data = prologix_result
                print(f"✅ Prologix рассчитан: {prologix_result['cost_per_unit_rub']:.2f} руб за единицу")
            else:
                print(f"❌ calculate_prologix_cost вернул None")
        else:
            print(f"⚠️ Prologix пропущен: volume_m3={volume_m3}, packing_units_per_box={packing_units_per_box} (нужны данные упаковки)")
        
        # 12. Расчет стоимости Море контейнером (если есть данные об объеме и объем >= 10 м³)
        sea_container_cost_data = None
        
        if volume_m3 and volume_m3 > 0 and packing_units_per_box and packing_units_per_box > 0:
            # Объем ОДНОЙ коробки
            box_volume_m3 = volume_m3
            
            # Количество коробок
            boxes_count = quantity / packing_units_per_box
            
            # Общий объем ВСЕГО груза
            total_volume_m3 = box_volume_m3 * boxes_count
            total_weight = weight_kg * quantity
            
            print(f"📦 Море контейнером: коробок={boxes_count:.1f}, объем коробки={box_volume_m3:.4f} м³, ОБЩИЙ объем={total_volume_m3:.3f} м³")
            
            sea_container_result = self.calculate_sea_container_cost(
                volume_m3=total_volume_m3,
                weight_kg=total_weight,
                quantity=quantity,
                base_goods_cost_yuan=base_goods_cost_yuan,
                local_delivery_total_yuan=local_delivery_total_yuan,
                msk_pickup_total_rub=msk_pickup_total_rub,
                other_costs_total_rub=total_other_costs_rub,
                category=category,  # Передаем категорию для расчета пошлин и НДС
                custom_logistics_params=custom_logistics_params  # Передаем кастомные параметры
            )
            
            if sea_container_result:
                sea_container_cost_data = sea_container_result
                print(f"✅ Море контейнером рассчитан: {sea_container_result['cost_per_unit_rub']:.2f} руб за единицу")
            else:
                print(f"❌ calculate_sea_container_cost вернул None (объем < 10 м³)")
        else:
            print(f"⚠️ Море контейнером пропущен: volume_m3={volume_m3}, packing_units_per_box={packing_units_per_box} (нужны данные упаковки)")
        
        # Применяем кастомные ставки для Highway ЖД ПЕРЕД созданием маршрута
        if custom_rates and 'highway_rail' in custom_rates:
            print(f"🔧 Применяем кастомную ставку для Highway ЖД: {logistics_rate_usd_per_kg} → {custom_rates['highway_rail']}")
            base_logistics_rate_usd_per_kg = custom_rates['highway_rail']
            logistics_rate_usd_per_kg = base_logistics_rate_usd_per_kg + density_surcharge_usd
            # Пересчитываем логистику с новой ставкой
            logistics_cost_per_unit_rub = weight_kg * logistics_rate_usd_per_kg * self.currencies["usd_to_rub"]
            logistics_cost_rub = logistics_cost_per_unit_rub * quantity
            # Пересчитываем общую стоимость
            cost_per_unit_rub = (goods_cost_per_unit_rub + logistics_cost_per_unit_rub +
                                local_delivery_per_unit_rub + msk_pickup_per_unit_rub + other_costs_per_unit_rub)
            total_cost_rub = cost_per_unit_rub * quantity
            total_cost_usd = total_cost_rub / self.currencies["usd_to_rub"]
            print(f"   ✅ Новая себестоимость ЖД: {cost_per_unit_rub:.2f} руб/шт")
        
        # 📊 НОВАЯ СТРУКТУРА: Все маршруты в едином формате
        routes = {}
        
        # 1. Highway Company ЖД (с надбавками за плотность)
        routes["highway_rail"] = {
            "name": "Highway ЖД",
            "delivery_days": 25,
            "cost_rub": round(total_cost_rub, 2),
            "cost_usd": round(total_cost_usd, 2),
            "per_unit": round(cost_per_unit_rub, 2),
            "sale_rub": round(total_cost_rub * markup, 2),
            "sale_usd": round(total_cost_usd * markup, 2),
            "sale_per_unit": round(cost_per_unit_rub * markup, 2),
            # Старые поля для совместимости
            "cost_per_unit_rub": round(cost_per_unit_rub, 2),
            "cost_per_unit_usd": round(cost_per_unit_usd, 2),
            "total_cost_rub": round(total_cost_rub, 2),
            "total_cost_usd": round(total_cost_usd, 2),
            "sale_per_unit_rub": round(cost_per_unit_rub * markup, 2),
            "sale_total_rub": round(total_cost_rub * markup, 2),
            "logistics_rate_usd": round(logistics_rate_usd_per_kg, 2),
            "base_rate_usd": round(base_logistics_rate_usd_per_kg, 2),
            "density_surcharge_usd": round(density_surcharge_usd, 2) if density_surcharge_usd else 0,
            "has_density_surcharge": density_surcharge_usd > 0 if density_surcharge_usd else False,
            # Детальная структура затрат
            "breakdown": {
                # Стоимость в Китае (детализация)
                "base_price_yuan": round(price_yuan, 2),
                "base_price_rub": round(price_yuan * self.currencies["yuan_to_rub"], 2),
                "toni_commission_pct": commission_percent,
                "toni_commission_rub": round((price_yuan * self.currencies["yuan_to_rub"]) * (commission_percent / 100), 2),
                "transfer_commission_pct": transfer_percent,
                "transfer_commission_rub": round(goods_cost_per_unit_rub - (price_yuan * self.currencies["yuan_to_rub"]) * (1 + commission_percent / 100), 2),
                "factory_price": round(goods_cost_per_unit_rub, 2),
                "local_delivery": round(local_delivery_per_unit_rub, 2),
                # Логистика (детализация)
                "logistics": round(logistics_cost_per_unit_rub, 2),
                "logistics_rate": round(logistics_rate_usd_per_kg, 2),
                "base_rate": round(base_logistics_rate_usd_per_kg, 2),
                "density_surcharge": round(density_surcharge_usd, 2) if density_surcharge_usd else 0,
                "weight_kg": weight_kg,
                "total_weight_kg": round(weight_kg * quantity, 2),
                # Прочие
                "msk_pickup": round(msk_pickup_per_unit_rub, 2),
                "other_costs": round(other_costs_per_unit_rub, 2)
            }
        }
        
        # 2. Highway Company Авиа (с надбавками за плотность, Авиа = ЖД + 2.1$)
        # Пересчитываем для авиа
        if custom_rates and 'highway_air' in custom_rates:
            # Используем кастомную ставку напрямую
            print(f"🔧 Применяем кастомную ставку для Highway Авиа: {custom_rates['highway_air']}")
            air_base_rate = custom_rates['highway_air']
        else:
            air_base_rate = base_logistics_rate_usd_per_kg + 2.1
        
        air_density_surcharge = self.get_density_surcharge(density_kg_m3, 'air') if density_kg_m3 else 0
        air_total_rate = air_base_rate + air_density_surcharge
        air_logistics_cost_rub = weight_kg * air_total_rate * self.currencies["usd_to_rub"] * quantity
        
        # ВАЖНО: используем те же компоненты себестоимости что и для ЖД (не требует пошлин)
        air_cost_per_unit_rub = (goods_cost_per_unit_rub + 
                                 (air_logistics_cost_rub / quantity) + 
                                 local_delivery_per_unit_rub +
                                 msk_pickup_per_unit_rub + 
                                 other_costs_per_unit_rub)
        air_total_cost_rub = air_cost_per_unit_rub * quantity
        
        routes["highway_air"] = {
            "name": "Highway Авиа",
            "delivery_days": 15,
            "cost_rub": round(air_total_cost_rub, 2),
            "cost_usd": round(air_total_cost_rub / self.currencies["usd_to_rub"], 2),
            "per_unit": round(air_cost_per_unit_rub, 2),
            "sale_rub": round(air_total_cost_rub * markup, 2),
            "sale_usd": round((air_total_cost_rub * markup) / self.currencies["usd_to_rub"], 2),
            "sale_per_unit": round(air_cost_per_unit_rub * markup, 2),
            # Старые поля для совместимости
            "cost_per_unit_rub": round(air_cost_per_unit_rub, 2),
            "cost_per_unit_usd": round(air_cost_per_unit_rub / self.currencies["usd_to_rub"], 2),
            "total_cost_rub": round(air_total_cost_rub, 2),
            "total_cost_usd": round(air_total_cost_rub / self.currencies["usd_to_rub"], 2),
            "sale_per_unit_rub": round(air_cost_per_unit_rub * markup, 2),
            "sale_total_rub": round(air_total_cost_rub * markup, 2),
            "logistics_rate_usd": round(air_total_rate, 2),
            "base_rate_usd": round(air_base_rate, 2),
            "density_surcharge_usd": round(air_density_surcharge, 2) if air_density_surcharge else 0,
            "has_density_surcharge": air_density_surcharge > 0 if air_density_surcharge else False,
            # Детальная структура затрат
            "breakdown": {
                # Стоимость в Китае (детализация)
                "base_price_yuan": round(price_yuan, 2),
                "base_price_rub": round(price_yuan * self.currencies["yuan_to_rub"], 2),
                "toni_commission_pct": commission_percent,
                "toni_commission_rub": round((price_yuan * self.currencies["yuan_to_rub"]) * (commission_percent / 100), 2),
                "transfer_commission_pct": transfer_percent,
                "transfer_commission_rub": round(goods_cost_per_unit_rub - (price_yuan * self.currencies["yuan_to_rub"]) * (1 + commission_percent / 100), 2),
                "factory_price": round(goods_cost_per_unit_rub, 2),
                "local_delivery": round(local_delivery_per_unit_rub, 2),
                # Логистика (детализация)
                "logistics": round(air_logistics_cost_rub / quantity, 2),
                "logistics_rate": round(air_total_rate, 2),
                "base_rate": round(air_base_rate, 2),
                "density_surcharge": round(air_density_surcharge, 2) if air_density_surcharge else 0,
                "weight_kg": weight_kg,
                "total_weight_kg": round(weight_kg * quantity, 2),
                # Прочие
                "msk_pickup": round(msk_pickup_per_unit_rub, 2),
                "other_costs": round(other_costs_per_unit_rub, 2)
            }
        }
        
        # 3. Highway под контракт
        if contract_cost_data:
            contract_cost_unit = contract_cost_data["per_unit"]["rub"]
            contract_cost_total = contract_cost_data["total"]["rub"]
            routes["highway_contract"] = {
                "name": "Highway под контракт",
                "delivery_days": 25,
                "cost_rub": contract_cost_total,
                "cost_usd": contract_cost_data["total"]["usd"],
                "per_unit": contract_cost_unit,
                "sale_rub": round(contract_cost_total * markup, 2),
                "sale_usd": round(contract_cost_data["total"]["usd"] * markup, 2),
                "sale_per_unit": round(contract_cost_unit * markup, 2),
                # Старые поля для совместимости
                "cost_per_unit_rub": contract_cost_unit,
                "cost_per_unit_usd": contract_cost_data["per_unit"]["usd"],
                "total_cost_rub": contract_cost_total,
                "total_cost_usd": contract_cost_data["total"]["usd"],
                "sale_per_unit_rub": round(contract_cost_unit * markup, 2),
                "sale_total_rub": round(contract_cost_total * markup, 2),
                "logistics_rate_usd": contract_cost_data["logistics_rate_usd"],
                "base_rate_usd": contract_cost_data["base_rate_usd"],
                "density_surcharge_usd": contract_cost_data["density_surcharge_usd"],
                "fixed_cost_rub": contract_cost_data["fixed_cost_rub"],
                "has_density_surcharge": contract_cost_data["density_surcharge_usd"] > 0,
                # Детальная структура затрат
                "breakdown": contract_cost_data["breakdown"]
            }
        
        # 4. Prologix (если доступен)
        if prologix_cost_data:
            prologix_cost_unit = prologix_cost_data["cost_per_unit_rub"]
            prologix_cost_total = prologix_cost_data["total_cost_rub"]
            routes["prologix"] = {
                "name": "Prologix",
                "delivery_days": prologix_cost_data.get("delivery_days_avg", 30),
                "cost_rub": prologix_cost_total,
                "cost_usd": prologix_cost_data["total_cost_usd"],
                "per_unit": prologix_cost_unit,
                "sale_rub": round(prologix_cost_total * markup, 2),
                "sale_usd": round(prologix_cost_data["total_cost_usd"] * markup, 2),
                "sale_per_unit": round(prologix_cost_unit * markup, 2),
                # Старые поля для совместимости
                "cost_per_unit_rub": prologix_cost_unit,
                "cost_per_unit_usd": prologix_cost_data["cost_per_unit_usd"],
                "total_cost_rub": prologix_cost_total,
                "total_cost_usd": prologix_cost_data["total_cost_usd"],
                "sale_per_unit_rub": round(prologix_cost_unit * markup, 2),
                "sale_total_rub": round(prologix_cost_total * markup, 2),
                "rate_rub_per_m3": prologix_cost_data["rate_rub_per_m3"],
                "total_volume_m3": prologix_cost_data["total_volume_m3"],
                "logistics_cost_rub": prologix_cost_data["logistics_cost_rub"],
                "fixed_cost_rub": prologix_cost_data["fixed_cost_rub"],
                # Детальная структура затрат
                "breakdown": prologix_cost_data["breakdown"]
            }
        
        # 5. Море контейнером (если доступен)
        if sea_container_cost_data:
            sea_cost_unit = sea_container_cost_data["cost_per_unit_rub"]
            sea_cost_total = sea_container_cost_data["total_cost_rub"]
            routes["sea_container"] = {
                "name": "Море контейнером",
                "delivery_days": sea_container_cost_data.get("delivery_days", 60),
                "cost_rub": sea_cost_total,
                "cost_usd": sea_container_cost_data["total_cost_usd"],
                "per_unit": sea_cost_unit,
                "sale_rub": round(sea_cost_total * markup, 2),
                "sale_usd": round(sea_container_cost_data["total_cost_usd"] * markup, 2),
                "sale_per_unit": round(sea_cost_unit * markup, 2),
                # Старые поля для совместимости
                "cost_per_unit_rub": sea_cost_unit,
                "cost_per_unit_usd": sea_container_cost_data["cost_per_unit_usd"],
                "total_cost_rub": sea_cost_total,
                "total_cost_usd": sea_container_cost_data["total_cost_usd"],
                "sale_per_unit_rub": round(sea_cost_unit * markup, 2),
                "sale_total_rub": round(sea_cost_total * markup, 2),
                # Специфичные поля для морских контейнеров
                "containers_40ft": sea_container_cost_data["containers_40ft"],
                "containers_20ft": sea_container_cost_data["containers_20ft"],
                "total_capacity_m3": sea_container_cost_data["total_capacity_m3"],
                "remaining_capacity_m3": sea_container_cost_data["remaining_capacity_m3"],
                "total_volume_m3": sea_container_cost_data["total_volume_m3"],
                "containers_cost_usd": sea_container_cost_data["containers_cost_usd"],
                "containers_cost_rub": sea_container_cost_data["containers_cost_rub"],
                "containers_fixed_cost_rub": sea_container_cost_data["containers_fixed_cost_rub"],
                "duty_on_containers_usd": sea_container_cost_data["duty_on_containers_usd"],
                "fixed_cost_rub": sea_container_cost_data["fixed_cost_rub"],
                # Детальная структура затрат
                "breakdown": sea_container_cost_data["breakdown"]
            }
        
        return {
            "product_name": product_name,
            "category": category["category"],
            "quantity": quantity,
            # ✨ НОВОЕ: Все маршруты в едином формате
            "routes": routes,
            "unit_price_yuan": price_yuan,
            "total_price": {
                "yuan": round(price_yuan * quantity, 2),
                "usd": round(total_goods_cost_usd, 2),
                "rub": round(total_goods_cost_rub, 2)
            },
            "logistics": {
                "rate_usd": logistics_rate_usd_per_kg,
                "base_rate_usd": base_logistics_rate_usd_per_kg,
                "density_surcharge_usd": density_surcharge_usd,
                "cost_usd": round(total_logistics_cost_usd, 2),
                "cost_rub": round(total_logistics_cost_rub, 2),
                "delivery_type": delivery_type
            },
            "density_info": {
                "density_kg_m3": round(density_kg_m3, 1) if density_kg_m3 else None,
                "volume_m3": round(volume_m3, 4) if volume_m3 else None,
                "has_density_data": density_kg_m3 is not None
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
            "prologix_cost": prologix_cost_data,
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
        
        # Кастомные параметры логистики уже применены ДО создания маршрутов
        # (см. строки 888-900 для highway_rail и 952-957 для highway_air)
        
        # ВАЖНО: После применения кастомных ставок нужно пересчитать корневые cost_price/sale_price
        # на основе САМОГО ДЕШЁВОГО маршрута (а не Highway ЖД который был по умолчанию)
        cheapest_route_key = None
        cheapest_cost = float('inf')
        
        for route_key, route_data in result.get('routes', {}).items():
            route_cost = route_data.get('cost_rub', float('inf'))
            if route_cost < cheapest_cost:
                cheapest_cost = route_cost
                cheapest_route_key = route_key
        
        if cheapest_route_key:
            cheapest_route = result['routes'][cheapest_route_key]
            print(f"🏆 Самый дешёвый маршрут после пересчёта: {cheapest_route['name']} = {cheapest_route['cost_rub']:.2f}₽")
            
            # Обновляем корневые поля на основе самого дешёвого маршрута
            result['cost_price'] = {
                "total": {
                    "usd": cheapest_route['cost_usd'],
                    "rub": cheapest_route['cost_rub']
                },
                "per_unit": {
                    "usd": round(cheapest_route['cost_usd'] / quantity, 2),
                    "rub": cheapest_route['per_unit']
                }
            }
            result['sale_price'] = {
                "total": {
                    "usd": cheapest_route['sale_usd'],
                    "rub": cheapest_route['sale_rub']
                },
                "per_unit": {
                    "usd": round(cheapest_route['sale_usd'] / quantity, 2),
                    "rub": cheapest_route['sale_per_unit']
                }
            }
            # Пересчитываем прибыль
            result['profit'] = {
                "total": {
                    "usd": round(cheapest_route['sale_usd'] - cheapest_route['cost_usd'], 2),
                    "rub": round(cheapest_route['sale_rub'] - cheapest_route['cost_rub'], 2)
                },
                "per_unit": {
                    "usd": round((cheapest_route['sale_usd'] - cheapest_route['cost_usd']) / quantity, 2),
                    "rub": round(cheapest_route['sale_per_unit'] - cheapest_route['per_unit'], 2)
                }
            }
        
        return result

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
