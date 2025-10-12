# 🚀 ПЛАН РЕФАКТОРИНГА V2.0 (с "Новой категорией" и кастомными параметрами)

**Дата создания:** 10.10.2025  
**Статус:** К реализации  
**Цель:** Устранить технический долг, упростить добавление новых маршрутов, улучшить работу "Новой категории"

---

## 🎯 ГЛАВНЫЕ ПРОБЛЕМЫ (расширенный список)

### 1. **КРИТИЧЕСКАЯ: Кастомные параметры НЕ сохраняются в БД**

**Текущее состояние:**
```python
# В БД сохраняется только ONE custom_rate (legacy поле для Highway)
custom_rate REAL  # Только для обратной совместимости

# НО пользователь может редактировать ДЛЯ КАЖДОГО МАРШРУТА:
custom_logistics = {
    "highway_rail": {"custom_rate": 4, "duty_rate": 10, "vat_rate": 20},
    "prologix": {"custom_rate": 25000, "duty_rate": 10, "vat_rate": 20},
    "sea_container": {"duty_rate": 15, "vat_rate": 20}
}

# И forced_category тоже НЕ сохраняется!
forced_category = "Новая категория"
```

**Последствия:**
- ❌ При открытии расчета из истории кастомные параметры ТЕРЯЮТСЯ
- ❌ Невозможно воспроизвести расчёт с "Новой категорией"
- ❌ Пользователь думает что данные сохранены, но они пропадают после перезагрузки страницы

---

### 2. **КРИТИЧЕСКАЯ: "Новая категория" работает только в рамках одной сессии**

**Проблема:**
```
1. Пользователь: Товар "XYZ" → "Новая категория" → Ввод ставок → Рассчитал
2. Сохранено в БД: category="Новая категория", но БЕЗ кастомных ставок
3. Пользователь: Обновил страницу → Открыл расчет из истории
4. Результат: Загружается с rail_base=0, custom_logistics=null → Цифры НЕПРАВИЛЬНЫЕ
```

**Текущий костыль:**
- Frontend хранит `customLogistics` в памяти
- При обновлении страницы → память очищается → данные теряются

---

### 3. **ВЫСОКАЯ: Дублирование логики вызова `calculate_cost()`**

(Уже описано в предыдущем анализе - остаётся актуальным)

---

### 4. **СРЕДНЯЯ: Нет версионирования расчётов**

**Проблема:**
```
1. Пользователь создал расчёт #238 с определёнными параметрами
2. Отредактировал → PUT /calculation/238 → Запись ПЕРЕЗАПИСАНА
3. Нет истории изменений → нельзя откатить к предыдущей версии
```

---

## 💡 РЕШЕНИЯ

### Этап 0: ФУНДАМЕНТ - Структура БД и модели данных (2-3 дня)

#### 0.1 **Добавить поля в БД для кастомных параметров**

**SQL миграция:**
```sql
-- Добавляем JSONB поле для хранения всех кастомных параметров
ALTER TABLE calculations 
ADD COLUMN custom_logistics JSONB DEFAULT NULL;

-- Добавляем принудительную категорию
ALTER TABLE calculations 
ADD COLUMN forced_category TEXT DEFAULT NULL;

-- Индекс для быстрого поиска по категории
CREATE INDEX idx_calculations_forced_category 
ON calculations(forced_category);

-- Опционально: таблица версий для истории изменений
CREATE TABLE calculation_versions (
    id SERIAL PRIMARY KEY,
    calculation_id INTEGER NOT NULL REFERENCES calculations(id),
    version INTEGER NOT NULL,
    custom_logistics JSONB,
    forced_category TEXT,
    cost_price_rub REAL,
    cost_price_usd REAL,
    sale_price_rub REAL,
    sale_price_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(calculation_id, version)
);
```

