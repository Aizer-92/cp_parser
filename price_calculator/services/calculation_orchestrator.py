"""
Calculation Orchestrator
High-level orchestration for price calculations
"""

from typing import Dict, Any, Optional
from models.category import Category
from models.calculation_state import CalculationState
from services.calculation_context import CalculationContext
from price_calculator import PriceCalculator


class CalculationOrchestrator:
    """
    Оркестратор расчётов.
    
    Высокоуровневая обёртка над CalculationContext и price_calculator.
    Упрощает выполнение расчётов:
    1. Загружает категорию
    2. Выбирает стратегию
    3. Валидирует параметры
    4. Выполняет расчёт
    5. Управляет состоянием
    """
    
    def __init__(self, categories: Dict[str, Any]):
        """
        Инициализирует оркестратор.
        
        Args:
            categories: Словарь категорий {category_name: category_data}
        """
        self.categories = categories
        self.context: Optional[CalculationContext] = None
        self.calculator = PriceCalculator()  # Экземпляр калькулятора
    
    def start_calculation(
        self,
        product_name: str,
        quantity: int,
        weight_kg: float,
        unit_price_yuan: float,
        markup: float,
        forced_category: Optional[str] = None,
        product_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Начинает новый расчёт.
        
        Args:
            product_name: Название товара
            quantity: Количество
            weight_kg: Вес одной единицы (кг)
            unit_price_yuan: Цена за единицу (юань)
            markup: Наценка (например, 1.7 для 70%)
            forced_category: Принудительная категория (опционально)
            product_url: URL товара или WeChat (опционально)
            
        Returns:
            Dict с информацией о состоянии:
            {
                'state': str,
                'needs_user_input': bool,
                'required_params': List[str],
                'category': str,
                'message': str
            }
        """
        # Создаём новый контекст
        self.context = CalculationContext()
        
        # Определяем категорию
        category_name = forced_category if forced_category else self._detect_category(product_name)
        
        if category_name not in self.categories:
            # Категория не найдена - используем "Новая категория"
            category_name = "Новая категория"
        
        # Загружаем данные категории
        category_data = self.categories.get(category_name, {})
        category = Category.from_dict(category_data)
        
        # Базовые параметры
        # ВАЖНО: calculate_cost() ожидает 'price_yuan', а не 'unit_price_yuan'
        base_params = {
            'product_name': product_name,
            'quantity': quantity,
            'weight_kg': weight_kg,
            'price_yuan': unit_price_yuan,  # Используем правильное имя параметра
            'markup': markup,
            'product_url': product_url  # URL товара или WeChat
        }
        
        # Устанавливаем категорию в контекст
        self.context.set_category(category, base_params)
        
        # Формируем ответ
        response = {
            'state': self.context.get_state_name(),
            'needs_user_input': self.context.needs_user_input(),
            'required_params': self.context.get_required_params(),
            'category': category.name,
            'message': self._get_state_message()
        }
        
        return response
    
    def provide_custom_params(self, custom_logistics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Предоставляет кастомные параметры.
        
        Args:
            custom_logistics: Кастомные логистические параметры
            
        Returns:
            Dict с результатом валидации:
            {
                'valid': bool,
                'errors': List[str],
                'state': str,
                'can_calculate': bool
            }
            
        Raises:
            ValueError: Если контекст не инициализирован
        """
        if not self.context:
            raise ValueError("Контекст не инициализирован. Вызовите start_calculation() сначала.")
        
        is_valid, errors = self.context.provide_custom_logistics(custom_logistics)
        
        can_calc, _ = self.context.can_calculate()
        
        return {
            'valid': is_valid,
            'errors': errors,
            'state': self.context.get_state_name(),
            'can_calculate': can_calc,
            'message': self._get_state_message()
        }
    
    def calculate(self) -> Dict[str, Any]:
        """
        Выполняет расчёт.
        
        Returns:
            Dict с результатом расчёта или ошибкой:
            {
                'success': bool,
                'result': Dict (если success=True),
                'error': str (если success=False),
                'state': str
            }
            
        Raises:
            ValueError: Если контекст не инициализирован
        """
        if not self.context:
            raise ValueError("Контекст не инициализирован. Вызовите start_calculation() сначала.")
        
        # Проверяем готовность
        can_calc, reason = self.context.can_calculate()
        if not can_calc:
            return {
                'success': False,
                'error': f"Невозможно выполнить расчёт: {reason}",
                'state': self.context.get_state_name()
            }
        
        try:
            # Подготавливаем параметры
            calc_params = self.context.prepare_calculation_params()
            
            # Выполняем расчёт через PriceCalculator
            # ИСПРАВЛЕНИЕ: Метод называется calculate_cost, а не calculate_routes
            result = self.calculator.calculate_cost(**calc_params)
            
            # Помечаем как рассчитанный
            self.context.mark_calculated(result)
            
            return {
                'success': True,
                'result': result,
                'state': self.context.get_state_name(),
                'message': 'Расчёт выполнен успешно'
            }
            
        except Exception as e:
            # Помечаем ошибку
            self.context.mark_error(str(e))
            
            return {
                'success': False,
                'error': str(e),
                'state': self.context.get_state_name()
            }
    
    def get_context_info(self) -> Dict[str, Any]:
        """
        Получить информацию о текущем контексте.
        
        Returns:
            Dict с информацией о контексте
            
        Raises:
            ValueError: Если контекст не инициализирован
        """
        if not self.context:
            raise ValueError("Контекст не инициализирован.")
        
        return self.context.to_dict()
    
    def mark_saved(self, calculation_id: int):
        """
        Помечает расчёт как сохранённый.
        
        Args:
            calculation_id: ID расчёта в БД
            
        Raises:
            ValueError: Если контекст не инициализирован
        """
        if not self.context:
            raise ValueError("Контекст не инициализирован.")
        
        self.context.mark_saved(calculation_id)
    
    def reset(self):
        """Сбрасывает оркестратор (удаляет контекст)"""
        if self.context:
            self.context.reset()
        self.context = None
    
    def _detect_category(self, product_name: str) -> str:
        """
        Определяет категорию по названию товара.
        
        Args:
            product_name: Название товара
            
        Returns:
            str: Название категории или "Новая категория"
        """
        # ИСПРАВЛЕНИЕ: Используем существующую проверенную логику из category_detector
        try:
            from category_detector import detect_category_from_name
            detected = detect_category_from_name(product_name)
            
            # Если detect_category_from_name вернул категорию, проверяем что она есть в нашем списке
            if detected and detected in self.categories:
                return detected
        except Exception as e:
            print(f"⚠️ Ошибка при определении категории через category_detector: {e}")
        
        # Fallback: простой поиск по ключевым словам
        product_lower = product_name.lower()
        
        for category_name, category_data in self.categories.items():
            keywords = category_data.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in product_lower:
                    return category_name
        
        # Если не найдено - вернём "Новая категория"
        return "Новая категория"
    
    def _get_state_message(self) -> str:
        """
        Получить человекочитаемое сообщение для текущего состояния.
        
        Returns:
            str: Сообщение
        """
        if not self.context:
            return "Контекст не инициализирован"
        
        state = self.context.get_current_state()
        
        messages = {
            CalculationState.DRAFT: "Готово к новому расчёту",
            CalculationState.PENDING_PARAMS: f"Требуется ввод параметров: {', '.join(self.context.get_required_params())}",
            CalculationState.READY: "Готово к расчёту",
            CalculationState.CALCULATED: "Расчёт выполнен",
            CalculationState.SAVED: "Расчёт сохранён",
            CalculationState.ERROR: "Ошибка в расчёте"
        }
        
        return messages.get(state, f"Неизвестное состояние: {state.value}")

