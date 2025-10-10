"""
Calculation Context
Manages calculation state, strategy selection, and parameters
"""

from typing import Dict, Any, Optional, List
from models.category import Category
from models.calculation_state import CalculationState, CalculationStateMachine
from strategies import CalculationStrategy, StandardCategoryStrategy, CustomCategoryStrategy


class CalculationContext:
    """
    Контекст расчёта.
    
    Объединяет:
    - Category (категория товара)
    - CalculationStateMachine (состояние расчёта)
    - CalculationStrategy (стратегия расчёта)
    
    Управляет:
    - Выбором стратегии на основе категории
    - Переходами между состояниями
    - Параметрами расчёта
    - Валидацией данных
    """
    
    def __init__(self):
        """Инициализирует пустой контекст"""
        self.category: Optional[Category] = None
        self.state_machine: CalculationStateMachine = CalculationStateMachine()
        self.strategy: Optional[CalculationStrategy] = None
        
        self.base_params: Dict[str, Any] = {}
        self.custom_logistics: Dict[str, Any] = {}
        self.result: Optional[Dict[str, Any]] = None
    
    def set_category(self, category: Category, base_params: Dict[str, Any]):
        """
        Устанавливает категорию и базовые параметры.
        Автоматически выбирает стратегию и переходит в нужное состояние.
        
        Args:
            category: Категория товара
            base_params: Базовые параметры (quantity, weight, price, markup)
        """
        self.category = category
        self.base_params = base_params
        
        # Выбираем стратегию на основе категории
        if category.needs_custom_params():
            self.strategy = CustomCategoryStrategy()
        else:
            self.strategy = StandardCategoryStrategy()
        
        print(f"📦 Категория: {category.name}")
        print(f"🎯 Стратегия: {self.strategy.get_strategy_name()}")
        
        # Определяем нужное состояние
        if self.strategy.requires_user_input(category):
            # Требуются кастомные параметры
            self.state_machine.transition_to(
                CalculationState.PENDING_PARAMS,
                context={'category': category.name}
            )
        else:
            # Параметры не требуются, можем сразу рассчитывать
            self.state_machine.transition_to(CalculationState.READY)
    
    def needs_user_input(self) -> bool:
        """
        Проверяет требуется ли ввод от пользователя.
        
        Returns:
            bool: True если требуются параметры
        """
        if not self.strategy or not self.category:
            return False
        
        return self.strategy.requires_user_input(self.category)
    
    def get_required_params(self) -> List[str]:
        """
        Получить список требуемых параметров.
        
        Returns:
            List[str]: Список названий параметров
        """
        if not self.strategy or not self.category:
            return []
        
        return self.strategy.get_required_params(self.category)
    
    def provide_custom_logistics(self, custom_logistics: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Предоставляет кастомные логистические параметры.
        
        Валидирует параметры и переходит в состояние READY если валидны.
        
        Args:
            custom_logistics: Кастомные параметры
            
        Returns:
            tuple[bool, List[str]]: (is_valid, errors)
        """
        if not self.strategy or not self.category:
            return False, ["Категория не установлена"]
        
        # Валидируем параметры
        is_valid, errors = self.strategy.validate_params(self.category, custom_logistics)
        
        if not is_valid:
            return False, errors
        
        # Сохраняем параметры
        self.custom_logistics = custom_logistics
        
        # Переходим в READY
        if self.state_machine.state == CalculationState.PENDING_PARAMS:
            self.state_machine.transition_to(CalculationState.READY)
        
        return True, []
    
    def can_calculate(self) -> tuple[bool, str]:
        """
        Проверяет можно ли выполнить расчёт.
        
        Returns:
            tuple[bool, str]: (can_calculate, reason)
        """
        # Проверка состояния
        if self.state_machine.state != CalculationState.READY:
            return False, f"Неправильное состояние: {self.state_machine.get_state_name()}"
        
        # Проверка категории
        if not self.category:
            return False, "Категория не установлена"
        
        # Проверка стратегии
        if not self.strategy:
            return False, "Стратегия не выбрана"
        
        # Проверка параметров
        if not self.base_params:
            return False, "Базовые параметры не установлены"
        
        # Проверка кастомных параметров если требуются
        if self.strategy.requires_user_input(self.category):
            if not self.custom_logistics:
                return False, "Требуются кастомные параметры"
        
        return True, "OK"
    
    def prepare_calculation_params(self) -> Dict[str, Any]:
        """
        Подготавливает параметры для передачи в calculator.
        
        Returns:
            Dict: Параметры готовые для calculator.calculate_cost()
            
        Raises:
            ValueError: Если невозможно подготовить параметры
        """
        can_calc, reason = self.can_calculate()
        if not can_calc:
            raise ValueError(f"Невозможно подготовить параметры: {reason}")
        
        # Используем стратегию для подготовки параметров
        calc_params = self.strategy.prepare_calculation_params(
            self.category,
            self.base_params,
            self.custom_logistics if self.custom_logistics else None
        )
        
        return calc_params
    
    def mark_calculated(self, result: Dict[str, Any]):
        """
        Помечает расчёт как выполненный и сохраняет результат.
        
        Args:
            result: Результат расчёта
        """
        self.result = result
        
        # Извлекаем cost_price для контекста
        cost_price_rub = None
        if 'cost_price' in result:
            cost_price_total = result['cost_price'].get('total', {})
            cost_price_rub = cost_price_total.get('rub')
        
        self.state_machine.transition_to(
            CalculationState.CALCULATED,
            context={'cost_price_rub': cost_price_rub}
        )
    
    def mark_saved(self, calculation_id: int):
        """
        Помечает расчёт как сохранённый в БД.
        
        Args:
            calculation_id: ID расчёта в БД
        """
        self.state_machine.transition_to(
            CalculationState.SAVED,
            context={'calculation_id': calculation_id}
        )
    
    def mark_error(self, error_message: str):
        """
        Помечает расчёт как завершившийся с ошибкой.
        
        Args:
            error_message: Сообщение об ошибке
        """
        self.state_machine.transition_to(
            CalculationState.ERROR,
            context={'error': error_message}
        )
    
    def reset(self):
        """Сбрасывает контекст в начальное состояние"""
        self.category = None
        self.strategy = None
        self.base_params = {}
        self.custom_logistics = {}
        self.result = None
        self.state_machine.reset()
    
    def get_current_state(self) -> CalculationState:
        """
        Получить текущее состояние.
        
        Returns:
            CalculationState: Текущее состояние
        """
        return self.state_machine.state
    
    def get_state_name(self) -> str:
        """
        Получить человекочитаемое название состояния.
        
        Returns:
            str: Название состояния
        """
        return self.state_machine.get_state_name()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализует контекст в словарь.
        
        Returns:
            Dict: Данные контекста
        """
        return {
            'category': self.category.to_dict() if self.category else None,
            'state': self.state_machine.to_dict(),
            'strategy': self.strategy.get_strategy_name() if self.strategy else None,
            'base_params': self.base_params,
            'custom_logistics': self.custom_logistics,
            'needs_user_input': self.needs_user_input(),
            'required_params': self.get_required_params(),
            'can_calculate': self.can_calculate()[0],
            'has_result': self.result is not None
        }
    
    def __repr__(self):
        cat_name = self.category.name if self.category else 'None'
        state_name = self.state_machine.get_state_name()
        strategy_name = self.strategy.get_strategy_name() if self.strategy else 'None'
        return f"<CalculationContext category={cat_name} state={state_name} strategy={strategy_name}>"

