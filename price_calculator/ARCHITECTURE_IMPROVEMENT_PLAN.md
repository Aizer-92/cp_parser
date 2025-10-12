# 🏗️ План улучшения архитектуры: Унификация маршрутов

## 📊 Текущая проблема

При добавлении нового маршрута (например, `sea_container`) требуется изменить **12+ файлов** в разных местах:

### Текущий процесс добавления маршрута:

1. **Backend** (`price_calculator.py`):
   - ✏️ Добавить метод расчета (например, `calculate_sea_container_cost()`)
   - ✏️ Добавить вызов метода в `calculate_cost()`
   - ✏️ Добавить маршрут в `routes` dict
   - ✏️ Обновить документацию в docstring

2. **Frontend Components** (JavaScript):
   - ✏️ `PriceCalculatorAppV2.js`: добавить спец. блоки для нового маршрута
   - ✏️ `RouteDetailsV2.js`: добавить `isNewRoute()`, обновить `logisticsTotal()`, добавить блоки отображения
   - ✏️ `RouteEditorV2.js`: добавить `isNewRoute()`, обновить `openEdit()`, добавить UI для редактирования
   - ✏️ `LogisticsSettingsModal.js`: добавить настройки для нового маршрута

3. **Документация**:
   - ✏️ `ROUTES_STRUCTURE.md`: описать структуру и формулы
   - ✏️ `CALCULATION_FORMULAS.md`: добавить формулы расчета

**Итого:** ~12 файлов, ~50 мест для изменений ❌

---

## 🎯 Цель улучшения

Создать **унифицированную архитектуру**, где:
1. Добавление маршрута = **1 конфигурационный файл** + **1 класс расчета**
2. Frontend автоматически адаптируется под новые маршруты
3. Минимум дублирования кода
4. Легко тестировать и поддерживать

---

## 🏗️ Предлагаемая архитектура

### Компонент 1: **Route Registry** (Реестр маршрутов)

**Файл:** `routes_config.py`