**Обновление моделей Pydantic:**
```python
# models/calculation.py
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Dict, Literal
from datetime import datetime

class CustomLogisticsParams(BaseModel):
    """Параметры кастомизации маршрута"""
    custom_rate: Optional[float] = Field(None, ge=0, description="Кастомная логистическая ставка")
    duty_rate: Optional[float] = Field(None, ge=0, le=100, description="Пошлина (%)")
    vat_rate: Optional[float] = Field(None, ge=0, le=100, description="НДС (%)")
    duty_type: Literal["percent", "specific", "combined"] = "percent"
    specific_rate: Optional[float] = Field(None, ge=0, description="Весовая пошлина (EUR/кг)")
    
    @root_validator
    def validate_duty_consistency(cls, values):
        """Проверка совместимости duty_type и specific_rate"""
        duty_type = values.get('duty_type')
        specific_rate = values.get('specific_rate')
        
        if duty_type in ['specific', 'combined'] and specific_rate is None:
            raise ValueError(f"Для duty_type={duty_type} обязателен specific_rate")
        
        return values


class RouteKeys:
    """Константы для ключей маршрутов"""
    HIGHWAY_RAIL = "highway_rail"
    HIGHWAY_AIR = "highway_air"
    HIGHWAY_CONTRACT = "highway_contract"
    PROLOGIX = "prologix"
    SEA_CONTAINER = "sea_container"
    
    @classmethod
    def all(cls) -> List[str]:
        return [
            cls.HIGHWAY_RAIL,
            cls.HIGHWAY_AIR,
            cls.HIGHWAY_CONTRACT,
            cls.PROLOGIX,
            cls.SEA_CONTAINER
        ]
    
    @classmethod
    def validate(cls, route_key: str) -> bool:
        """Проверка что ключ маршрута валидный"""
        return route_key in cls.all()


class CalculationRequest(BaseModel):
    """Запрос на расчёт (с валидацией)"""
    product_name: str = Field(..., min_length=1, max_length=500)
    price_yuan: float = Field(..., gt=0)
    weight_kg: Optional[float] = Field(None, gt=0)
    quantity: int = Field(..., gt=0)
    markup: float = Field(1.7, gt=1.0)
    
    # Packing (для точных расчётов)
    packing_units_per_box: Optional[int] = Field(None, gt=0)
    packing_box_weight: Optional[float] = Field(None, gt=0)
    packing_box_length: Optional[float] = Field(None, gt=0)
    packing_box_width: Optional[float] = Field(None, gt=0)
    packing_box_height: Optional[float] = Field(None, gt=0)
    
    # Кастомизация (с валидацией ключей маршрутов)
    custom_logistics: Optional[Dict[str, CustomLogisticsParams]] = None
    forced_category: Optional[str] = None
    
    # Legacy поля
    product_url: Optional[str] = ""
    custom_rate: Optional[float] = None  # Deprecated, используем custom_logistics
    delivery_type: str = "rail"  # Deprecated
    
    @validator('custom_logistics')
    def validate_route_keys(cls, v):
        """Проверка что все ключи маршрутов валидные"""
        if v is None:
            return v
        
        invalid_keys = [k for k in v.keys() if not RouteKeys.validate(k)]
        if invalid_keys:
            raise ValueError(f"Неизвестные маршруты: {invalid_keys}. Допустимые: {RouteKeys.all()}")
        
        return v
    
    @root_validator
    def validate_weight_source(cls, values):
        """Проверка что есть хотя бы один источник веса"""
        weight = values.get('weight_kg')
        packing_weight = values.get('packing_box_weight')
        packing_units = values.get('packing_units_per_box')
        
        has_weight = weight is not None and weight > 0
        has_packing = all([packing_weight, packing_units])
        
        if not has_weight and not has_packing:
            raise ValueError(
                "Требуется либо weight_kg, либо (packing_box_weight + packing_units_per_box)"
            )
        
        return values


class CalculationResponse(BaseModel):
    """Ответ с результатами расчёта"""
    id: Optional[int] = None
    product_name: str
    category: str
    forced_category: Optional[str] = None  # Новое поле
    custom_logistics: Optional[Dict[str, CustomLogisticsParams]] = None  # Новое поле
    
    # ... остальные поля
    
    routes: Dict[str, Dict]  # Все маршруты
    
    # Метаданные
    created_at: Optional[datetime] = None
    version: Optional[int] = 1  # Для версионирования


class CalculationVersion(BaseModel):
    """Версия расчёта (для истории изменений)"""
    id: int
    calculation_id: int
    version: int
    custom_logistics: Optional[Dict[str, CustomLogisticsParams]]
    forced_category: Optional[str]
    cost_price_rub: float
    created_at: datetime
```

---

