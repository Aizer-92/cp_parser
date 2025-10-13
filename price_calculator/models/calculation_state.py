"""
Calculation State Machine for Price Calculator
Manages calculation lifecycle and state transitions
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime


class CalculationState(Enum):
    """
    Состояния жизненного цикла расчёта.
    Каждое состояние представляет этап процесса расчёта.
    """
    DRAFT = "draft"                    # Начальное состояние, товар введён
    PENDING_PARAMS = "pending_params"  # Ожидает ввода кастомных параметров
    READY = "ready"                    # Готов к расчёту
    CALCULATED = "calculated"          # Расчёт выполнен
    SAVED = "saved"                    # Сохранён в БД
    ERROR = "error"                    # Ошибка в процессе
    
    def __str__(self):
        return self.value


class StateTransitionError(Exception):
    """Ошибка при невалидном переходе между состояниями"""
    pass


class CalculationStateMachine:
    """
    Конечный автомат (FSM) для управления состоянием расчёта.
    
    Гарантирует:
    - Только валидные переходы между состояниями
    - История всех переходов
    - Хуки при входе/выходе из состояний
    - Невозможность некорректных состояний
    """
    
    # Определение разрешённых переходов
    TRANSITIONS = {
        CalculationState.DRAFT: [
            CalculationState.PENDING_PARAMS,
            CalculationState.READY,
            CalculationState.ERROR
        ],
        CalculationState.PENDING_PARAMS: [
            CalculationState.READY,
            CalculationState.DRAFT,
            CalculationState.ERROR
        ],
        CalculationState.READY: [
            CalculationState.CALCULATED,
            CalculationState.DRAFT,  # Для редактирования
            CalculationState.ERROR
        ],
        CalculationState.CALCULATED: [
            CalculationState.SAVED,
            CalculationState.DRAFT,  # Для редактирования
            CalculationState.ERROR
        ],
        CalculationState.SAVED: [
            CalculationState.DRAFT  # Для редактирования
        ],
        CalculationState.ERROR: [
            CalculationState.DRAFT  # Восстановление после ошибки
        ]
    }
    
    # Человекочитаемые названия состояний
    STATE_NAMES = {
        CalculationState.DRAFT: "Черновик",
        CalculationState.PENDING_PARAMS: "Ожидание параметров",
        CalculationState.READY: "Готов к расчёту",
        CalculationState.CALCULATED: "Рассчитан",
        CalculationState.SAVED: "Сохранён",
        CalculationState.ERROR: "Ошибка"
    }
    
    def __init__(self, initial_state: CalculationState = CalculationState.DRAFT):
        """
        Инициализирует state machine.
        
        Args:
            initial_state: Начальное состояние (по умолчанию DRAFT)
        """
        self.state = initial_state
        self.history: List[Dict[str, Any]] = [{
            'state': initial_state,
            'timestamp': datetime.now(),
            'context': {}
        }]
        self._hooks: Dict[str, List[Callable]] = {
            'on_enter': {},
            'on_exit': {}
        }
    
    def can_transition_to(self, target_state: CalculationState) -> bool:
        """
        Проверяет возможность перехода в целевое состояние.
        
        Args:
            target_state: Целевое состояние
            
        Returns:
            bool: True если переход возможен
        """
        allowed_states = self.TRANSITIONS.get(self.state, [])
        return target_state in allowed_states
    
    def get_allowed_transitions(self) -> List[CalculationState]:
        """
        Получить список разрешённых переходов из текущего состояния.
        
        Returns:
            List[CalculationState]: Список доступных состояний
        """
        return self.TRANSITIONS.get(self.state, [])
    
    def transition_to(self, target_state: CalculationState, context: Dict[str, Any] = None) -> bool:
        """
        Выполняет переход в новое состояние.
        
        Args:
            target_state: Целевое состояние
            context: Контекст перехода (дополнительные данные)
            
        Returns:
            bool: True если переход выполнен успешно
            
        Raises:
            StateTransitionError: Если переход невозможен
        """
        if not self.can_transition_to(target_state):
            allowed = [s.value for s in self.get_allowed_transitions()]
            raise StateTransitionError(
                f"Невозможен переход: {self.state.value} → {target_state.value}. "
                f"Разрешённые переходы: {allowed}"
            )
        
        # Вызываем хук выхода из текущего состояния
        self._trigger_hooks('on_exit', self.state, context or {})
        
        # Сохраняем предыдущее состояние
        previous_state = self.state
        
        # Переходим в новое состояние
        self.state = target_state
        
        # Записываем в историю
        self.history.append({
            'from': previous_state,
            'to': target_state,
            'timestamp': datetime.now(),
            'context': context or {}
        })
        
        # Вызываем хук входа в новое состояние
        self._trigger_hooks('on_enter', target_state, context or {})
        
        # Вызываем встроенные обработчики
        self._handle_state_enter(target_state, context or {})
        
        return True
    
    def register_hook(self, hook_type: str, state: CalculationState, callback: Callable):
        """
        Регистрирует хук для состояния.
        
        Args:
            hook_type: Тип хука ('on_enter' или 'on_exit')
            state: Состояние для которого регистрируем хук
            callback: Функция-обработчик
        """
        if hook_type not in self._hooks:
            self._hooks[hook_type] = {}
        
        if state not in self._hooks[hook_type]:
            self._hooks[hook_type][state] = []
        
        self._hooks[hook_type][state].append(callback)
    
    def _trigger_hooks(self, hook_type: str, state: CalculationState, context: Dict[str, Any]):
        """Вызывает зарегистрированные хуки"""
        hooks = self._hooks.get(hook_type, {}).get(state, [])
        for hook in hooks:
            try:
                hook(self, context)
            except Exception as e:
                print(f"⚠️ Ошибка в хуке {hook_type} для {state.value}: {e}")
    
    def _handle_state_enter(self, state: CalculationState, context: Dict[str, Any]):
        """
        Встроенные обработчики входа в состояния.
        Можно использовать для логирования, уведомлений и т.д.
        """
        handlers = {
            CalculationState.PENDING_PARAMS: self._handle_pending_params,
            CalculationState.READY: self._handle_ready,
            CalculationState.CALCULATED: self._handle_calculated,
            CalculationState.SAVED: self._handle_saved,
            CalculationState.ERROR: self._handle_error
        }
        
        handler = handlers.get(state)
        if handler:
            handler(context)
    
    def _handle_pending_params(self, context: Dict):
        """Обработка состояния ожидания параметров"""
        category = context.get('category', 'неизвестной категории')
        print(f"⏳ Ожидание ввода параметров для: {category}")
    
    def _handle_ready(self, context: Dict):
        """Обработка готовности к расчёту"""
        print(f"✅ Готов к расчёту")
    
    def _handle_calculated(self, context: Dict):
        """Обработка завершённого расчёта"""
        cost_price = context.get('cost_price_rub', 'Н/Д')
        print(f"💰 Расчёт завершён. Себестоимость: {cost_price} ₽")
    
    def _handle_saved(self, context: Dict):
        """Обработка сохранения"""
        calc_id = context.get('calculation_id', 'Н/Д')
        print(f"💾 Расчёт сохранён в БД. ID: {calc_id}")
    
    def _handle_error(self, context: Dict):
        """Обработка ошибки"""
        error_message = context.get('error', 'Неизвестная ошибка')
        print(f"❌ Ошибка в расчёте: {error_message}")
    
    def get_state_name(self) -> str:
        """
        Получить человекочитаемое название текущего состояния.
        
        Returns:
            str: Название состояния на русском
        """
        return self.STATE_NAMES.get(self.state, self.state.value)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Получить полную историю переходов.
        
        Returns:
            List[Dict]: История переходов с метаданными
        """
        return self.history.copy()
    
    def get_last_transition(self) -> Optional[Dict[str, Any]]:
        """
        Получить последний переход.
        
        Returns:
            Optional[Dict]: Данные последнего перехода или None
        """
        if len(self.history) > 1:
            return self.history[-1]
        return None
    
    def reset(self, initial_state: CalculationState = CalculationState.DRAFT):
        """
        Сбросить state machine в начальное состояние.
        
        Args:
            initial_state: Состояние для сброса
        """
        self.state = initial_state
        self.history = [{
            'state': initial_state,
            'timestamp': datetime.now(),
            'context': {}
        }]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализация state machine в словарь.
        
        Returns:
            Dict: Данные для сохранения
        """
        return {
            'current_state': self.state.value,
            'state_name': self.get_state_name(),
            'allowed_transitions': [s.value for s in self.get_allowed_transitions()],
            'history': [
                {
                    'from': h.get('from').value if h.get('from') else None,
                    'to': h.get('to').value if h.get('to') else h.get('state').value,
                    'timestamp': h['timestamp'].isoformat(),
                    'context': h.get('context', {})
                }
                for h in self.history
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationStateMachine':
        """
        Десериализация state machine из словаря.
        
        Args:
            data: Сохранённые данные
            
        Returns:
            CalculationStateMachine: Восстановленный экземпляр
        """
        state_value = data.get('current_state', 'draft')
        state = CalculationState(state_value)
        
        machine = cls(initial_state=state)
        
        # Восстанавливаем историю если есть
        if 'history' in data:
            machine.history = []
            for h in data['history']:
                machine.history.append({
                    'from': CalculationState(h['from']) if h.get('from') else None,
                    'to': CalculationState(h['to']) if h.get('to') else None,
                    'state': CalculationState(h['to']) if h.get('to') else CalculationState(h.get('state', 'draft')),
                    'timestamp': datetime.fromisoformat(h['timestamp']),
                    'context': h.get('context', {})
                })
        
        return machine
    
    def __repr__(self):
        return f"<CalculationStateMachine state={self.state.value} transitions={len(self.history)}>"
    
    def __str__(self):
        return f"State: {self.get_state_name()} ({self.state.value})"






