# Профессиональные решения для системы пользовательских категорий

## 🎯 Анализ требований

### Функциональные требования:
1. Пользователь может создавать расчёты для любых товаров
2. Если товар не распознан - можно ввести параметры вручную
3. Параметры должны сохраняться и переиспользоваться
4. История должна отображать корректные цены
5. UX должен быть простым и не навязчивым

### Нефункциональные требования:
1. **Устойчивость** - не должна ломаться при добавлении новых категорий
2. **Масштабируемость** - легко добавлять новые типы параметров
3. **Поддерживаемость** - понятная архитектура
4. **Производительность** - быстрая работа
5. **Тестируемость** - легко покрыть тестами

---

## 🏗️ Профессиональные архитектурные решения

### Решение 1: "Calculation State Machine" ⭐⭐⭐⭐⭐ (ЛУЧШЕЕ)

#### Концепция: Конечный автомат (FSM) для управления состоянием расчёта

**Состояния расчёта:**
```
DRAFT → PENDING_PARAMS → READY → CALCULATED → SAVED
```

**Диаграмма состояний:**
```
┌─────────┐
│  DRAFT  │ (товар введён, категория определена)
└────┬────┘
     │
     ├─→ (категория известна) ─→ [READY]
     │
     └─→ (категория требует параметров) ─→ [PENDING_PARAMS]
                                                │
                                                ├─→ (параметры введены) ─→ [READY]
                                                │
                                                └─→ (отменено) ─→ [DRAFT]
[READY] ─→ (расчёт) ─→ [CALCULATED] ─→ (сохранение) ─→ [SAVED]
```

#### Архитектура:

**1. Модель Calculation с состоянием:**

```python
# models/calculation_state.py
from enum import Enum
from typing import Optional, Dict, Any

class CalculationState(Enum):
    DRAFT = "draft"                    # Начальное состояние
    PENDING_PARAMS = "pending_params"  # Ожидает ввод параметров
    READY = "ready"                    # Готов к расчёту
    CALCULATED = "calculated"          # Рассчитан
    SAVED = "saved"                    # Сохранён в БД

class CalculationStateMachine:
    """Управление переходами между состояниями"""
    
    TRANSITIONS = {
        CalculationState.DRAFT: [
            CalculationState.PENDING_PARAMS,
            CalculationState.READY
        ],
        CalculationState.PENDING_PARAMS: [
            CalculationState.READY,
            CalculationState.DRAFT
        ],
        CalculationState.READY: [
            CalculationState.CALCULATED
        ],
        CalculationState.CALCULATED: [
            CalculationState.SAVED,
            CalculationState.DRAFT  # Для редактирования
        ],
        CalculationState.SAVED: [
            CalculationState.DRAFT  # Для редактирования
        ]
    }
    
    def __init__(self, initial_state: CalculationState = CalculationState.DRAFT):
        self.state = initial_state
        self.history = [initial_state]
    
    def can_transition_to(self, target_state: CalculationState) -> bool:
        """Проверяет возможность перехода"""
        return target_state in self.TRANSITIONS.get(self.state, [])
    
    def transition_to(self, target_state: CalculationState, context: Dict[str, Any] = None):
        """Выполняет переход в новое состояние"""
        if not self.can_transition_to(target_state):
            raise ValueError(
                f"Invalid transition: {self.state.value} → {target_state.value}"
            )
        
        self.state = target_state
        self.history.append(target_state)
        
        # Вызываем хуки перехода
        self._on_enter_state(target_state, context)
    
    def _on_enter_state(self, state: CalculationState, context: Dict[str, Any] = None):
        """Хук при входе в состояние"""
        handlers = {
            CalculationState.PENDING_PARAMS: self._handle_pending_params,
            CalculationState.READY: self._handle_ready,
            CalculationState.CALCULATED: self._handle_calculated,
        }
        
        handler = handlers.get(state)
        if handler:
            handler(context or {})
    
    def _handle_pending_params(self, context: Dict):
        """Обработка состояния ожидания параметров"""
        print(f"⏳ Ожидание ввода параметров для категории: {context.get('category')}")
    
    def _handle_ready(self, context: Dict):
        """Обработка готовности к расчёту"""
        print(f"✅ Готов к расчёту")
    
    def _handle_calculated(self, context: Dict):
        """Обработка завершённого расчёта"""
        print(f"💰 Расчёт завершён: {context.get('cost_price')} ₽")
```

**2. Категория с метаданными:**

