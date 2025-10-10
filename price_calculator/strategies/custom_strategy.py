"""
Custom Category Strategy
For categories requiring user input (e.g., "Новая категория")
"""

from typing import Dict, Any, List, Optional
from models.category import Category
from .calculation_strategy import CalculationStrategy


class CustomCategoryStrategy(CalculationStrategy):
    """
    Стратегия для кастомных категорий.
    
    Используется когда:
    - У категории нет базовых ставок (rail_base=0, air_base=0)
    - Требуется ввод параметров от пользователя
    - Это "Новая категория" или похожая
    """
    
    def requires_user_input(self, category: Category) -> bool:
        """
        Кастомные категории требуют ввода от пользователя.
        
        Args:
            category: Категория товара
            
        Returns:
            bool: True если категория требует параметров
        """
        return category.needs_custom_params()
    
    def get_required_params(self, category: Category) -> List[str]:
        """
        Возвращает список требуемых параметров.
        
        Args:
            category: Категория товара
            
        Returns:
            List[str]: Список названий параметров
        """
        return category.get_required_params_names()
    
    def validate_params(self, category: Category, params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Валидирует кастомные параметры.
        
        Args:
            category: Категория товара
            params: Кастомные параметры (custom_logistics)
            
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        # Используем встроенную валидацию категории
        is_valid, errors = category.validate_params(params)
        
        # Дополнительная валидация для custom_logistics
        if not params:
            return False, ["Не предоставлены кастомные параметры"]
        
        # Проверяем что есть хотя бы один маршрут с параметрами
        has_route_params = False
        for route_key, route_params in params.items():
            if isinstance(route_params, dict) and route_params:
                has_route_params = True
                
                # Проверяем custom_rate для Highway маршрутов
                if route_key in ['highway_rail', 'highway_air', 'highway_contract']:
                    custom_rate = route_params.get('custom_rate')
                    if custom_rate is not None and custom_rate > 0:
                        has_route_params = True
                        break
                
                # Проверяем для Prologix
                if route_key == 'prologix':
                    custom_rate = route_params.get('custom_rate')
                    if custom_rate is not None and custom_rate > 0:
                        has_route_params = True
                        break
        
        if not has_route_params:
            errors.append("Необходимо указать параметры хотя бы для одного маршрута")
            is_valid = False
        
        return is_valid, errors
    
    def prepare_calculation_params(
        self,
        category: Category,
        base_params: Dict[str, Any],
        custom_logistics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Подготавливает параметры для расчёта кастомной категории.
        
        Использует custom_logistics вместо базовых ставок.
        
        Args:
            category: Категория товара
            base_params: Базовые параметры (quantity, weight, price, markup)
            custom_logistics: Кастомные логистические параметры (обязательно!)
            
        Returns:
            Dict: Параметры для calculator.calculate_cost()
            
        Raises:
            ValueError: Если custom_logistics не предоставлены
        """
        if not custom_logistics:
            raise ValueError(
                f"Кастомные параметры обязательны для категории '{category.name}'"
            )
        
        # Валидируем параметры
        is_valid, errors = self.validate_params(category, custom_logistics)
        if not is_valid:
            raise ValueError(f"Невалидные параметры: {', '.join(errors)}")
        
        # Копируем базовые параметры
        calc_params = base_params.copy()
        
        # Добавляем категорию
        calc_params['forced_category'] = category.name
        
        # Добавляем кастомные логистические параметры
        calc_params['custom_logistics_params'] = custom_logistics
        
        return calc_params
    
    def get_strategy_name(self) -> str:
        return "CustomCategory"