### Этап 1: КРИТИЧЕСКОЕ - Сохранение кастомных параметров (1 день)

#### 1.1 **Обновить `save_calculation()` и `update_calculation()`**

**database.py:**
```python
def save_calculation(data: dict) -> int:
    """Сохранение расчета с кастомными параметрами"""
    conn, db_type = get_database_connection()
    cursor = conn.cursor()
    
    # Сериализуем custom_logistics в JSON
    custom_logistics_json = None
    if data.get('custom_logistics'):
        import json
        custom_logistics_json = json.dumps(data['custom_logistics'])
    
    if db_type == 'postgres':
        cursor.execute('''
            INSERT INTO calculations 
            (product_name, category, forced_category, custom_logistics,
             price_yuan, weight_kg, quantity, markup, custom_rate, 
             product_url, cost_price_rub, cost_price_usd, 
             sale_price_rub, sale_price_usd, profit_rub, profit_usd,
             ...) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ...) 
            RETURNING id
        ''', (
            data['product_name'],
            data['category'],
            data.get('forced_category'),  # НОВОЕ
            custom_logistics_json,         # НОВОЕ
            data['price_yuan'],
            # ... остальные поля
        ))
    
    # ... аналогично для SQLite
```

#### 1.2 **Обновить `_calculate_price_logic` и `_update_calculation_logic`**

**main.py:**
```python
async def _calculate_price_logic(request: CalculationRequest):
    """Общая логика расчета (с сохранением кастомных параметров)"""
    # ... расчёт ...
    
    # Подготовка данных для сохранения
    calculation_data = {
        'product_name': request.product_name,
        'category': result.get('category', 'Не определена'),
        'forced_category': request.forced_category,  # НОВОЕ
        'custom_logistics': request.custom_logistics.dict() if request.custom_logistics else None,  # НОВОЕ
        'price_yuan': request.price_yuan,
        # ... остальные поля
    }
    
    calculation_id = save_calculation(calculation_data)
    result['id'] = calculation_id
    result['forced_category'] = request.forced_category  # Добавляем в ответ
    result['custom_logistics'] = request.custom_logistics  # Добавляем в ответ
    
    return result
```

#### 1.3 **Обновить `get_calculation()` для загрузки параметров**

**main.py:**
```python
@app.get("/api/v2/calculation/{calculation_id}")
async def get_calculation_v2(calculation_id: int):
    """Загрузка расчёта со ВСЕМИ кастомными параметрами"""
    try:
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, product_name, category, forced_category, custom_logistics,
                   price_yuan, weight_kg, quantity, markup, 
                   cost_price_rub, cost_price_usd, sale_price_rub, sale_price_usd,
                   created_at
            FROM calculations 
            WHERE id = %s
        ''', (calculation_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Расчет не найден")
        
        # Парсим custom_logistics из JSON
        custom_logistics = None
        if row['custom_logistics']:
            import json
            custom_logistics = json.loads(row['custom_logistics'])
        
        return {
            "id": row['id'],
            "product_name": row['product_name'],
            "category": row['category'],
            "forced_category": row['forced_category'],  # НОВОЕ
            "custom_logistics": custom_logistics,        # НОВОЕ
            # ... остальные поля
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 1.4 **Обновить Frontend для восстановления параметров**

**static/js/v2/PriceCalculatorAppV2.js:**
```javascript
async loadCalculationById(calculationId) {
    try {
        const response = await axios.get(`/api/v2/calculation/${calculationId}`);
        const data = response.data;
        
        // Восстанавливаем productData
        this.productData = {
            calculation_id: data.id,
            name: data.product_name,
            price_yuan: data.price_yuan,
            quantity: data.quantity,
            weight_kg: data.weight_kg,
            markup: data.markup,
            forcedCategory: data.forced_category || null,  // НОВОЕ
            // ... остальные поля
        };
        
        // ВАЖНО: Восстанавливаем кастомные параметры логистики
        if (data.custom_logistics) {
            this.customLogistics = data.custom_logistics;
            console.log('✅ Восстановлены кастомные параметры:', this.customLogistics);
        }
        
        // Если есть forced_category - устанавливаем как выбранную
        if (data.forced_category) {
            console.log('✅ Восстановлена принудительная категория:', data.forced_category);
        }
        
        // Пересчитываем с восстановленными параметрами
        await this.performCalculation();
        
        // Переходим на Этап 2
        this.currentStep = 2;
        this.calculationResult = response.data.routes;
        
        console.log('✅ Расчёт загружен полностью с кастомными параметрами');
    } catch (error) {
        console.error('❌ Ошибка загрузки расчёта:', error);
        alert('Не удалось загрузить расчёт');
    }
}
```

---

### Этап 2: КРИТИЧЕСКОЕ - Helper для унификации вызовов (1 день)

#### 2.1 **Создать `_build_calculation_params()` helper**

**main.py:**
```python
def _build_calculation_params(
    request: CalculationRequest, 
    calculated_weight: Optional[float] = None
) -> dict:
    """
    Формирует параметры для calculate_cost из request.
    Единый источник истины для параметров расчёта.
    
    Args:
        request: Запрос с данными
        calculated_weight: Вес (если уже вычислен из packing)
    
    Returns:
        dict: Параметры для **kwargs в calculate_cost()
    """
    weight_kg = calculated_weight if calculated_weight is not None else request.weight_kg
    
    return {
        "product_name": request.product_name,
        "price_yuan": request.price_yuan,
        "weight_kg": weight_kg,
        "quantity": request.quantity,
        "custom_rate": request.custom_rate,  # Legacy
        "delivery_type": request.delivery_type,  # Legacy
        "markup": request.markup,
        "product_url": request.product_url,
        # Packing
        "packing_units_per_box": request.packing_units_per_box,
        "packing_box_weight": request.packing_box_weight,
        "packing_box_length": request.packing_box_length,
        "packing_box_width": request.packing_box_width,
        "packing_box_height": request.packing_box_height,
        # Кастомизация
        "custom_logistics_params": request.custom_logistics.dict() if request.custom_logistics else None,
        "forced_category": request.forced_category
    }


