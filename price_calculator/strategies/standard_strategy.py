"""
Standard Category Strategy
For categories with predefined rates and parameters
"""

from typing import Dict, Any, List, Optional
from models.category import Category
from .calculation_strategy import CalculationStrategy


class StandardCategoryStrategy(CalculationStrategy):
    """
    Стратегия для стандартных категорий.
    
    Используется когда:
    - У категории есть базовые ставки (rail_base, air_base)
    - Все параметры известны заранее
    - Не требуется ввод от пользователя
    """
    
    def requires_user_input(self, category: Category) -> bool:
        """
        Стандартные категории не требуют ввода пользователя.
        
        Args:
            category: Категория товара
            
        Returns:
            bool: False - параметры не требуются
        """
        return False
    
    def get_required_params(self, category: Category) -> List[str]:
        """
        Стандартные категории не требуют дополнительных параметров.
        
        Args:
            category: Категория товара
            
        Returns:
            List[str]: Пустой список
        """
        return []
    
    def validate_params(self, category: Category, params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Для стандартных категорий валидация всегда успешна.
        
        Args:
            category: Категория товара
            params: Параметры (не используются)
            
        Returns:
            tuple[bool, List[str]]: (True, [])
        """
        return True, []
    
    def prepare_calculation_params(
        self,
        category: Category,
        base_params: Dict[str, Any],
        custom_logistics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Подготавливает параметры для расчёта стандартной категории.
        
        Использует базовые ставки из категории.
        custom_logistics игнорируется для стандартных категорий.
        
        Args:
            category: Категория товара
            base_params: Базовые параметры (quantity, weight, price, markup)
            custom_logistics: Кастомные параметры (игнорируются)
            
        Returns:
            Dict: Параметры для calculator.calculate_cost()
        """
        # Копируем базовые параметры
        calc_params = base_params.copy()
        
        # Добавляем категорию
        calc_params['forced_category'] = category.name
        
        # Для стандартных категорий custom_logistics не используется
        # Расчёт будет использовать базовые ставки из категории
        
        return calc_params
    
    def get_strategy_name(self) -> str:
        return "StandardCategory"