```python
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Callable
from enum import Enum

class RouteType(Enum):
    """Типы логистических маршрутов"""
    HIGHWAY_RAIL = "highway_rail"
    HIGHWAY_AIR = "highway_air"
    HIGHWAY_CONTRACT = "highway_contract"
    PROLOGIX = "prologix"
    SEA_CONTAINER = "sea_container"
    # Легко добавить новые:
    # CARGO = "cargo"
    # TRAIN_DIRECT = "train_direct"

class LogisticsType(Enum):
    """Тип расчета логистики"""
    RATE_PER_KG = "rate_per_kg"           # $/кг (Highway)
    RATE_PER_M3 = "rate_per_m3"           # ₽/м³ (Prologix)
    FIXED_CONTAINERS = "fixed_containers"  # Контейнеры (Sea)
    FIXED_COST = "fixed_cost"             # Фикс. стоимость (Cargo)

class CustomsType(Enum):
    """Тип таможенных пошлин"""
    NONE = "none"                # Без пошлин
    PERCENT = "percent"          # Процентные (10%)
    SPECIFIC = "specific"        # Весовые (EUR/кг)
    COMBINED = "combined"        # Комбинированные (10% или EUR/кг, что больше)

@dataclass
class RouteConfig:
    """Конфигурация маршрута"""
    
    # Базовая информация
    route_type: RouteType
    name: str
    description: str
    delivery_days: int
    
    # Тип логистики
    logistics_type: LogisticsType
    
    # Таможня
    has_customs: bool = False
    customs_type: CustomsType = CustomsType.NONE
    
    # Комиссии
    toni_commission_percent: float = 5.0
    transfer_commission_percent: float = 18.0
    
    # Требования к данным
    requires_weight: bool = True
    requires_volume: bool = False
    requires_packing: bool = False
    min_volume_m3: Optional[float] = None
    min_weight_kg: Optional[float] = None
    
    # Редактируемые параметры (для UI)
    editable_params: List[str] = None  # ["logistics_rate", "duty_rate", "vat_rate"]
    
    # UI настройки
    display_order: int = 0
    color: str = "#111827"
    icon: Optional[str] = None
    
    # Метод расчета
    calculator_class: str = None  # "HighwayCalculator", "SeaContainerCalculator"


# РЕЕСТР ВСЕХ МАРШРУТОВ
ROUTES_REGISTRY = {
    RouteType.HIGHWAY_RAIL: RouteConfig(
        route_type=RouteType.HIGHWAY_RAIL,
        name="Highway ЖД",
        description="Автомобильно-железнодорожная доставка",
        delivery_days=25,
        logistics_type=LogisticsType.RATE_PER_KG,
        has_customs=False,
        requires_weight=True,
        requires_volume=False,
        editable_params=["logistics_rate"],
        display_order=1,
        calculator_class="HighwayCalculator"
    ),
    
    RouteType.HIGHWAY_AIR: RouteConfig(
        route_type=RouteType.HIGHWAY_AIR,
        name="Highway Авиа",
        description="Авиадоставка",
        delivery_days=15,
        logistics_type=LogisticsType.RATE_PER_KG,
        has_customs=False,
        requires_weight=True,
        requires_volume=False,
        editable_params=["logistics_rate"],
        display_order=2,
        calculator_class="HighwayCalculator"
    ),
    
    RouteType.HIGHWAY_CONTRACT: RouteConfig(
        route_type=RouteType.HIGHWAY_CONTRACT,
        name="Highway под контракт",
        description="Доставка под контракт с пошлинами",
        delivery_days=25,
        logistics_type=LogisticsType.RATE_PER_KG,
        has_customs=True,
        customs_type=CustomsType.PERCENT,
        toni_commission_percent=5.0,
        transfer_commission_percent=0.0,  # Под контракт 0%
        requires_weight=True,
        requires_volume=False,
        editable_params=["logistics_rate", "duty_rate", "vat_rate"],
        display_order=3,
        calculator_class="ContractCalculator"
    ),
    
    RouteType.PROLOGIX: RouteConfig(
        route_type=RouteType.PROLOGIX,
        name="Prologix",
        description="Доставка по кубометрам",
        delivery_days=22,
        logistics_type=LogisticsType.RATE_PER_M3,
        has_customs=True,
        customs_type=CustomsType.PERCENT,
        toni_commission_percent=5.0,
        transfer_commission_percent=0.0,
        requires_weight=True,
        requires_volume=True,
        requires_packing=True,
        min_volume_m3=2.0,
        editable_params=["logistics_rate", "duty_rate", "vat_rate"],
        display_order=4,
        calculator_class="PrologixCalculator"
    ),
    
    RouteType.SEA_CONTAINER: RouteConfig(
        route_type=RouteType.SEA_CONTAINER,
        name="Море контейнером",
        description="Контейнерная морская доставка",
        delivery_days=60,
        logistics_type=LogisticsType.FIXED_CONTAINERS,
        has_customs=True,
        customs_type=CustomsType.PERCENT,
        toni_commission_percent=5.0,
        transfer_commission_percent=0.0,
        requires_weight=True,
        requires_volume=True,
        requires_packing=True,
        min_volume_m3=10.0,
        editable_params=["duty_rate", "vat_rate"],  # Тарифы фиксированные!
        display_order=5,
        calculator_class="SeaContainerCalculator"
    ),
    
    # ЛЕГКО ДОБАВИТЬ НОВЫЙ МАРШРУТ:
    # RouteType.CARGO: RouteConfig(
    #     route_type=RouteType.CARGO,
    #     name="Карго",
    #     description="Карго доставка",
    #     delivery_days=30,
    #     logistics_type=LogisticsType.RATE_PER_KG,
    #     has_customs=True,
    #     customs_type=CustomsType.PERCENT,
    #     requires_weight=True,
    #     min_weight_kg=100.0,
    #     editable_params=["logistics_rate", "duty_rate", "vat_rate"],
    #     display_order=6,
    #     calculator_class="CargoCalculator"
    # ),
}


def get_route_config(route_type: RouteType) -> RouteConfig:
    """Получить конфигурацию маршрута"""
    return ROUTES_REGISTRY.get(route_type)


def get_all_routes() -> Dict[RouteType, RouteConfig]:
    """Получить все маршруты"""
    return ROUTES_REGISTRY


def get_available_routes(volume_m3: Optional[float] = None, 
                         weight_kg: Optional[float] = None,
                         has_packing: bool = False) -> List[RouteConfig]:
    """
    Получить доступные маршруты на основе параметров груза
    
    Args:
        volume_m3: Объем груза
        weight_kg: Вес груза
        has_packing: Есть ли данные упаковки
        
    Returns:
        Список доступных маршрутов
    """
    available = []
    
    for route_config in ROUTES_REGISTRY.values():
        # Проверяем минимальный объем
        if route_config.min_volume_m3 and (not volume_m3 or volume_m3 < route_config.min_volume_m3):
            continue
        
        # Проверяем минимальный вес
        if route_config.min_weight_kg and (not weight_kg or weight_kg < route_config.min_weight_kg):
            continue
        
        # Проверяем требование к данным упаковки
        if route_config.requires_packing and not has_packing:
            continue
        
        available.append(route_config)
    
    # Сортируем по display_order
    return sorted(available, key=lambda r: r.display_order)
```