async def _calculate_price_logic(request: CalculationRequest):
    """Общая логика расчета (упрощённая)"""
    # Вычисляем вес из packing если нужно
    calculated_weight_kg = _calculate_weight_from_packing(request)
    
    # Получаем параметры через helper
    calc_params = _build_calculation_params(request, calculated_weight_kg)
    
    # Вызываем расчёт
    calc = get_calculator()
    result = calc.calculate_cost(**calc_params)
    
    # ... сохранение в БД ...
    
    return result


async def _update_calculation_logic(calculation_id: int, request: CalculationRequest):
    """Общая логика обновления (упрощённая)"""
    # Получаем параметры через ТОТ ЖЕ helper
    calc_params = _build_calculation_params(request, request.weight_kg)
    
    # Вызываем расчёт
    calculator = PriceCalculator()
    result = calculator.calculate_cost(**calc_params)
    
    # ... обновление в БД ...
    
    return result
```

**Выгода:**
- ✅ Новые поля добавляются в ОДНОМ месте
- ✅ Невозможно забыть параметр при добавлении нового endpoint
- ✅ Меньше риска ошибок

---

### Этап 3: ВЫСОКИЙ - Извлечение базовых компонентов (2 дня)

#### 3.1 **Создать `cost_components.py`**

**models/cost_components.py:**
```python
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class CostComponentResult:
    """Результат расчёта компонента стоимости"""
    total_rub: float
    per_unit_rub: float
    details: Dict  # Детализация для breakdown