```python
# models/category.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class CategoryRequirements:
    """Требования категории к параметрам"""
    requires_logistics_rate: bool = False
    requires_duty_rate: bool = False
    requires_vat_rate: bool = False
    requires_specific_rate: bool = False
    
    def is_complete(self, provided_params: Dict) -> bool:
        """Проверяет все ли требуемые параметры предоставлены"""
        checks = []
        
        if self.requires_logistics_rate:
            checks.append('custom_rate' in provided_params)
        if self.requires_duty_rate:
            checks.append('duty_rate' in provided_params)
        if self.requires_vat_rate:
            checks.append('vat_rate' in provided_params)
        if self.requires_specific_rate:
            checks.append('specific_rate' in provided_params)
        
        return all(checks)

@dataclass
class Category:
    """Модель категории товара"""
    id: int
    name: str
    material: str = ""
    
    # Базовые ставки (могут быть None)
    rail_base: Optional[float] = None
    air_base: Optional[float] = None
    
    # Требования к параметрам
    requirements: CategoryRequirements = field(default_factory=CategoryRequirements)
    
    # Метаданные
    keywords: List[str] = field(default_factory=list)
    description: str = ""
    
    def needs_custom_params(self) -> bool:
        """Проверяет нужны ли кастомные параметры"""
        # Если базовые ставки не определены
        if self.rail_base is None or self.rail_base == 0:
            return True
        if self.air_base is None or self.air_base == 0:
            return True
        
        # Или есть явные требования
        return (self.requirements.requires_logistics_rate or
                self.requirements.requires_duty_rate or
                self.requirements.requires_vat_rate or
                self.requirements.requires_specific_rate)
    
    def validate_params(self, params: Dict) -> tuple[bool, List[str]]:
        """Валидирует предоставленные параметры"""
        errors = []
        
        if self.requirements.requires_logistics_rate and 'custom_rate' not in params:
            errors.append("Требуется логистическая ставка")
        
        if self.requirements.requires_duty_rate and 'duty_rate' not in params:
            errors.append("Требуется ставка пошлины")
        
        return len(errors) == 0, errors
```

**3. Сервис управления расчётами:**

```python
# services/calculation_manager.py
class CalculationManager:
    """Управление жизненным циклом расчёта"""
    
    def __init__(self, calculator: PriceCalculator, db):
        self.calculator = calculator
        self.db = db
    
    def create_calculation(self, product_name: str, **params) -> Dict:
        """Создаёт новый расчёт"""
        # 1. Определяем категорию
        category = self.calculator.find_category_by_name(product_name)
        
        # 2. Создаём state machine
        state_machine = CalculationStateMachine()
        
        # 3. Определяем начальное состояние
        if category.needs_custom_params():
            state_machine.transition_to(
                CalculationState.PENDING_PARAMS,
                context={'category': category.name}
            )
        else:
            state_machine.transition_to(CalculationState.READY)
        
        return {
            'id': None,
            'state': state_machine.state.value,
            'category': category,
            'params': params,
            'custom_logistics': {},
            'result': None
        }
    
    def provide_custom_params(self, calculation: Dict, custom_logistics: Dict) -> Dict:
        """Предоставляет кастомные параметры"""
        state_machine = CalculationStateMachine(
            CalculationState(calculation['state'])
        )
        
        # Валидация параметров
        category = calculation['category']
        is_valid, errors = category.validate_params(custom_logistics)
        
        if not is_valid:
            return {
                'success': False,
                'errors': errors
            }
        
        # Обновляем расчёт
        calculation['custom_logistics'] = custom_logistics
        state_machine.transition_to(CalculationState.READY)
        calculation['state'] = state_machine.state.value
        
        return {
            'success': True,
            'calculation': calculation
        }
    
    def perform_calculation(self, calculation: Dict) -> Dict:
        """Выполняет расчёт"""
        state_machine = CalculationStateMachine(
            CalculationState(calculation['state'])
        )
        
        # Проверяем что можем рассчитывать
        if state_machine.state != CalculationState.READY:
            raise ValueError(f"Cannot calculate in state: {state_machine.state.value}")
        
        # Выполняем расчёт
        result = self.calculator.calculate_cost(
            **calculation['params'],
            custom_logistics_params=calculation['custom_logistics']
        )
        
        calculation['result'] = result
        state_machine.transition_to(
            CalculationState.CALCULATED,
            context={'cost_price': result.get('cost_price', {}).get('total', {}).get('rub')}
        )
        calculation['state'] = state_machine.state.value
        
        return calculation
    
    def save_calculation(self, calculation: Dict) -> int:
        """Сохраняет расчёт в БД"""
        state_machine = CalculationStateMachine(
            CalculationState(calculation['state'])
        )
        
        if state_machine.state != CalculationState.CALCULATED:
            raise ValueError("Can only save CALCULATED calculations")
        
        # Сохраняем
        calc_id = self.db.save_calculation(calculation)
        
        state_machine.transition_to(CalculationState.SAVED)
        calculation['state'] = state_machine.state.value
        calculation['id'] = calc_id
        
        return calc_id
```

