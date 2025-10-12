"""
Recalculation Service - сервис пересчёта маршрутов для расчёта

Этот сервис отвечает за:
1. Интеграцию со старой логикой расчёта (price_calculator.py)
2. Создание/обновление LogisticsRoute на основе результатов
3. Пересчёт всех маршрутов при изменении параметров расчёта
"""
from typing import Dict, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from models_v3 import Calculation, LogisticsRoute, Position
from .logistics_service import LogisticsService
from .calculation_service import CalculationService

# Import старой логики расчёта
from services.calculation_orchestrator import CalculationOrchestrator
from price_calculator import PriceCalculator


class RecalculationService:
    """
    Сервис для пересчёта маршрутов логистики
    
    Связывает старую логику расчёта с новой архитектурой БД
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logistics_service = LogisticsService(db)
        self.calculation_service = CalculationService(db)
        
        # Загружаем категории и создаем оркестратор
        calculator = PriceCalculator()
        self.orchestrator = CalculationOrchestrator(calculator.categories)
    
    def recalculate_routes(
        self, 
        calculation_id: int,
        category: Optional[str] = None,
        custom_logistics: Optional[Dict] = None
    ) -> List[LogisticsRoute]:
        """
        Пересчитать все маршруты для расчёта
        
        Args:
            calculation_id: ID расчёта
            category: Категория товара (если None, берется из Position)
            custom_logistics: Кастомные ставки логистики
            
        Returns:
            Список созданных/обновленных маршрутов
            
        Raises:
            ValueError: Если расчёт не найден или отсутствуют необходимые данные
        """
        # Загружаем расчёт с позицией
        calculation = self.calculation_service.get_with_full_details(calculation_id)
        if not calculation:
            raise ValueError(f"Calculation {calculation_id} not found")
        
        if not calculation.position:
            raise ValueError(f"Position not found for calculation {calculation_id}")
        
        # Определяем категорию
        category = category or calculation.position.category
        if not category:
            raise ValueError("Category is required for calculation")
        
        # Проверяем вес для quick расчета
        if calculation.calculation_type == 'quick':
            if not calculation.weight_kg:
                raise ValueError("Weight is required for quick calculation")
            weight_kg = float(calculation.weight_kg)
        else:
            # Для precise расчета нужна упаковка
            if not calculation.packing_units_per_box:
                raise ValueError("Packing data is required for precise calculation")
            # Вес будет рассчитан автоматически
            weight_kg = float(calculation.packing_box_weight) / calculation.packing_units_per_box if calculation.packing_box_weight else 0.2
        
        # Шаг 1: Инициализируем расчёт через оркестратор
        start_result = self.orchestrator.start_calculation(
            product_name=calculation.position.name,
            quantity=calculation.quantity,
            weight_kg=weight_kg,
            unit_price_yuan=float(calculation.price_yuan),
            markup=1.7,  # Default markup, можно сделать настраиваемым
            forced_category=category,
            product_url=calculation.factory_custom_url or None
        )
        
        # Шаг 2: Если нужны кастомные параметры, предоставляем их
        if start_result.get('needs_user_input'):
            if not custom_logistics:
                raise ValueError(f"Category '{category}' requires custom logistics parameters")
            
            self.orchestrator.provide_custom_params(custom_logistics)
        
        # Шаг 3: Выполняем расчёт
        try:
            calc_response = self.orchestrator.calculate()
            
            if not calc_response.get('success'):
                raise ValueError(calc_response.get('error', 'Unknown error'))
            
            result = calc_response['result']
        except Exception as e:
            raise ValueError(f"Calculation failed: {str(e)}")
        
        # Сохраняем/обновляем маршруты
        routes = []
        for route_data in result.get('routes', []):
            route_name = self._normalize_route_name(route_data.get('route_name', route_data.get('name', '')))
            
            logistics_data = {
                'custom_rate': self._get_decimal(route_data.get('logistics_rate')),
                'duty_rate': self._get_decimal(route_data.get('duty_rate')),
                'vat_rate': self._get_decimal(route_data.get('vat_rate')),
                'specific_rate': self._get_decimal(route_data.get('specific_rate')),
                'cost_price_rub': self._get_decimal(route_data.get('cost_per_unit_rub')),
                'cost_price_usd': self._get_decimal(route_data.get('cost_per_unit_usd')),
                'sale_price_rub': self._get_decimal(route_data.get('sale_per_unit_rub')),
                'sale_price_usd': self._get_decimal(route_data.get('sale_per_unit_usd')),
                'profit_rub': self._get_decimal(route_data.get('profit_per_unit_rub')),
                'profit_usd': self._get_decimal(route_data.get('profit_per_unit_usd')),
                'total_cost_rub': self._get_decimal(route_data.get('total_cost_rub')),
                'total_cost_usd': self._get_decimal(route_data.get('total_cost_usd')),
                'total_sale_rub': self._get_decimal(route_data.get('total_sale_rub')),
                'total_sale_usd': self._get_decimal(route_data.get('total_sale_usd')),
                'total_profit_rub': self._get_decimal(route_data.get('total_profit_rub')),
                'total_profit_usd': self._get_decimal(route_data.get('total_profit_usd')),
            }
            
            route = self.logistics_service.update_route(
                calculation_id=calculation_id,
                route_name=route_name,
                route_data=logistics_data
            )
            routes.append(route)
        
        return routes
    
    def _normalize_route_name(self, name: str) -> str:
        """
        Нормализовать название маршрута к стандартному виду
        
        Highway ЖД → highway_rail
        Highway Авиа → highway_air
        etc.
        """
        name_lower = name.lower()
        
        if 'жд' in name_lower or 'rail' in name_lower:
            return 'highway_rail'
        elif 'авиа' in name_lower or 'air' in name_lower:
            return 'highway_air'
        elif 'контракт' in name_lower or 'contract' in name_lower:
            return 'highway_contract'
        elif 'prologix' in name_lower:
            return 'prologix'
        elif 'sea' in name_lower or 'море' in name_lower or 'container' in name_lower:
            return 'sea_container'
        else:
            # Fallback: убираем пробелы и приводим к lowercase
            return name.replace(' ', '_').lower()
    
    def _get_decimal(self, value) -> Optional[Decimal]:
        """Безопасное преобразование в Decimal"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None