class CostComponents:
    """Базовые компоненты стоимости (общие для всех маршрутов)"""
    
    def __init__(self, currencies: dict, formula_config: dict):
        self.currencies = currencies
        self.formula_config = formula_config
    
    def calculate_goods_cost(
        self, 
        price_yuan: float, 
        quantity: int,
        include_toni: bool = True,
        include_transfer: bool = False
    ) -> CostComponentResult:
        """
        Стоимость товара с комиссиями.
        
        Args:
            price_yuan: Цена за единицу в юанях
            quantity: Количество единиц
            include_toni: Включать ли комиссию Тони (5%)
            include_transfer: Включать ли комиссию за перевод (18%)
        
        Returns:
            CostComponentResult с детализацией
        """
        base_rub = price_yuan * self.currencies["yuan_to_rub"]
        
        toni_commission = base_rub * 0.05 if include_toni else 0
        
        if include_transfer:
            transfer_commission = (base_rub + toni_commission) * 0.18
        else:
            transfer_commission = 0
        
        total_per_unit = base_rub + toni_commission + transfer_commission
        
        return CostComponentResult(
            total_rub=total_per_unit * quantity,
            per_unit_rub=total_per_unit,
            details={
                "base_rub": base_rub,
                "toni_commission_rub": toni_commission,
                "transfer_commission_rub": transfer_commission,
                "toni_commission_pct": 5.0 if include_toni else 0,
                "transfer_commission_pct": 18.0 if include_transfer else 0
            }
        )
    
    def calculate_local_delivery(
        self, 
        weight_kg: float, 
        quantity: int
    ) -> CostComponentResult:
        """Локальная доставка в Китае (2¥/кг)"""
        rate = self.formula_config.local_delivery_rate_yuan_per_kg or 2.0
        per_unit_yuan = rate * weight_kg
        per_unit_rub = per_unit_yuan * self.currencies["yuan_to_rub"]
        
        return CostComponentResult(
            total_rub=per_unit_rub * quantity,
            per_unit_rub=per_unit_rub,
            details={
                "rate_yuan_per_kg": rate,
                "per_unit_yuan": per_unit_yuan,
                "total_yuan": per_unit_yuan * quantity
            }
        )
    
    def calculate_msk_pickup(self, quantity: int) -> CostComponentResult:
        """Забор в МСК (фиксированная сумма)"""
        total = self.formula_config.msk_pickup_total_rub or 1000
        return CostComponentResult(
            total_rub=total,
            per_unit_rub=total / quantity,
            details={"fixed_cost_rub": total}
        )
    
    def calculate_other_costs(
        self, 
        base_cost_rub: float, 
        quantity: int
    ) -> CostComponentResult:
        """Прочие расходы (2.5% от базовой стоимости)"""
        percent = self.formula_config.other_costs_percent or 2.5
        total = base_cost_rub * (percent / 100)
        return CostComponentResult(
            total_rub=total,
            per_unit_rub=total / quantity,
            details={"percent": percent}
        )
```

---

### Этап 4: ВЫСОКИЙ - Рефакторинг маршрутов (3-4 дня)

#### 4.1 **Создать базовый класс `BaseRoute`**

**models/routes/base_route.py:**
```python
from abc import ABC, abstractmethod
from typing import Dict, Optional
from ..cost_components import CostComponents, CostComponentResult