**4. Фронтенд с реактивным состоянием:**

```javascript
// composables/useCalculationState.js
import { ref, computed, watch } from 'vue';

export function useCalculationState(initialState = 'draft') {
    const state = ref(initialState);
    const history = ref([initialState]);
    
    // Определение переходов
    const transitions = {
        draft: ['pending_params', 'ready'],
        pending_params: ['ready', 'draft'],
        ready: ['calculated'],
        calculated: ['saved', 'draft'],
        saved: ['draft']
    };
    
    // Computed свойства для состояний
    const isDraft = computed(() => state.value === 'draft');
    const isPendingParams = computed(() => state.value === 'pending_params');
    const isReady = computed(() => state.value === 'ready');
    const isCalculated = computed(() => state.value === 'calculated');
    const isSaved = computed(() => state.value === 'saved');
    
    // Проверка возможности перехода
    const canTransitionTo = (targetState) => {
        const allowed = transitions[state.value] || [];
        return allowed.includes(targetState);
    };
    
    // Переход в новое состояние
    const transitionTo = (targetState, context = {}) => {
        if (!canTransitionTo(targetState)) {
            console.error(`Invalid transition: ${state.value} → ${targetState}`);
            return false;
        }
        
        state.value = targetState;
        history.value.push(targetState);
        
        // Вызываем хуки
        onEnterState(targetState, context);
        
        return true;
    };
    
    // Хуки входа в состояния
    const onEnterState = (newState, context) => {
        const handlers = {
            pending_params: () => {
                console.log('⏳ Требуется ввод параметров');
                // Можно эмитить событие для UI
            },
            ready: () => {
                console.log('✅ Готов к расчёту');
            },
            calculated: () => {
                console.log('💰 Расчёт завершён');
            }
        };
        
        const handler = handlers[newState];
        if (handler) handler(context);
    };
    
    return {
        state,
        history,
        isDraft,
        isPendingParams,
        isReady,
        isCalculated,
        isSaved,
        canTransitionTo,
        transitionTo
    };
}
```

```vue
<!-- PriceCalculatorAppV2.vue -->
<script setup>
import { useCalculationState } from './composables/useCalculationState';

const calculationState = useCalculationState();

// Автоматическое управление UI на основе состояния
watch(() => calculationState.isPendingParams.value, (isPending) => {
    if (isPending) {
        // Открыть форму параметров
        showParamsModal.value = true;
    }
});

const handleCategoryDetected = (category) => {
    if (category.needs_custom_params) {
        calculationState.transitionTo('pending_params', { category });
    } else {
        calculationState.transitionTo('ready');
    }
};

const handleParamsProvided = (customParams) => {
    // Сохраняем параметры
    customLogistics.value = customParams;
    
    // Переходим в ready
    calculationState.transitionTo('ready');
    
    // Автоматически запускаем расчёт
    performCalculation();
};

const performCalculation = async () => {
    const result = await axios.post('/api/v2/calculate', {
        ...formData.value,
        custom_logistics: customLogistics.value,
        state: calculationState.state.value
    });
    
    calculationState.transitionTo('calculated', { 
        cost_price: result.data.cost_price 
    });
};
</script>

<template>
    <!-- UI адаптируется под состояние -->
    <div class="calculator">
        <!-- Индикатор состояния -->
        <StateIndicator :state="calculationState.state.value" />
        
        <!-- Форма ввода (всегда видна) -->
        <ProductForm 
            v-model="formData"
            :disabled="!calculationState.isDraft"
        />
        
        <!-- Модальное окно параметров (открывается автоматически) -->
        <CustomParamsModal
            v-if="calculationState.isPendingParams"
            :category="currentCategory"
            @submit="handleParamsProvided"
            @cancel="calculationState.transitionTo('draft')"
        />
        
        <!-- Результаты (показываются после расчёта) -->
        <CalculationResults
            v-if="calculationState.isCalculated || calculationState.isSaved"
            :result="calculationResult"
        />
        
        <!-- Кнопки действий (адаптивные) -->
        <div class="actions">
            <button 
                v-if="calculationState.isReady"
                @click="performCalculation"
            >
                Рассчитать
            </button>
            
            <button
                v-if="calculationState.isCalculated"
                @click="saveCalculation"
            >
                Сохранить
            </button>
            
            <button
                v-if="calculationState.isSaved"
                @click="calculationState.transitionTo('draft')"
            >
                Новый расчёт
            </button>
        </div>
    </div>
</template>
```