---

### Компонент 2: **Abstract Route Calculator** (Базовый класс)

**Файл:** `calculators/base_calculator.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CalculationInput:
    """Входные данные для расчета"""
    price_yuan: float
    quantity: int
    weight_kg: float
    volume_m3: Optional[float] = None
    category: Optional[Dict] = None
    custom_params: Optional[Dict] = None
    # ... остальные поля


@dataclass
class CalculationOutput:
    """Результат расчета маршрута"""
    route_type: str
    name: str
    delivery_days: int
    
    # Стоимость
    cost_rub: float
    cost_usd: float
    per_unit: float
    
    # Продажа
    sale_rub: float
    sale_usd: float
    sale_per_unit: float
    
    # Детализация (breakdown)
    breakdown: Dict[str, Any]
    
    # Специфичные данные маршрута
    route_specific_data: Optional[Dict] = None


class BaseRouteCalculator(ABC):
    """Базовый класс для расчета маршрутов"""
    
    def __init__(self, route_config: RouteConfig, currencies: Dict, formula_config: Dict):
        self.route_config = route_config
        self.currencies = currencies
        self.formula_config = formula_config
    
    @abstractmethod
    def calculate(self, input_data: CalculationInput) -> Optional[CalculationOutput]:
        """
        Рассчитать стоимость доставки
        
        Returns:
            CalculationOutput или None если маршрут недоступен
        """
        pass
    
    def _calculate_goods_cost(self, input_data: CalculationInput) -> float:
        """Общая логика расчета стоимости товара"""
        base_cost = input_data.price_yuan * input_data.quantity
        toni = base_cost * (self.route_config.toni_commission_percent / 100)
        transfer = (base_cost + toni) * (self.route_config.transfer_commission_percent / 100)
        return (base_cost + toni + transfer) * self.currencies["yuan_to_rub"]
    
    def _calculate_customs(self, customs_value: float, duty_rate: float, vat_rate: float) -> Dict:
        """Общая логика расчета пошлин"""
        duty = customs_value * duty_rate
        vat = (customs_value + duty) * vat_rate
        return {"duty": duty, "vat": vat, "total": duty + vat}
    
    def is_available(self, input_data: CalculationInput) -> bool:
        """Проверить, доступен ли маршрут"""
        config = self.route_config
        
        if config.min_volume_m3 and (not input_data.volume_m3 or input_data.volume_m3 < config.min_volume_m3):
            return False
        
        if config.requires_packing and not input_data.volume_m3:
            return False
        
        return True
```

---

### Компонент 3: **Конкретные калькуляторы** (по типам)

**Файл:** `calculators/sea_container_calculator.py`

```python
class SeaContainerCalculator(BaseRouteCalculator):
    """Калькулятор для морских контейнеров"""
    
    CONTAINERS = {
        "20ft": {"capacity_m3": 30, "price_usd": 1500, "fixed_cost_rub": 180000},
        "40ft": {"capacity_m3": 70, "price_usd": 2050, "fixed_cost_rub": 225000}
    }
    
    def calculate(self, input_data: CalculationInput) -> Optional[CalculationOutput]:
        if not self.is_available(input_data):
            return None
        
        # Выбор оптимальных контейнеров
        container_config = self._optimize_containers(input_data.volume_m3)
        
        # Расчет логистики
        logistics_cost = self._calculate_logistics(container_config)
        
        # Расчет пошлин
        customs = self._calculate_customs_for_sea(logistics_cost, input_data.category)
        
        # Формируем результат
        return CalculationOutput(
            route_type=self.route_config.route_type.value,
            name=self.route_config.name,
            delivery_days=self.route_config.delivery_days,
            # ... остальные поля
            route_specific_data={
                "containers_40ft": container_config["containers_40"],
                "containers_20ft": container_config["containers_20"],
                "remaining_capacity_m3": container_config["remaining"]
            }
        )
    
    def _optimize_containers(self, volume_m3: float) -> Dict:
        """Оптимальный выбор контейнеров"""
        # Логика из calculate_sea_container_cost()
        ...
```