class BaseRoute(ABC):
    """Базовый класс для всех логистических маршрутов"""
    
    def __init__(
        self, 
        route_key: str, 
        route_name: str, 
        delivery_days: int,
        cost_components: CostComponents
    ):
        self.route_key = route_key
        self.route_name = route_name
        self.delivery_days = delivery_days
        self.components = cost_components
    
    @abstractmethod
    def calculate_logistics(
        self, 
        **kwargs
    ) -> CostComponentResult:
        """
        Расчёт логистики (специфичный для каждого маршрута).
        Должен быть реализован в подклассах.
        """
        pass
    
    @abstractmethod
    def requires_customs(self) -> bool:
        """Требуется ли расчёт пошлин и НДС для этого маршрута"""
        pass
    
    def calculate(
        self,
        price_yuan: float,
        weight_kg: float,
        quantity: int,
        markup: float,
        category: Optional[Dict] = None,
        custom_params: Optional[Dict] = None,
        **logistics_kwargs
    ) -> Dict:
        """
        Общий расчёт маршрута (единая логика для ВСЕХ маршрутов).
        
        Returns:
            {
                "name": str,
                "delivery_days": int,
                "cost_rub": float,
                "cost_usd": float,
                "per_unit": float,
                "sale_rub": float,
                "sale_usd": float,
                "sale_per_unit": float,
                "breakdown": {...}
            }
        """
        # 1. Стоимость товара (с учётом специфики маршрута)
        goods_cost = self.components.calculate_goods_cost(
            price_yuan=price_yuan,
            quantity=quantity,
            include_toni=True,
            include_transfer=self._needs_transfer_commission()
        )
        
        # 2. Локальная доставка (одинаково для всех)
        local_delivery = self.components.calculate_local_delivery(
            weight_kg=weight_kg,
            quantity=quantity
        )
        
        # 3. Логистика (специфична для маршрута)
        logistics = self.calculate_logistics(
            weight_kg=weight_kg,
            quantity=quantity,
            custom_params=custom_params,
            **logistics_kwargs
        )
        
        # 4. Пошлины + НДС (если нужны)
        customs_cost = None
        if self.requires_customs() and category:
            customs_cost = self._calculate_customs(
                goods_cost=goods_cost,
                logistics_cost=logistics,
                local_delivery=local_delivery,
                category=category,
                weight_kg=weight_kg,
                quantity=quantity,
                custom_params=custom_params
            )
        
        # 5. Забор МСК
        msk_pickup = self.components.calculate_msk_pickup(quantity)
        
        # 6. Прочие расходы (от базовой стоимости)
        base_for_other_costs = (
            goods_cost.total_rub + 
            local_delivery.total_rub
        )
        other_costs = self.components.calculate_other_costs(
            base_cost_rub=base_for_other_costs,
            quantity=quantity
        )
        
        # 7. Итоговая стоимость
        total_cost_rub = (
            goods_cost.total_rub +
            logistics.total_rub +
            local_delivery.total_rub +
            msk_pickup.total_rub +
            other_costs.total_rub
        )
        
        if customs_cost:
            total_cost_rub += customs_cost.total_rub
        
        cost_per_unit = total_cost_rub / quantity
        total_cost_usd = total_cost_rub / self.components.currencies["usd_to_rub"]
        
        # 8. Формируем результат
        return {
            "name": self.route_name,
            "delivery_days": self.delivery_days,
            "cost_rub": round(total_cost_rub, 2),
            "cost_usd": round(total_cost_usd, 2),
            "per_unit": round(cost_per_unit, 2),
            "sale_rub": round(total_cost_rub * markup, 2),
            "sale_usd": round(total_cost_usd * markup, 2),
            "sale_per_unit": round(cost_per_unit * markup, 2),
            "breakdown": self._build_breakdown(
                goods_cost, logistics, local_delivery, 
                msk_pickup, other_costs, customs_cost
            )
        }
    
    def _needs_transfer_commission(self) -> bool:
        """Нужна ли комиссия за перевод (18%) для этого маршрута"""
        # По умолчанию нет, переопределяется в Highway ЖД/Авиа
        return False
    
    def _build_breakdown(
        self, 
        goods: CostComponentResult,
        logistics: CostComponentResult,
        local_delivery: CostComponentResult,
        msk_pickup: CostComponentResult,
        other_costs: CostComponentResult,
        customs: Optional[CostComponentResult]
    ) -> Dict:
        """Формирует детализацию затрат"""
        breakdown = {
            "goods": goods.details,
            "logistics": logistics.details,
            "local_delivery": local_delivery.details,
            "msk_pickup": msk_pickup.details,
            "other_costs": other_costs.details
        }
        
        if customs:
            breakdown["customs"] = customs.details
        
        return breakdown
    
    def _calculate_customs(
        self,
        goods_cost: CostComponentResult,
        logistics_cost: CostComponentResult,
        local_delivery: CostComponentResult,
        category: Dict,
        weight_kg: float,
        quantity: int,
        custom_params: Optional[Dict] = None
    ) -> CostComponentResult:
        """Расчёт пошлин и НДС (общая логика)"""
        # Таможенная стоимость
        customs_value_rub = (
            goods_cost.total_rub +
            logistics_cost.total_rub +
            local_delivery.total_rub
        )
        
        # Получаем ставки пошлин (с учётом кастомных параметров)
        duty_rate, vat_rate, duty_type, specific_rate = self._get_duty_rates(
            category, custom_params
        )
        
        # Расчёт пошлин (с поддержкой весовых)
        if duty_type == "specific":
            # Только весовые
            duty_rub = self._calculate_specific_duty(
                specific_rate, weight_kg, quantity
            )
        elif duty_type == "combined":
            # Процентные ИЛИ весовые (что больше)
            ad_valorem = customs_value_rub * duty_rate
            specific = self._calculate_specific_duty(
                specific_rate, weight_kg, quantity
            )
            duty_rub = max(ad_valorem, specific)
        else:
            # Только процентные
            duty_rub = customs_value_rub * duty_rate
        
        # НДС
        vat_rub = (customs_value_rub + duty_rub) * vat_rate
        
        return CostComponentResult(
            total_rub=duty_rub + vat_rub,
            per_unit_rub=(duty_rub + vat_rub) / quantity,
            details={
                "duty_rate": duty_rate,
                "vat_rate": vat_rate,
                "duty_type": duty_type,
                "specific_rate": specific_rate,
                "duty_rub": duty_rub,
                "vat_rub": vat_rub,
                "customs_value_rub": customs_value_rub
            }
        )
