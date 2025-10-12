"""
Base Calculation Strategy
Defines interface for all calculation strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from models.category import Category


class CalculationStrategy(ABC):
    """
    Базовая стратегия расчёта.
    
    Определяет интерфейс для всех стратегий расчёта.
    Разные стратегии используются для разных типов категорий.
    """
    
    @abstractmethod
    def requires_user_input(self, category: Category) -> bool:
        """
        Определяет требуется ли ввод от пользователя для этой категории.
        
        Args:
            category: Категория товара
            
        Returns:
            bool: True если требуется ввод пользователя
        """
        pass
    
    @abstractmethod
    def get_required_params(self, category: Category) -> List[str]:
        """
        Возвращает список требуемых параметров для категории.
        
        Args:
            category: Категория товара
            
        Returns:
            List[str]: Список названий требуемых параметров
        """
        pass
    
    @abstractmethod
    def validate_params(self, category: Category, params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Валидирует предоставленные параметры.
        
        Args:
            category: Категория товара
            params: Предоставленные параметры
            
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        pass
    
    @abstractmethod
    def prepare_calculation_params(
        self, 
        category: Category,
        base_params: Dict[str, Any],
        custom_logistics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Подготавливает параметры для расчёта.
        
        Args:
            category: Категория товара
            base_params: Базовые параметры (quantity, weight, price и т.д.)
            custom_logistics: Кастомные логистические параметры
            
        Returns:
            Dict: Параметры готовые для передачи в calculator.calculate_cost()
        """
        pass
    
    def get_strategy_name(self) -> str:
        """
        Возвращает название стратегии.
        
        Returns:
            str: Название стратегии
        """
        return self.__class__.__name__
    
    def __str__(self):
        return f"<{self.get_strategy_name()}>"
    
    def __repr__(self):
        return self.__str__()