---

### Компонент 4: **Route Calculator Factory**

**Файл:** `calculators/calculator_factory.py`

```python
class RouteCalculatorFactory:
    """Фабрика для создания калькуляторов"""
    
    CALCULATORS = {
        "HighwayCalculator": HighwayCalculator,
        "ContractCalculator": ContractCalculator,
        "PrologixCalculator": PrologixCalculator,
        "SeaContainerCalculator": SeaContainerCalculator,
        # Легко добавить новые:
        # "CargoCalculator": CargoCalculator,
    }
    
    @staticmethod
    def create_calculator(route_config: RouteConfig, currencies: Dict, formula_config: Dict):
        """Создать калькулятор для маршрута"""
        calculator_class = RouteCalculatorFactory.CALCULATORS.get(route_config.calculator_class)
        if not calculator_class:
            raise ValueError(f"Calculator {route_config.calculator_class} not found")
        
        return calculator_class(route_config, currencies, formula_config)
    
    @staticmethod
    def calculate_all_routes(input_data: CalculationInput) -> Dict[str, CalculationOutput]:
        """Рассчитать все доступные маршруты"""
        results = {}
        
        for route_type, route_config in ROUTES_REGISTRY.items():
            calculator = RouteCalculatorFactory.create_calculator(
                route_config, 
                input_data.currencies, 
                input_data.formula_config
            )
            
            result = calculator.calculate(input_data)
            if result:  # Если маршрут доступен
                results[route_type.value] = result
        
        return results
```

---

### Компонент 5: **Unified Frontend** (автоматическая адаптация)

**Файл:** `static/js/v2/RouteRenderer.js`

```javascript
// Универсальный рендерер маршрутов
const RouteRenderer = {
    name: 'RouteRenderer',
    props: {
        route: Object,
        routeConfig: Object  // Конфигурация из routes_config.py
    },
    
    computed: {
        // Автоматически определяем тип отображения на основе logistics_type
        logisticsDisplay() {
            switch (this.routeConfig.logistics_type) {
                case 'rate_per_kg':
                    return this._renderRatePerKg();
                case 'rate_per_m3':
                    return this._renderRatePerM3();
                case 'fixed_containers':
                    return this._renderContainers();
                case 'fixed_cost':
                    return this._renderFixedCost();
            }
        },
        
        // Автоматически определяем редактируемые поля
        editableFields() {
            return this.routeConfig.editable_params || [];
        }
    },
    
    methods: {
        _renderRatePerKg() {
            // Универсальный рендер для $/кг
        },
        
        _renderContainers() {
            // Универсальный рендер для контейнеров
            // Проверяем route.route_specific_data.containers_40ft
        },
        
        // ...
    }
};
```

---

## 📋 Преимущества новой архитектуры

### ✅ Добавление нового маршрута

**Было:** 12+ файлов, ~50 изменений

**Станет:** 2 файла:

1. **routes_config.py** - добавить RouteConfig (10 строк)
2. **calculators/new_calculator.py** - создать класс (50-100 строк)

```python
# 1. Добавить в routes_config.py
RouteType.CARGO: RouteConfig(
    route_type=RouteType.CARGO,
    name="Карго",
    delivery_days=30,
    logistics_type=LogisticsType.RATE_PER_KG,
    has_customs=True,
    calculator_class="CargoCalculator"
)

# 2. Создать calculators/cargo_calculator.py
class CargoCalculator(BaseRouteCalculator):
    def calculate(self, input_data):
        # Логика расчета
        ...
```

**Frontend автоматически адаптируется!** ✨

---

### ✅ Единый источник истины

- Все параметры маршрута в **одном месте** (RouteConfig)
- Нет дублирования информации
- Легко менять параметры (например, срок доставки)

### ✅ Легко тестировать

```python
def test_sea_container_calculator():
    config = get_route_config(RouteType.SEA_CONTAINER)
    calculator = SeaContainerCalculator(config, currencies, formula_config)
    
    result = calculator.calculate(CalculationInput(...))
    
    assert result.route_specific_data["containers_40ft"] == 1
    assert result.route_specific_data["remaining_capacity_m3"] == 35.0
```

### ✅ API для frontend