#### Преимущества State Machine:

✅ **Явное управление состоянием** - всегда понятно в каком состоянии расчёт  
✅ **Невозможность невалидных состояний** - FSM гарантирует корректность  
✅ **Легко тестировать** - тесты переходов между состояниями  
✅ **Масштабируемость** - легко добавлять новые состояния  
✅ **Визуализация** - можно нарисовать диаграмму состояний  
✅ **Отладка** - история переходов для диагностики  
✅ **Предсказуемость** - одинаковый результат при одинаковых входных данных  

#### Недостатки:

❌ Требует рефакторинга существующего кода  
❌ Более сложная начальная реализация  
❌ Нужно обучить команду паттерну FSM  

---

### Решение 2: "Calculation Context with Strategy Pattern" ⭐⭐⭐⭐

#### Концепция: Контекст расчёта + стратегии для разных типов категорий

**Архитектура:**

```python
# models/calculation_context.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class CalculationStrategy(ABC):
    """Базовая стратегия расчёта"""
    
    @abstractmethod
    def requires_user_input(self, category: Category) -> bool:
        """Требуется ли ввод пользователя"""
        pass
    
    @abstractmethod
    def get_required_params(self, category: Category) -> List[str]:
        """Какие параметры требуются"""
        pass
    
    @abstractmethod
    def calculate(self, context: 'CalculationContext') -> Dict[str, Any]:
        """Выполнить расчёт"""
        pass

class StandardCategoryStrategy(CalculationStrategy):
    """Стратегия для стандартных категорий"""
    
    def requires_user_input(self, category: Category) -> bool:
        return False
    
    def get_required_params(self, category: Category) -> List[str]:
        return []
    
    def calculate(self, context: 'CalculationContext') -> Dict[str, Any]:
        # Используем базовые ставки категории
        return context.calculator.calculate_cost(
            **context.params,
            category=context.category
        )

class CustomCategoryStrategy(CalculationStrategy):
    """Стратегия для кастомных категорий"""
    
    def requires_user_input(self, category: Category) -> bool:
        return not category.rail_base or not category.air_base
    
    def get_required_params(self, category: Category) -> List[str]:
        params = []
        if not category.rail_base:
            params.append('rail_rate')
        if not category.air_base:
            params.append('air_rate')
        return params
    
    def calculate(self, context: 'CalculationContext') -> Dict[str, Any]:
        # Используем кастомные параметры
        return context.calculator.calculate_cost(
            **context.params,
            custom_logistics_params=context.custom_logistics
        )

class CalculationContext:
    """Контекст расчёта с выбором стратегии"""
    
    def __init__(self, calculator: PriceCalculator):
        self.calculator = calculator
        self.category: Optional[Category] = None
        self.params: Dict[str, Any] = {}
        self.custom_logistics: Dict[str, Any] = {}
        self.strategy: Optional[CalculationStrategy] = None
        self.result: Optional[Dict[str, Any]] = None
    
    def set_product(self, product_name: str, **params):
        """Устанавливает товар и определяет стратегию"""
        self.category = self.calculator.find_category_by_name(product_name)
        self.params = params
        
        # Выбираем стратегию на основе категории
        if self.category.needs_custom_params():
            self.strategy = CustomCategoryStrategy()
        else:
            self.strategy = StandardCategoryStrategy()
    
    def needs_user_input(self) -> bool:
        """Требуется ли ввод от пользователя"""
        if not self.strategy:
            return False
        return self.strategy.requires_user_input(self.category)
    
    def get_required_params(self) -> List[str]:
        """Получить список требуемых параметров"""
        if not self.strategy:
            return []
        return self.strategy.get_required_params(self.category)
    
    def provide_custom_logistics(self, custom_logistics: Dict[str, Any]):
        """Предоставить кастомные параметры"""
        self.custom_logistics = custom_logistics
    
    def calculate(self) -> Dict[str, Any]:
        """Выполнить расчёт используя текущую стратегию"""
        if not self.strategy:
            raise ValueError("Strategy not set. Call set_product first.")
        
        self.result = self.strategy.calculate(self)
        return self.result
```

