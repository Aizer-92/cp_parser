"""
Сервисный слой для управления расчётами

Отвечает за:
- Выполнение расчётов через PriceCalculator
- Сохранение/обновление расчётов в БД
- Загрузку расчётов из БД
- Бизнес-логику управления расчётами
"""

from typing import Optional, Dict, Any
from datetime import datetime

from price_calculator import PriceCalculator
from database import save_calculation_to_db, update_calculation, get_calculation_history


class CalculationService:
    """Сервис для управления расчётами цен"""
    
    def __init__(self):
        self.calculator = PriceCalculator()
    
    def perform_calculation(
        self,
        product_name: str,
        price_yuan: float,
        quantity: int,
        markup: float = 1.7,
        weight_kg: Optional[float] = None,
        custom_rate: Optional[float] = None,
        delivery_type: str = "rail",
        product_url: str = "",
        # Данные пакинга
        packing_units_per_box: Optional[int] = None,
        packing_box_weight: Optional[float] = None,
        packing_box_length: Optional[float] = None,
        packing_box_width: Optional[float] = None,
        packing_box_height: Optional[float] = None,
        # Кастомные параметры логистики
        custom_logistics: Optional[Dict[str, Any]] = None,
        forced_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Выполняет расчёт цены товара
        
        Args:
            product_name: Название товара
            price_yuan: Цена в юанях
            quantity: Количество
            markup: Наценка (default: 1.7)
            ... (остальные параметры)
        
        Returns:
            Результат расчёта (dict)
        """
        return self.calculator.calculate_cost(
            product_name=product_name,
            price_yuan=price_yuan,
            weight_kg=weight_kg,
            quantity=quantity,
            custom_rate=custom_rate,
            delivery_type=delivery_type,
            markup=markup,
            product_url=product_url,
            packing_units_per_box=packing_units_per_box,
            packing_box_weight=packing_box_weight,
            packing_box_length=packing_box_length,
            packing_box_width=packing_box_width,
            packing_box_height=packing_box_height,
            custom_logistics_params=custom_logistics,
            forced_category=forced_category
        )
    
    def create_calculation(
        self,
        calculation_result: Dict[str, Any],
        custom_logistics: Optional[Dict[str, Any]] = None,
        forced_category: Optional[str] = None
    ) -> int:
        """
        Создаёт новый расчёт в БД
        
        Args:
            calculation_result: Результат расчёта от calculator.calculate_cost()
            custom_logistics: Кастомные параметры логистики
            forced_category: Принудительная категория
        
        Returns:
            ID созданного расчёта
        """
        db_data = self._prepare_db_data(
            calculation_result,
            custom_logistics=custom_logistics,
            forced_category=forced_category
        )
        
        return save_calculation_to_db(db_data)
    
    def update_calculation(
        self,
        calculation_id: int,
        calculation_result: Dict[str, Any],
        custom_logistics: Optional[Dict[str, Any]] = None,
        forced_category: Optional[str] = None
    ) -> bool:
        """
        Обновляет существующий расчёт в БД
        
        Args:
            calculation_id: ID расчёта
            calculation_result: Результат расчёта от calculator.calculate_cost()
            custom_logistics: Кастомные параметры логистики
            forced_category: Принудительная категория
        
        Returns:
            True если успешно
        """
        try:
            print(f"🔄 CalculationService.update_calculation: ID={calculation_id}")
            print(f"   calculation_result keys: {list(calculation_result.keys())}")
            print(f"   custom_logistics: {custom_logistics is not None}")
            print(f"   forced_category: {forced_category}")
            
            db_data = self._prepare_db_data(
                calculation_result,
                custom_logistics=custom_logistics,
                forced_category=forced_category
            )
            
            print(f"✅ db_data подготовлены успешно: {len(db_data)} полей")
            
            update_calculation(calculation_id, db_data)
            print(f"✅ update_calculation завершён успешно")
            return True
        except Exception as e:
            print(f"❌ Ошибка в CalculationService.update_calculation: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _prepare_db_data(
        self,
        result: Dict[str, Any],
        custom_logistics: Optional[Dict[str, Any]] = None,
        forced_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Подготавливает данные для сохранения в БД
        
        Args:
            result: Результат расчёта от calculator.calculate_cost()
            custom_logistics: Кастомные параметры логистики
            forced_category: Принудительная категория
        
        Returns:
            Данные в формате для save_calculation_to_db/update_calculation
        """
        try:
            # Безопасное извлечение данных с fallback
            # ВАЖНО: используем `or {}` чтобы обработать None
            packing_data = result.get('packing') or {}
            customs_info = result.get('customs_info') or {}
            customs_calc = result.get('customs_calculations') or {}
            density_warning = result.get('density_warning') or {}
            
            return {
                'product_name': result.get('product_name', ''),
                'category': result.get('category', 'Не определена'),
                'price_yuan': result.get('unit_price_yuan', 0),
                'weight_kg': result.get('weight_kg', 0),
                'quantity': result.get('quantity', 0),
                'markup': result.get('markup', 1.7),
                'custom_rate': result.get('logistics', {}).get('rate_usd') if result.get('logistics') else None,
                'product_url': result.get('product_url', ''),
                # ВАЖНО: database.py ожидает ключи БЕЗ _total!
                'cost_price_rub': result.get('cost_price', {}).get('total', {}).get('rub', 0),
                'cost_price_usd': result.get('cost_price', {}).get('total', {}).get('usd', 0),
                'sale_price_rub': result.get('sale_price', {}).get('total', {}).get('rub', 0),
                'sale_price_usd': result.get('sale_price', {}).get('total', {}).get('usd', 0),
                'profit_rub': result.get('profit', {}).get('total', {}).get('rub', 0),
                'profit_usd': result.get('profit', {}).get('total', {}).get('usd', 0),
                'calculation_type': result.get('calculation_type', 'quick'),
                # Данные пакинга (с безопасным извлечением)
                'packing_units_per_box': packing_data.get('units_per_box'),
                'packing_box_weight': packing_data.get('box_weight_kg'),
                'packing_box_length': packing_data.get('box_length_cm'),
                'packing_box_width': packing_data.get('box_width_cm'),
                'packing_box_height': packing_data.get('box_height_cm'),
                'packing_total_boxes': packing_data.get('total_boxes'),
                'packing_total_volume': packing_data.get('total_volume_m3'),
                'packing_total_weight': packing_data.get('total_weight_kg'),
                # Данные о пошлинах
                'tnved_code': customs_info.get('tnved_code'),
                'duty_rate': customs_info.get('duty_rate'),
                'vat_rate': customs_info.get('vat_rate'),
                'duty_amount_usd': customs_calc.get('duty_amount_usd'),
                'vat_amount_usd': customs_calc.get('vat_amount_usd'),
                'total_customs_cost_usd': customs_calc.get('total_customs_cost_usd'),
                'certificates': ', '.join(customs_info.get('certificates', [])) if customs_info.get('certificates') else None,
                'customs_notes': customs_info.get('required_documents'),
                # Данные о плотности
                'density_warning_message': density_warning.get('message'),
                'calculated_density': density_warning.get('calculated_density'),
                'category_density': density_warning.get('category_density'),
                # Кастомные параметры логистики и принудительная категория
                'custom_logistics': custom_logistics,
                'forced_category': forced_category
            }
        except Exception as e:
            print(f"❌ Ошибка в _prepare_db_data: {e}")
            print(f"   result keys: {list(result.keys()) if result else 'None'}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_calculation_history(self, limit: int = 50) -> list:
        """
        Получает историю расчётов из БД
        
        Args:
            limit: Максимальное количество записей
        
        Returns:
            Список расчётов
        """
        return get_calculation_history()


# Singleton instance
_calculation_service = None

def get_calculation_service() -> CalculationService:
    """Возвращает singleton instance CalculationService"""
    global _calculation_service
    if _calculation_service is None:
        _calculation_service = CalculationService()
    return _calculation_service