```

#### 4.2 **Реализация конкретных маршрутов**

**models/routes/highway_rail.py:**
```python
from .base_route import BaseRoute
from ..cost_components import CostComponentResult

class HighwayRailRoute(BaseRoute):
    """Highway ЖД - с комиссией за перевод (18%)"""
    
    def __init__(self, cost_components):
        super().__init__(
            route_key="highway_rail",
            route_name="Highway ЖД",
            delivery_days=25,
            cost_components=cost_components
        )
    
    def _needs_transfer_commission(self) -> bool:
        """Highway ЖД использует комиссию за перевод"""
        return True
    
    def requires_customs(self) -> bool:
        """Highway ЖД не требует пошлин/НДС"""
        return False
    
    def calculate_logistics(
        self, 
        weight_kg: float,
        quantity: int,
        base_rate: float,
        density_surcharge: float = 0,
        custom_params: Optional[Dict] = None,
        **kwargs
    ) -> CostComponentResult:
        """Логистика Highway ЖД ($/кг с надбавкой за плотность)"""
        # Применяем кастомную ставку если есть
        if custom_params and custom_params.get('custom_rate') is not None:
            base_rate = custom_params['custom_rate']
        
        total_rate_usd = base_rate + density_surcharge
        cost_per_unit_usd = weight_kg * total_rate_usd
        cost_per_unit_rub = cost_per_unit_usd * self.components.currencies["usd_to_rub"]
        
        return CostComponentResult(
            total_rub=cost_per_unit_rub * quantity,
            per_unit_rub=cost_per_unit_rub,
            details={
                "rate_usd_per_kg": total_rate_usd,
                "base_rate_usd": base_rate,
                "density_surcharge_usd": density_surcharge,
                "weight_kg": weight_kg
            }
        )
```

**models/routes/prologix.py:**
```python
class PrologixRoute(BaseRoute):
    """Prologix - расчёт по кубометрам с пошлинами"""
    
    def __init__(self, cost_components, prologix_rates):
        super().__init__(
            route_key="prologix",
            route_name="Prologix",
            delivery_days=30,
            cost_components=cost_components
        )
        self.rates = prologix_rates
    
    def requires_customs(self) -> bool:
        """Prologix требует пошлин/НДС"""
        return True
    
    def calculate_logistics(
        self, 
        volume_m3: float,
        quantity: int,
        custom_params: Optional[Dict] = None,
        **kwargs
    ) -> CostComponentResult:
        """Логистика Prologix (руб/м³)"""
        # Находим тариф по объёму
        rate_rub_per_m3 = self._get_rate_for_volume(volume_m3)
        
        # Применяем кастомную ставку если есть
        if custom_params and custom_params.get('custom_rate') is not None:
            rate_rub_per_m3 = custom_params['custom_rate']
        
        total_rub = volume_m3 * rate_rub_per_m3
        
        return CostComponentResult(
            total_rub=total_rub,
            per_unit_rub=total_rub / quantity,
            details={
                "rate_rub_per_m3": rate_rub_per_m3,
                "volume_m3": volume_m3
            }
        )
    
    def _get_rate_for_volume(self, volume_m3: float) -> float:
        """Находит тариф по объёму из конфигурации"""
        for tariff in self.rates["tariffs"]:
            if tariff["volume_min"] <= volume_m3 <= tariff["volume_max"]:
                return tariff["rate_rub_per_m3"]
        
        # Fallback
        return self.rates["tariffs"][-1]["rate_rub_per_m3"]