#### Преимущества Strategy Pattern:

✅ **Гибкость** - легко добавлять новые стратегии  
✅ **Разделение ответственности** - каждая стратегия независима  
✅ **Тестируемость** - легко тестировать отдельные стратегии  
✅ **Расширяемость** - новые типы категорий = новые стратегии  

---

### Решение 3: "Event-Driven Architecture" ⭐⭐⭐⭐⭐

#### Концепция: События для управления жизненным циклом

```python
# events/calculation_events.py
from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime

@dataclass
class CalculationEvent:
    """Базовое событие расчёта"""
    calculation_id: str
    timestamp: datetime
    data: Dict[str, Any]

@dataclass
class CategoryDetectedEvent(CalculationEvent):
    """Категория определена"""
    category_name: str
    needs_custom_params: bool

@dataclass
class CustomParamsRequestedEvent(CalculationEvent):
    """Запрошен ввод кастомных параметров"""
    required_params: list

@dataclass
class CustomParamsProvidedEvent(CalculationEvent):
    """Кастомные параметры предоставлены"""
    custom_logistics: Dict

@dataclass
class CalculationCompletedEvent(CalculationEvent):
    """Расчёт завершён"""
    result: Dict

# Event Bus
class EventBus:
    """Шина событий"""
    
    def __init__(self):
        self._handlers = {}
    
    def subscribe(self, event_type: type, handler: callable):
        """Подписаться на событие"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event: CalculationEvent):
        """Опубликовать событие"""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")

# Обработчики событий
class CalculationEventHandlers:
    """Обработчики событий расчёта"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        self.event_bus.subscribe(CategoryDetectedEvent, self.on_category_detected)
        self.event_bus.subscribe(CustomParamsProvidedEvent, self.on_params_provided)
        self.event_bus.subscribe(CalculationCompletedEvent, self.on_calculation_completed)
    
    def on_category_detected(self, event: CategoryDetectedEvent):
        """Обработка определения категории"""
        if event.needs_custom_params:
            # Запрашиваем параметры
            self.event_bus.publish(CustomParamsRequestedEvent(
                calculation_id=event.calculation_id,
                timestamp=datetime.now(),
                data={},
                required_params=['custom_rate', 'duty_rate']
            ))
    
    def on_params_provided(self, event: CustomParamsProvidedEvent):
        """Обработка предоставления параметров"""
        print(f"Параметры получены для расчёта {event.calculation_id}")
        # Можно автоматически запустить расчёт
    
    def on_calculation_completed(self, event: CalculationCompletedEvent):
        """Обработка завершения расчёта"""
        print(f"Расчёт {event.calculation_id} завершён")
        # Можно отправить уведомление, сохранить в БД и т.д.
```

#### Преимущества Event-Driven:

✅ **Слабая связанность** - компоненты не знают друг о друге  
✅ **Масштабируемость** - легко добавлять новые обработчики  
✅ **Аудит** - автоматическая история всех событий  
✅ **Асинхронность** - события можно обрабатывать асинхронно  
✅ **Микросервисность** - готовность к разделению на микросервисы  

---

### Решение 4: "Builder Pattern для Calculation" ⭐⭐⭐

#### Концепция: Пошаговое построение расчёта

```python
class CalculationBuilder:
    """Строитель расчёта"""
    
    def __init__(self, calculator: PriceCalculator):
        self.calculator = calculator
        self._product_name = None
        self._category = None
        self._params = {}
        self._custom_logistics = {}
        self._validation_errors = []
    
    def with_product(self, product_name: str):
        """Установить товар"""
        self._product_name = product_name
        self._category = self.calculator.find_category_by_name(product_name)
        return self
    
    def with_params(self, **params):
        """Установить параметры"""
        self._params = params
        return self
    
    def with_custom_logistics(self, custom_logistics: Dict):
        """Установить кастомные параметры логистики"""
        self._custom_logistics = custom_logistics
        return self
    
    def validate(self) -> bool:
        """Валидировать перед построением"""
        self._validation_errors = []
        
        if not self._product_name:
            self._validation_errors.append("Product name is required")
        
        if self._category and self._category.needs_custom_params():
            if not self._custom_logistics:
                self._validation_errors.append("Custom logistics required for this category")
        
        return len(self._validation_errors) == 0
    
    def build(self) -> Dict[str, Any]:
        """Построить расчёт"""
        if not self.validate():
            raise ValueError(f"Validation failed: {self._validation_errors}")
        
        result = self.calculator.calculate_cost(
            **self._params,
            custom_logistics_params=self._custom_logistics,
            forced_category=self._category.name if self._category else None
        )
        
        return {
            'product_name': self._product_name,
            'category': self._category,
            'params': self._params,
            'custom_logistics': self._custom_logistics,
            'result': result,
            'is_custom': bool(self._custom_logistics)
        }

# Использование:
calculation = (CalculationBuilder(calculator)
    .with_product("Неизвестный товар")
    .with_params(quantity=100, weight_kg=0.5, unit_price_yuan=50)
    .with_custom_logistics({"highway_rail": {"custom_rate": 8.5}})
    .build())
```

