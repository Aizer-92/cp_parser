"""
Модуль для работы с данными по таможенным пошлинам
"""

import json
import os
from typing import Dict, List, Optional, Any

class CustomsDataLoader:
    """Загрузчик данных по таможенным пошлинам"""
    
    def __init__(self, data_file: str = "categories_with_duties.json"):
        self.data_file = data_file
        self._customs_data = None
        self._categories_with_customs = None
    
    def load_customs_data(self) -> Dict[str, Any]:
        """Загружает данные по пошлинам из JSON файла"""
        if self._customs_data is None:
            try:
                if os.path.exists(self.data_file):
                    with open(self.data_file, 'r', encoding='utf-8') as f:
                        self._customs_data = json.load(f)
                else:
                    print(f"Файл {self.data_file} не найден")
                    self._customs_data = {"categories": []}
            except Exception as e:
                print(f"Ошибка загрузки данных по пошлинам: {e}")
                self._customs_data = {"categories": []}
        
        return self._customs_data
    
    def get_categories_with_customs(self) -> List[Dict[str, Any]]:
        """Возвращает категории с данными по пошлинам"""
        if self._categories_with_customs is None:
            data = self.load_customs_data()
            self._categories_with_customs = data.get("categories", [])
        
        return self._categories_with_customs
    
    def get_customs_info_by_tnved(self, tnved_code: str) -> Optional[Dict[str, Any]]:
        """Получает информацию по пошлинам для конкретного кода ТН ВЭД"""
        categories = self.get_categories_with_customs()
        
        for category in categories:
            if category.get("tnved_code") == tnved_code and "customs_info" in category:
                return category["customs_info"]
        
        return None
    
    def get_customs_info_by_category(self, category_name: str, material: str = None) -> Optional[Dict[str, Any]]:
        """Получает информацию по пошлинам для категории товара"""
        categories = self.get_categories_with_customs()
        
        for category in categories:
            if category.get("category", "").lower() == category_name.lower():
                # Если материал указан, ищем точное совпадение
                if material:
                    if category.get("material", "").lower().find(material.lower()) != -1:
                        if "customs_info" in category:
                            return {
                                **category["customs_info"],
                                "tnved_code": category.get("tnved_code"),
                                "category": category.get("category"),
                                "material": category.get("material")
                            }
                else:
                    # Берем первое совпадение по категории
                    if "customs_info" in category:
                        return {
                            **category["customs_info"],
                            "tnved_code": category.get("tnved_code"),
                            "category": category.get("category"),
                            "material": category.get("material")
                        }
        
        return None
    
    def calculate_customs_cost(self, customs_value_usd: float, customs_info: Dict[str, Any]) -> Dict[str, float]:
        """Рассчитывает таможенные расходы"""
        import re
        
        result = {
            "customs_value_usd": customs_value_usd,
            "duty_amount_usd": 0.0,
            "vat_amount_usd": 0.0,
            "total_customs_cost_usd": 0.0,
            "duty_rate_numeric": 0.0,
            "vat_rate_numeric": 0.0
        }
        
        # Извлекаем числовое значение пошлины
        duty_rate = customs_info.get("duty_rate", "0%")
        duty_match = re.search(r'(\d+(?:\.\d+)?)', duty_rate)
        if duty_match:
            result["duty_rate_numeric"] = float(duty_match.group(1))
            if customs_info.get("duty_type") == "ad_valorem":
                result["duty_amount_usd"] = customs_value_usd * (result["duty_rate_numeric"] / 100)
        
        # Извлекаем числовое значение НДС
        vat_rate = customs_info.get("vat_rate", "20%")
        vat_match = re.search(r'(\d+(?:\.\d+)?)', vat_rate)
        if vat_match:
            result["vat_rate_numeric"] = float(vat_match.group(1))
            # НДС рассчитывается с суммы (таможенная стоимость + пошлина)
            vat_base = customs_value_usd + result["duty_amount_usd"]
            result["vat_amount_usd"] = vat_base * (result["vat_rate_numeric"] / 100)
        
        result["total_customs_cost_usd"] = result["duty_amount_usd"] + result["vat_amount_usd"]
        
        return result

# Глобальный экземпляр загрузчика
customs_loader = CustomsDataLoader()