```

---

### Этап 5: СРЕДНИЙ - Версионирование расчётов (опционально, 1-2 дня)

#### 5.1 **Сохранение версий при обновлении**

```python
def update_calculation(calculation_id: int, data: dict) -> int:
    """Обновление расчёта с сохранением версии"""
    conn, db_type = get_database_connection()
    cursor = conn.cursor()
    
    # 1. Получаем текущую версию
    cursor.execute("SELECT version FROM calculations WHERE id = %s", (calculation_id,))
    current_version = cursor.fetchone()['version'] or 1
    next_version = current_version + 1
    
    # 2. Сохраняем текущую версию в историю
    cursor.execute('''
        INSERT INTO calculation_versions 
        (calculation_id, version, custom_logistics, forced_category, 
         cost_price_rub, cost_price_usd, sale_price_rub, sale_price_usd)
        SELECT id, version, custom_logistics, forced_category,
               cost_price_rub, cost_price_usd, sale_price_rub, sale_price_usd
        FROM calculations WHERE id = %s
    ''', (calculation_id,))
    
    # 3. Обновляем основную запись с новой версией
    cursor.execute('''
        UPDATE calculations 
        SET ..., version = %s
        WHERE id = %s
    ''', (..., next_version, calculation_id))
    
    conn.commit()
    return calculation_id
```

---

## 📋 ПОРЯДОК РЕАЛИЗАЦИИ

### ✅ Приоритет 1: КРИТИЧЕСКОЕ (первая неделя)

1. **День 1-2: Этап 0.1** - Миграция БД + модели Pydantic
   - SQL миграция (custom_logistics, forced_category)
   - Обновить модели (CalculationRequest, CalculationResponse)
   - Добавить валидацию

2. **День 3: Этап 1** - Сохранение/загрузка кастомных параметров
   - Обновить save_calculation()
   - Обновить get_calculation()
   - Обновить frontend loadCalculationById()

3. **День 4: Этап 2** - Helper для унификации
   - Создать _build_calculation_params()
   - Рефакторинг всех вызовов calculate_cost()

4. **День 5: Тестирование**
   - Создать расчёт с "Новой категорией"
   - Сохранить и перезагрузить страницу
   - Убедиться что параметры восстановились

### ✅ Приоритет 2: ВЫСОКОЕ (вторая неделя)

5. **День 6-7: Этап 3** - Базовые компоненты
   - Создать CostComponents
   - Перенести общую логику

6. **День 8-10: Этап 4** - Рефакторинг маршрутов
   - BaseRoute
   - HighwayRailRoute, HighwayAirRoute
   - PrologixRoute, SeaContainerRoute

7. **День 11: Интеграция и тестирование**
   - Удалить старые методы calculate_*_cost()
   - Полное тестирование всех маршрутов

### ⚠️ Опционально: Версионирование (позже)

8. **Этап 5** - Версии расчётов (если будет нужно)

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### После Этапа 1 (критическое):
- ✅ "Новая категория" работает ПОЛНОСТЬЮ
- ✅ Кастомные параметры сохраняются в БД
- ✅ При открытии расчёта из истории параметры восстанавливаются
- ✅ Цифры корректные после перезагрузки страницы

### После Этапа 2:
- ✅ Новые поля добавляются в ОДНОМ месте
- ✅ Невозможно забыть параметр при добавлении endpoint

### После Этапов 3-4:
- ✅ Код сокращён с 4,600 до ~2,000 строк
- ✅ Добавление нового маршрута: 1 день (наследуем BaseRoute)
- ✅ Каждый маршрут легко тестировать изолированно
- ✅ Нет дублирования логики

---

## ⚠️ РИСКИ

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| Сломать сохранение расчётов | Средняя | Поэтапная миграция БД + тесты |
| Потерять данные при миграции | Низкая | Бэкап БД перед изменениями |
| Несовместимость старых расчётов | Средняя | Поддержка legacy полей (custom_rate) |
| Увеличить время расчёта | Очень низкая | Профилирование после каждого этапа |

---

## 📝 ЧЕКЛИСТ ПЕРЕД СТАРТОМ

- [ ] Создать бэкап БД (SQLite + PostgreSQL)
- [ ] Создать ветку `refactoring/v2-with-custom-params`
- [ ] Написать тесты для текущего функционала (baseline)
- [ ] Договориться о времени на рефакторинг
- [ ] Подготовить план отката (если что-то пойдёт не так)

---

**Готов начинать? Начнём с Этапа 0.1 - миграции БД!** 🚀