---

## 📊 Сравнение решений

| Критерий | State Machine | Strategy | Event-Driven | Builder |
|----------|--------------|----------|--------------|---------|
| **Сложность реализации** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Устойчивость** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Масштабируемость** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Тестируемость** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Поддерживаемость** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Отладка** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Время внедрения** | 2-3 дня | 1-2 дня | 3-4 дня | 1 день |

---

## 🏆 РЕКОМЕНДАЦИЯ

### Гибридное решение: **State Machine + Strategy Pattern**

Комбинируем лучшее из обоих подходов:

**State Machine** - для управления жизненным циклом  
**Strategy Pattern** - для разных типов расчётов

```python
class CalculationOrchestrator:
    """Оркестратор расчётов"""
    
    def __init__(self, calculator: PriceCalculator):
        self.calculator = calculator
        self.state_machine = CalculationStateMachine()
        self.context = CalculationContext(calculator)
    
    def process_calculation(self, product_name: str, **params):
        """Основной процесс расчёта"""
        # 1. Устанавливаем товар и выбираем стратегию
        self.context.set_product(product_name, **params)
        
        # 2. Переходим в нужное состояние
        if self.context.needs_user_input():
            self.state_machine.transition_to(CalculationState.PENDING_PARAMS)
            return {
                'state': 'pending_params',
                'required_params': self.context.get_required_params()
            }
        else:
            self.state_machine.transition_to(CalculationState.READY)
        
        # 3. Выполняем расчёт
        result = self.context.calculate()
        self.state_machine.transition_to(CalculationState.CALCULATED)
        
        return {
            'state': 'calculated',
            'result': result
        }
```

### Почему это лучшее решение:

✅ **Явное управление состоянием** (State Machine)  
✅ **Гибкость расчётов** (Strategy Pattern)  
✅ **Устойчивость** - невозможны невалидные состояния  
✅ **Масштабируемость** - легко добавлять новые стратегии и состояния  
✅ **Тестируемость** - можно тестировать FSM и стратегии отдельно  
✅ **Отладка** - история переходов + логирование стратегий  
✅ **Не сломается** при добавлении новых категорий  

---

## 📝 План внедрения

### Фаза 1: Подготовка (1 день)
- [ ] Создать модели (Category, CategoryRequirements)
- [ ] Создать CalculationState enum
- [ ] Написать тесты для базовых компонентов

### Фаза 2: Бэкенд (2 дня)
- [ ] Реализовать CalculationStateMachine
- [ ] Реализовать CalculationStrategy (базовый + кастомный)
- [ ] Реализовать CalculationContext
- [ ] Реализовать CalculationOrchestrator
- [ ] Обновить API endpoints
- [ ] Написать интеграционные тесты

### Фаза 3: Фронтенд (2 дня)
- [ ] Создать composable useCalculationState
- [ ] Обновить PriceCalculatorAppV2
- [ ] Обновить RouteEditorV2 (убрать isNewCategory логику)
- [ ] Обновить HistoryPanelV2
- [ ] Добавить StateIndicator компонент

### Фаза 4: Тестирование (1 день)
- [ ] E2E тесты всех сценариев
- [ ] Нагрузочное тестирование
- [ ] Миграция существующих данных

**Общее время:** 6 рабочих дней

---

## 🎯 Итоговый вердикт

**State Machine + Strategy Pattern** - это профессиональное, enterprise-level решение, которое:

1. **Не сломается** при добавлении новых категорий
2. **Легко масштабируется** - новые стратегии = новые файлы
3. **Явное управление** - всегда понятно что происходит
4. **Тестируемо** - 100% покрытие тестами
5. **Документируемо** - диаграммы состояний + UML

Это решение используется в крупных enterprise системах (финтех, e-commerce) для управления сложными бизнес-процессами.