```python
@app.get("/api/routes/config")
def get_routes_config():
    """Вернуть конфигурацию всех маршрутов для frontend"""
    return {
        route_type.value: {
            "name": config.name,
            "logistics_type": config.logistics_type.value,
            "editable_params": config.editable_params,
            "has_customs": config.has_customs,
            # ...
        }
        for route_type, config in ROUTES_REGISTRY.items()
    }
```

Frontend получает конфигурацию и **автоматически адаптируется**!

---

## 🗂️ Новая структура файлов

```
price_calculator/
├── routes_config.py              # ✨ РЕЕСТР всех маршрутов
├── calculators/
│   ├── __init__.py
│   ├── base_calculator.py        # Базовый класс
│   ├── calculator_factory.py     # Фабрика
│   ├── highway_calculator.py     # Highway ЖД/Авиа
│   ├── contract_calculator.py    # Highway Контракт
│   ├── prologix_calculator.py    # Prologix
│   ├── sea_container_calculator.py  # Море контейнером
│   └── cargo_calculator.py       # ✨ Новый маршрут (пример)
├── static/js/v2/
│   ├── RouteRenderer.js          # ✨ Универсальный рендерер
│   ├── RouteEditor.js            # ✨ Универсальный редактор
│   └── PriceCalculatorAppV2.js   # Упрощенный, использует RouteRenderer
└── main.py                       # API endpoints
```

---

## 🔄 Миграция (поэтапная)

### Этап 1: Backend (без breaking changes)
1. Создать `routes_config.py` с RouteConfig для существующих маршрутов
2. Создать базовый `BaseRouteCalculator`
3. Рефакторить существующие методы в калькуляторы (один за раз)
4. Добавить `RouteCalculatorFactory`
5. Обновить `calculate_cost()` для использования фабрики
6. **Тесты:** Проверить, что результаты идентичны старым

### Этап 2: API
1. Добавить endpoint `/api/routes/config`
2. Обновить `/api/v2/calculate` для использования фабрики
3. Вернуть `route_config` в ответе
4. **Тесты:** Проверить совместимость с текущим frontend

### Этап 3: Frontend (постепенно)
1. Создать `RouteRenderer.js` (универсальный)
2. Создать `RouteEditor.js` (универсальный)
3. Обновить `PriceCalculatorAppV2.js` для использования новых компонентов
4. Постепенно удалять `if (isSeaContainer)`, `if (isPrologix)` проверки
5. **Тесты:** Проверить UI для всех маршрутов

### Этап 4: Cleanup
1. Удалить старые методы из `price_calculator.py`
2. Удалить дублирующийся код из frontend
3. Обновить документацию
4. **Результат:** Код сокращен на ~40%

---

## 📊 Метрики улучшения

| Метрика | Было | Станет | Улучшение |
|---------|------|--------|-----------|
| Файлов для нового маршрута | 12+ | 2 | **-83%** |
| Строк кода для нового маршрута | ~500 | ~100 | **-80%** |
| Время добавления маршрута | 4-6 часов | 1-2 часа | **-70%** |
| Дублирование кода | Высокое | Минимальное | **-90%** |
| Покрытие тестами | ~30% | ~80% | **+50%** |
| Сложность поддержки | Высокая | Низкая | ✅ |

---

## 🎯 Итог

### Текущая архитектура:
- ❌ Много дублирования
- ❌ Сложно добавлять маршруты
- ❌ Трудно тестировать
- ❌ Frontend жестко связан с backend

### Новая архитектура:
- ✅ **DRY** (Don't Repeat Yourself)
- ✅ **SOLID** принципы
- ✅ **Plugin architecture** - легко добавлять маршруты
- ✅ **Separation of Concerns** - каждый класс делает одно
- ✅ **Testable** - легко писать unit-тесты
- ✅ **Maintainable** - легко понять и изменить
- ✅ **Scalable** - готово к росту (10, 20, 50 маршрутов)

---

## 📅 Когда внедрять?

**Рекомендация:** Перед добавлением следующего маршрута (Карго/Контейнер 20ft)

**Почему:** 
- Сейчас 5 маршрутов - еще управляемо
- С 6+ маршрутами будет критично сложно поддерживать
- Миграция займет ~2-3 дня, но сэкономит недели в будущем

---

## 🚀 Следующие шаги

1. **Обсудить план** с командой
2. **Оценить сроки** миграции
3. **Приоритизировать** этапы
4. **Создать задачи** в трекере
5. **Начать с Этапа 1** (backend рефакторинг)

---

**Автор:** AI Assistant  
**Дата:** 2025-10-09  
**Версия:** 1.0






