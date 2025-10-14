# 🚀 V3 IMPLEMENTATION ROADMAP - План внедрения

**Дата начала:** 14 октября 2025  
**Статус:** 🟢 УТВЕРЖДЕН - Вариант A  
**Общее время:** 32 часа (~4 рабочих дня)

---

## 🎯 СТРАТЕГИЯ

**Ключевое преимущество V3:**
```
Position (1) ←→ (N) Calculations

Пример:
Position: "Рюкзак туристический 60L"
├── Calculation #1: 1000 шт, наценка 1.4, дата: 10.10.2025
├── Calculation #2: 2000 шт, наценка 1.7, дата: 12.10.2025 (кастомные ставки)
└── Calculation #3: 500 шт, наценка 1.5, дата: 14.10.2025 (другая категория)
```

**Бизнес-ценность:**
- ✅ История всех просчетов для одного товара
- ✅ Сравнение разных условий (тираж, наценка, ставки)
- ✅ База знаний по реальным товарам
- ✅ Быстрый пересчет для похожих товаров

---

## 📋 ДЕТАЛЬНЫЙ ПЛАН РАБОТ

### 🔴 ФАЗА 1: Восстановление критического функционала (22 часа)

#### Блок 1.1: Модель данных (4 часа) - ПРИОРИТЕТ #1

**Цель:** Связать Positions ↔ Calculations, сохранять результаты

**Задачи:**

##### 1.1.1 Обновить модель Calculation (2 часа)

**Файл:** `models_v3/calculation.py`

```python
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Calculation(Base):
    """
    Расчет стоимости для позиции
    
    Связь: Position (1) → Calculations (N)
    Каждый расчет = один набор параметров (кол-во, наценка, кастомные ставки)
    """
    __tablename__ = "v3_calculations"
    
    # IDs
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey('v3_positions.id'), nullable=False, index=True)
    
    # ============================================
    # ВХОДНЫЕ ПАРАМЕТРЫ (для пересчета)
    # ============================================
    quantity = Column(Integer, nullable=False)
    markup = Column(Float, nullable=False)
    
    # Кастомные параметры логистики (JSON)
    # Структура: {
    #   "highway_rail": {"custom_rate": 3.5, "duty_rate": 15, "vat_rate": 20},
    #   "highway_contract": {"duty_type": "combined", "duty_rate": 10, "specific_rate": 5, "vat_rate": 20}
    # }
    custom_logistics = Column(JSON, nullable=True)
    
    # Принудительная категория (если пользователь изменил)
    forced_category = Column(String, nullable=True)
    
    # ============================================
    # РЕЗУЛЬТАТЫ РАСЧЕТА (для отображения)
    # ============================================
    
    # Определенная категория (автоматически или вручную)
    category = Column(String, nullable=True, index=True)
    
    # Маршруты логистики (JSON)
    # Структура: {
    #   "highway_rail": {
    #     "name": "Highway ЖД",
    #     "cost_per_unit_rub": 450.50,
    #     "sale_per_unit_rub": 765.85,
    #     "profit_per_unit_rub": 315.35,
    #     "cost_price_rub": 450500,
    #     "sale_price_rub": 765850,
    #     "profit_rub": 315350,
    #     "delivery_days": 25,
    #     "breakdown": {...}  # Детальная структура затрат
    #   },
    #   "highway_air": {...},
    #   ...
    # }
    routes = Column(JSON, nullable=False)
    
    # Таможенные расчеты (JSON)
    # Структура: {
    #   "duty_amount_usd": 150.0,
    #   "duty_amount_rub": 12600.0,
    #   "vat_amount_usd": 450.0,
    #   "vat_amount_rub": 37800.0,
    #   "duty_rate": 9.6,
    #   "vat_rate": 20
    # }
    customs_calculation = Column(JSON, nullable=True)
    
    # Комментарий пользователя (опционально)
    comment = Column(Text, nullable=True)
    
    # ============================================
    # TIMESTAMPS
    # ============================================
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ============================================
    # RELATIONSHIPS
    # ============================================
    position = relationship("Position", back_populates="calculations")
    
    def __repr__(self):
        return f"<Calculation(id={self.id}, position_id={self.position_id}, quantity={self.quantity}, markup={self.markup}, created_at={self.created_at})>"
```

**Проверка:**
```python
# Создание расчета
calc = Calculation(
    position_id=123,
    quantity=1000,
    markup=1.7,
    category="рюкзак",
    routes={"highway_rail": {...}},
    customs_calculation={...}
)
db.add(calc)
db.commit()
```

---

##### 1.1.2 Обновить модель Position (1 час)

**Файл:** `models_v3/position.py`

```python
from sqlalchemy.orm import relationship

class Position(Base):
    __tablename__ = "v3_positions"
    
    # ... существующие поля ...
    
    # ============================================
    # RELATIONSHIPS
    # ============================================
    calculations = relationship(
        "Calculation", 
        back_populates="position",
        order_by="Calculation.created_at.desc()",  # Новые сверху
        cascade="all, delete-orphan"  # При удалении позиции удаляются все расчеты
    )
    
    factory = relationship("Factory", back_populates="positions")
```

**Проверка:**
```python
# Получить все расчеты для позиции
position = db.query(Position).get(123)
print(f"Позиция: {position.name}")
print(f"Расчетов: {len(position.calculations)}")

for calc in position.calculations:
    print(f"  - {calc.created_at}: {calc.quantity} шт × {calc.markup} = {calc.routes['highway_rail']['sale_price_rub']} ₽")
```

---

##### 1.1.3 Создать Alembic миграцию (1 час)

```bash
# Создать миграцию
alembic revision --autogenerate -m "add_calculations_fields_and_relationships"

# Применить миграцию
alembic upgrade head
```

**Проверка на Railway:**
```bash
# SSH в Railway
railway run alembic upgrade head

# Проверить структуру
railway run python -c "from models_v3 import Calculation; print(Calculation.__table__.columns.keys())"
```

---

#### Блок 1.2: API для пересчета (3 часа) - ПРИОРИТЕТ #2

**Цель:** Создать/обновить расчеты, сохранять в БД

##### 1.2.1 Создать endpoint для сохранения расчета (1.5 часа)

**Файл:** `main.py`

```python
from models_v3.calculation import Calculation
from models_v3.position import Position
from services_v3.recalculation_service import RecalculationService

@app.post("/api/v3/calculations", response_model=CalculationResultDTO)
async def create_calculation_v3(request: ProductInputDTO):
    """
    Создать НОВЫЙ расчет для позиции
    
    Flow:
    1. Выполнить расчет (как раньше)
    2. Сохранить в БД (v3_calculations)
    3. Вернуть результат + calculation_id
    """
    try:
        # 1. Выполнить расчет (существующая логика)
        result = await execute_calculation_v3(request)
        
        # 2. Сохранить в БД
        calc = Calculation(
            position_id=request.position_id,  # Должен быть в запросе!
            quantity=request.quantity,
            markup=request.markup,
            category=result.get('category'),
            routes=result.get('routes'),
            customs_calculation=result.get('customs_calculation'),
            custom_logistics=None,  # Пока нет кастомных параметров
            forced_category=request.forced_category if hasattr(request, 'forced_category') else None
        )
        
        db.add(calc)
        db.commit()
        db.refresh(calc)
        
        # 3. Добавить calculation_id в ответ
        result['calculation_id'] = calc.id
        result['created_at'] = calc.created_at.isoformat()
        
        print(f"✅ Расчет сохранен: calculation_id={calc.id}, position_id={calc.position_id}")
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка создания расчета: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

---

##### 1.2.2 Создать endpoint для пересчета (1.5 часа)

**Файл:** `main.py`

```python
@app.put("/api/v3/calculations/{calculation_id}", response_model=CalculationResultDTO)
async def update_calculation_v3(
    calculation_id: int,
    request: ProductInputDTO,
    custom_logistics: Optional[Dict[str, Any]] = None
):
    """
    ПЕРЕСЧИТАТЬ существующий расчет с новыми параметрами
    
    Используется для:
    - Изменения quantity/markup
    - Изменения категории
    - Применения кастомных ставок логистики
    
    Flow:
    1. Загрузить существующий расчет
    2. Обновить параметры
    3. Выполнить пересчет
    4. Сохранить результаты
    5. Вернуть обновленный результат
    """
    try:
        # 1. Загрузить существующий расчет
        calc = db.query(Calculation).filter(Calculation.id == calculation_id).first()
        
        if not calc:
            raise HTTPException(status_code=404, detail=f"Calculation {calculation_id} not found")
        
        print(f"🔄 Пересчет calculation_id={calculation_id}")
        print(f"   Старые параметры: quantity={calc.quantity}, markup={calc.markup}")
        print(f"   Новые параметры: quantity={request.quantity}, markup={request.markup}")
        
        # 2. Обновить параметры
        calc.quantity = request.quantity
        calc.markup = request.markup
        calc.custom_logistics = custom_logistics
        
        if hasattr(request, 'forced_category') and request.forced_category:
            calc.forced_category = request.forced_category
        
        # 3. Загрузить данные позиции для пересчета
        position = db.query(Position).filter(Position.id == calc.position_id).first()
        
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {calc.position_id} not found")
        
        # 4. Подготовить запрос для пересчета
        recalc_request = ProductInputDTO(
            product_name=position.name,
            price_yuan=position.price_yuan,
            quantity=request.quantity,
            markup=request.markup,
            category=calc.forced_category or position.category,
            is_precise_calculation=bool(position.packing_units_per_box),
            weight_kg=position.weight_kg,
            packing_units_per_box=position.packing_units_per_box,
            packing_box_weight=position.packing_box_weight,
            packing_box_length=position.packing_box_length,
            packing_box_width=position.packing_box_width,
            packing_box_height=position.packing_box_height
        )
        
        # 5. Выполнить пересчет с кастомными параметрами (если есть)
        from price_calculator import PriceCalculator
        from strategies.calculation_orchestrator import CalculationOrchestrator
        
        calculator = PriceCalculator()
        categories_dict = {cat['category']: cat for cat in calculator.categories}
        
        orchestrator = CalculationOrchestrator(
            categories=categories_dict,
            price_calculator=calculator
        )
        
        result = orchestrator.calculate(
            product_name=recalc_request.product_name,
            price_yuan=recalc_request.price_yuan,
            quantity=recalc_request.quantity,
            markup=recalc_request.markup,
            weight_kg=recalc_request.weight_kg or 0.2,
            is_precise_calculation=recalc_request.is_precise_calculation,
            packing_units_per_box=recalc_request.packing_units_per_box,
            packing_box_weight=recalc_request.packing_box_weight,
            packing_box_length=recalc_request.packing_box_length,
            packing_box_width=recalc_request.packing_box_width,
            packing_box_height=recalc_request.packing_box_height,
            forced_category=recalc_request.category,
            custom_logistics_params=custom_logistics  # ✅ Передаем кастомные параметры!
        )
        
        # 6. Сохранить результаты
        calc.category = result.get('category')
        calc.routes = result.get('routes')
        calc.customs_calculation = result.get('customs_calculation')
        calc.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(calc)
        
        # 7. Добавить calculation_id в ответ
        result['calculation_id'] = calc.id
        result['created_at'] = calc.created_at.isoformat()
        result['updated_at'] = calc.updated_at.isoformat()
        
        print(f"✅ Расчет обновлен: calculation_id={calc.id}")
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка пересчета: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

---

##### 1.2.3 Endpoint для получения расчета по ID

**Файл:** `main.py`

```python
@app.get("/api/v3/calculations/{calculation_id}")
async def get_calculation_v3(calculation_id: int):
    """
    Получить детали расчета по ID
    """
    calc = db.query(Calculation).filter(Calculation.id == calculation_id).first()
    
    if not calc:
        raise HTTPException(status_code=404, detail=f"Calculation {calculation_id} not found")
    
    # Загрузить позицию для дополнительной информации
    position = db.query(Position).filter(Position.id == calc.position_id).first()
    
    return {
        "calculation_id": calc.id,
        "position_id": calc.position_id,
        "position_name": position.name if position else None,
        "quantity": calc.quantity,
        "markup": calc.markup,
        "category": calc.category,
        "routes": calc.routes,
        "customs_calculation": calc.customs_calculation,
        "custom_logistics": calc.custom_logistics,
        "forced_category": calc.forced_category,
        "comment": calc.comment,
        "created_at": calc.created_at.isoformat(),
        "updated_at": calc.updated_at.isoformat() if calc.updated_at else None
    }
```

---

#### Блок 1.3: RouteEditorV3 компонент (4 часа) - ПРИОРИТЕТ #3

**Цель:** Редактирование каждого маршрута отдельно (как в V2)

##### 1.3.1 Создать RouteEditorV3.js (3 часа)

**Файл:** `static/js/v3/RouteEditorV3.js`

```javascript
// RouteEditorV3.js - Редактор параметров маршрута (аналог V2)
window.RouteEditorV3 = {
    props: {
        routeKey: String,      // highway_rail, highway_air, etc.
        route: Object,         // Данные маршрута
        calculationId: Number  // ID текущего расчета
    },
    
    data() {
        return {
            isEditing: false,
            editParams: {
                custom_rate: null,
                duty_type: 'percent',  // percent, specific, combined
                duty_rate: null,
                specific_rate: null,
                vat_rate: null
            }
        };
    },
    
    computed: {
        routeTitle() {
            const titles = {
                'highway_rail': 'Highway ЖД',
                'highway_air': 'Highway Авиа',
                'highway_contract': 'Highway под контракт',
                'prologix': 'Prologix',
                'sea_container': 'Море контейнером'
            };
            return titles[this.routeKey] || this.routeKey;
        },
        
        isHighway() {
            return this.routeKey === 'highway_rail' || this.routeKey === 'highway_air';
        },
        
        isContract() {
            return this.routeKey === 'highway_contract' || 
                   this.routeKey === 'prologix' || 
                   this.routeKey === 'sea_container';
        },
        
        canEditLogistics() {
            // Все маршруты кроме sea_container имеют логистическую ставку
            return this.routeKey !== 'sea_container';
        },
        
        canEditDuty() {
            // Только контрактные маршруты имеют пошлины
            return this.isContract;
        }
    },
    
    methods: {
        openEdit() {
            this.isEditing = true;
            
            // Загрузить текущие значения из route
            if (this.canEditLogistics) {
                // Извлечь логистическую ставку из breakdown
                const breakdown = this.route.breakdown;
                if (breakdown && breakdown.logistics_rate) {
                    this.editParams.custom_rate = breakdown.logistics_rate;
                }
            }
            
            if (this.canEditDuty) {
                // Извлечь пошлины из customs_info
                const customs = this.route.customs_info || {};
                this.editParams.duty_type = customs.duty_type || 'percent';
                this.editParams.duty_rate = customs.duty_rate;
                this.editParams.specific_rate = customs.specific_rate;
                this.editParams.vat_rate = customs.vat_rate;
            }
            
            console.log('✏️ Открыто редактирование:', this.routeKey, this.editParams);
        },
        
        cancelEdit() {
            this.isEditing = false;
        },
        
        async applyEdit() {
            console.log('💾 Применение изменений для', this.routeKey, this.editParams);
            
            // Подготовить custom_logistics
            const customLogistics = {};
            customLogistics[this.routeKey] = {};
            
            if (this.canEditLogistics && this.editParams.custom_rate) {
                customLogistics[this.routeKey].custom_rate = parseFloat(this.editParams.custom_rate);
            }
            
            if (this.canEditDuty) {
                customLogistics[this.routeKey].duty_type = this.editParams.duty_type;
                
                if (this.editParams.duty_rate) {
                    customLogistics[this.routeKey].duty_rate = parseFloat(this.editParams.duty_rate);
                }
                
                if (this.editParams.specific_rate) {
                    customLogistics[this.routeKey].specific_rate = parseFloat(this.editParams.specific_rate);
                }
                
                if (this.editParams.vat_rate) {
                    customLogistics[this.routeKey].vat_rate = parseFloat(this.editParams.vat_rate);
                }
            }
            
            console.log('📤 Custom logistics:', customLogistics);
            
            // Эмитим событие для пересчета
            this.$emit('update-route', {
                routeKey: this.routeKey,
                customLogistics: customLogistics
            });
            
            this.isEditing = false;
        }
    },
    
    template: `
    <div class="route-editor-card">
        <!-- Заголовок маршрута -->
        <div class="route-editor-header">
            <h4 class="route-name">{{ routeTitle }}</h4>
            <button 
                @click="openEdit" 
                v-if="!isEditing"
                class="btn-icon"
                title="Редактировать параметры маршрута"
            >
                ✏
            </button>
        </div>
        
        <!-- Отображение результатов (когда НЕ редактируем) -->
        <div v-if="!isEditing" class="route-results">
            <div class="route-row">
                <span class="route-label">Себестоимость:</span>
                <span class="route-value">{{ route.cost_per_unit_rub?.toFixed(2) || 0 }} ₽/шт</span>
            </div>
            <div class="route-row">
                <span class="route-label">Продажная цена:</span>
                <span class="route-value">{{ route.sale_per_unit_rub?.toFixed(2) || 0 }} ₽/шт</span>
            </div>
            <div class="route-row">
                <span class="route-label">Прибыль:</span>
                <span class="route-value text-success">{{ route.profit_per_unit_rub?.toFixed(2) || 0 }} ₽/шт</span>
            </div>
            <div class="route-row">
                <span class="route-label">Срок доставки:</span>
                <span class="route-value">{{ route.delivery_time || '—' }}</span>
            </div>
        </div>
        
        <!-- Форма редактирования (когда редактируем) -->
        <div v-if="isEditing" class="route-edit-form">
            <!-- Логистическая ставка (для Highway и Prologix) -->
            <div v-if="canEditLogistics" class="form-group">
                <label>Логистическая ставка ($/кг)</label>
                <input
                    v-model.number="editParams.custom_rate"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="Например: 3.5"
                    class="form-input"
                />
                <div class="form-hint">
                    Оставьте пустым для использования базовой ставки
                </div>
            </div>
            
            <!-- Пошлины и НДС (для контрактных маршрутов) -->
            <div v-if="canEditDuty">
                <div class="form-group">
                    <label>Тип пошлины</label>
                    <select v-model="editParams.duty_type" class="form-input">
                        <option value="percent">Адвалорная (%)</option>
                        <option value="specific">Специфическая ($/кг)</option>
                        <option value="combined">Комбинированная (% + $/кг)</option>
                    </select>
                </div>
                
                <div v-if="editParams.duty_type === 'percent' || editParams.duty_type === 'combined'" class="form-group">
                    <label>Пошлина (%)</label>
                    <input
                        v-model.number="editParams.duty_rate"
                        type="number"
                        step="0.1"
                        min="0"
                        max="100"
                        placeholder="Например: 15"
                        class="form-input"
                    />
                </div>
                
                <div v-if="editParams.duty_type === 'specific' || editParams.duty_type === 'combined'" class="form-group">
                    <label>Специфическая ставка ($/кг)</label>
                    <input
                        v-model.number="editParams.specific_rate"
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="Например: 2.5"
                        class="form-input"
                    />
                </div>
                
                <div class="form-group">
                    <label>НДС (%)</label>
                    <input
                        v-model.number="editParams.vat_rate"
                        type="number"
                        step="0.1"
                        min="0"
                        max="100"
                        placeholder="Например: 20"
                        class="form-input"
                    />
                </div>
            </div>
            
            <!-- Кнопки -->
            <div class="form-actions">
                <button @click="applyEdit" class="btn-primary">
                    Применить
                </button>
                <button @click="cancelEdit" class="btn-secondary">
                    Отмена
                </button>
            </div>
        </div>
    </div>
    `
};
```

---

##### 1.3.2 Интегрировать в CalculationResultsV3 (1 час)

**Файл:** `static/js/v3/CalculationResultsV3.js`

```javascript
// Добавить в data()
data() {
    return {
        expandedRoutes: {},
        needsCustomParams: false,
        lastRequestData: null,
        editingRoutes: {}  // ✅ NEW: Для отслеживания редактируемых маршрутов
    };
},

// Добавить метод handleUpdateRoute
methods: {
    async handleUpdateRoute(data) {
        console.log('🔄 Пересчет маршрута:', data);
        
        try {
            // Пересчет с кастомными параметрами
            const response = await axios.put(
                `/api/v3/calculations/${this.result.calculation_id}`,
                {
                    ...this.initialRequestData,
                    custom_logistics: data.customLogistics
                }
            );
            
            console.log('✅ Пересчет выполнен');
            
            // Обновить результаты
            this.$emit('recalculate', response.data);
            
        } catch (error) {
            console.error('❌ Ошибка пересчета:', error);
            alert('Ошибка пересчета: ' + (error.response?.data?.detail || error.message));
        }
    },
    
    // ... остальные методы
}

// Обновить template
template: `
<div class="calculation-results">
    <!-- ... (пустое состояние и форма кастомных параметров) ... -->
    
    <!-- Результаты -->
    <div v-else class="card">
        <!-- ... (заголовок, информация о товаре) ... -->
        
        <!-- Маршруты с редакторами -->
        <div style="margin-top: 24px;">
            <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px;">
                Варианты доставки ({{ sortedRoutes.length }})
            </h3>
            
            <!-- ✅ NEW: Используем RouteEditorV3 вместо свернутых карточек -->
            <div v-for="route in sortedRoutes" :key="route.key" style="margin-bottom: 16px;">
                <RouteEditorV3
                    :route-key="route.key"
                    :route="route"
                    :calculation-id="result.calculation_id"
                    @update-route="handleUpdateRoute"
                />
            </div>
        </div>
    </div>
</div>
`
```

---

#### Блок 1.4: Быстрое редактирование (3 часа) - ПРИОРИТЕТ #4

**Цель:** Изменить цену/количество/наценку без возврата к форме

##### 1.4.1 Создать QuickEditModalV3.js (2 часа)

**Файл:** `static/js/v3/QuickEditModalV3.js`

```javascript
// QuickEditModalV3.js - Быстрое редактирование основных параметров
window.QuickEditModalV3 = {
    props: {
        show: Boolean,
        priceYuan: Number,
        quantity: Number,
        markup: Number
    },
    
    data() {
        return {
            editParams: {
                price_yuan: this.priceYuan,
                quantity: this.quantity,
                markup: this.markup
            }
        };
    },
    
    watch: {
        show(val) {
            if (val) {
                // Обновить значения при открытии
                this.editParams.price_yuan = this.priceYuan;
                this.editParams.quantity = this.quantity;
                this.editParams.markup = this.markup;
            }
        }
    },
    
    methods: {
        apply() {
            this.$emit('apply', this.editParams);
        },
        
        cancel() {
            this.$emit('cancel');
        }
    },
    
    template: `
    <div v-if="show" class="modal-overlay" @click.self="cancel">
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">
                <h3>Быстрое редактирование</h3>
                <button @click="cancel" class="btn-close">✕</button>
            </div>
            
            <div class="modal-body">
                <div class="form-group">
                    <label>Цена в юанях *</label>
                    <input
                        v-model.number="editParams.price_yuan"
                        type="number"
                        step="0.01"
                        min="0"
                        required
                        class="form-input"
                    />
                </div>
                
                <div class="form-group">
                    <label>Количество *</label>
                    <input
                        v-model.number="editParams.quantity"
                        type="number"
                        min="1"
                        required
                        class="form-input"
                    />
                </div>
                
                <div class="form-group">
                    <label>Наценка *</label>
                    <input
                        v-model.number="editParams.markup"
                        type="number"
                        step="0.01"
                        min="1"
                        required
                        class="form-input"
                    />
                    <div class="form-hint">
                        Например: 1.4 = 40% прибыли, 1.7 = 70% прибыли
                    </div>
                </div>
            </div>
            
            <div class="modal-footer">
                <button @click="apply" class="btn-primary">
                    Пересчитать
                </button>
                <button @click="cancel" class="btn-secondary">
                    Отмена
                </button>
            </div>
        </div>
    </div>
    `
};
```

---

##### 1.4.2 Интегрировать в CalculationResultsV3 (1 час)

**Файл:** `static/js/v3/CalculationResultsV3.js`

```javascript
data() {
    return {
        // ...
        showQuickEdit: false,  // ✅ NEW
    };
},

methods: {
    openQuickEdit() {
        this.showQuickEdit = true;
    },
    
    async applyQuickEdit(params) {
        console.log('⚡ Быстрое редактирование:', params);
        
        try {
            // Пересчет с новыми параметрами
            const response = await axios.put(
                `/api/v3/calculations/${this.result.calculation_id}`,
                {
                    ...this.initialRequestData,
                    price_yuan: params.price_yuan,
                    quantity: params.quantity,
                    markup: params.markup
                }
            );
            
            console.log('✅ Пересчет выполнен');
            
            this.showQuickEdit = false;
            this.$emit('recalculate', response.data);
            
        } catch (error) {
            console.error('❌ Ошибка пересчета:', error);
            alert('Ошибка: ' + (error.response?.data?.detail || error.message));
        }
    },
    
    cancelQuickEdit() {
        this.showQuickEdit = false;
    }
},

template: `
<div class="calculation-results">
    <!-- QuickEditModal -->
    <QuickEditModalV3
        :show="showQuickEdit"
        :price-yuan="initialRequestData?.price_yuan"
        :quantity="initialRequestData?.quantity"
        :markup="initialRequestData?.markup"
        @apply="applyQuickEdit"
        @cancel="cancelQuickEdit"
    />
    
    <!-- ... остальной template ... -->
    
    <!-- Кнопки управления -->
    <div style="display: flex; gap: 12px;">
        <button @click="openQuickEdit" class="btn-secondary">
            ⚡ Быстрое редактирование
        </button>
        <button @click="openCustomParams" class="btn-secondary">
            Изменить ставки
        </button>
        <button @click="newCalculation" class="btn-text">
            Новый расчёт
        </button>
    </div>
</div>
`
```

---

#### Блок 1.5: Изменение категории (3 часа) - ПРИОРИТЕТ #5

##### 1.5.1 Создать CategoryChangeModalV3.js (2 часа)

**Файл:** `static/js/v3/CategoryChangeModalV3.js`

```javascript
// CategoryChangeModalV3.js - Изменение категории с пересчетом
window.CategoryChangeModalV3 = {
    props: {
        show: Boolean,
        currentCategory: String
    },
    
    data() {
        return {
            searchQuery: '',
            selectedCategory: this.currentCategory,
            availableCategories: [],
            filteredCategories: []
        };
    },
    
    watch: {
        show(val) {
            if (val) {
                this.loadCategories();
                this.selectedCategory = this.currentCategory;
                this.searchQuery = this.currentCategory || '';
            }
        },
        
        searchQuery(val) {
            this.filterCategories();
        }
    },
    
    methods: {
        async loadCategories() {
            try {
                const response = await axios.get('/api/v3/categories');
                const data = response.data;
                
                if (Array.isArray(data)) {
                    this.availableCategories = data.map(c => c.category || c.name || c);
                } else if (data.categories) {
                    this.availableCategories = data.categories.map(c => c.category || c.name || c);
                }
                
                this.filterCategories();
                
                console.log('✅ Загружено категорий:', this.availableCategories.length);
            } catch (error) {
                console.error('❌ Ошибка загрузки категорий:', error);
            }
        },
        
        filterCategories() {
            const query = this.searchQuery.toLowerCase().trim();
            
            if (!query) {
                this.filteredCategories = this.availableCategories.slice(0, 10);
                return;
            }
            
            this.filteredCategories = this.availableCategories
                .filter(cat => cat.toLowerCase().includes(query))
                .slice(0, 10);
        },
        
        selectCategory(category) {
            this.selectedCategory = category;
            this.searchQuery = category;
        },
        
        apply() {
            if (!this.selectedCategory) {
                alert('Выберите категорию');
                return;
            }
            
            this.$emit('apply', this.selectedCategory);
        },
        
        cancel() {
            this.$emit('cancel');
        }
    },
    
    template: `
    <div v-if="show" class="modal-overlay" @click.self="cancel">
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">
                <h3>Изменить категорию</h3>
                <button @click="cancel" class="btn-close">✕</button>
            </div>
            
            <div class="modal-body">
                <div class="form-group">
                    <label>Категория</label>
                    <input
                        v-model="searchQuery"
                        type="text"
                        placeholder="Начните вводить название..."
                        class="form-input"
                        @focus="filterCategories"
                    />
                    <div class="form-hint">
                        Текущая: <strong>{{ currentCategory || 'не определена' }}</strong>
                    </div>
                </div>
                
                <!-- Список категорий -->
                <div v-if="filteredCategories.length > 0" class="categories-list">
                    <div
                        v-for="cat in filteredCategories"
                        :key="cat"
                        @click="selectCategory(cat)"
                        :class="['category-item', { 'active': cat === selectedCategory }]"
                    >
                        {{ cat }}
                    </div>
                </div>
                
                <div v-else class="empty-state">
                    Категории не найдены
                </div>
            </div>
            
            <div class="modal-footer">
                <button @click="apply" class="btn-primary">
                    Применить и пересчитать
                </button>
                <button @click="cancel" class="btn-secondary">
                    Отмена
                </button>
            </div>
        </div>
    </div>
    `
};
```

---

##### 1.5.2 Интегрировать в CalculationResultsV3 (1 час)

```javascript
data() {
    return {
        // ...
        showCategoryChange: false,  // ✅ NEW
    };
},

methods: {
    openCategoryChange() {
        this.showCategoryChange = true;
    },
    
    async applyCategoryChange(newCategory) {
        console.log('🏷️ Изменение категории:', this.result.category, '→', newCategory);
        
        try {
            // Пересчет с новой категорией
            const response = await axios.put(
                `/api/v3/calculations/${this.result.calculation_id}`,
                {
                    ...this.initialRequestData,
                    forced_category: newCategory
                }
            );
            
            console.log('✅ Пересчет с новой категорией выполнен');
            
            this.showCategoryChange = false;
            this.$emit('recalculate', response.data);
            
        } catch (error) {
            console.error('❌ Ошибка пересчета:', error);
            alert('Ошибка: ' + (error.response?.data?.detail || error.message));
        }
    },
    
    cancelCategoryChange() {
        this.showCategoryChange = false;
    }
},

template: `
<div class="calculation-results">
    <!-- CategoryChangeModal -->
    <CategoryChangeModalV3
        :show="showCategoryChange"
        :current-category="result?.category"
        @apply="applyCategoryChange"
        @cancel="cancelCategoryChange"
    />
    
    <!-- ... -->
    
    <!-- Информация о товаре -->
    <div class="result-summary">
        <div class="summary-row">
            <span>Категория:</span>
            <span>
                {{ result.category || 'не определена' }}
                <button @click="openCategoryChange" class="btn-text" style="margin-left: 8px;">
                    изменить
                </button>
            </span>
        </div>
    </div>
</div>
`
```

---

#### Блок 1.6: История расчетов для позиции (3 часа) - ПРИОРИТЕТ #6

**Цель:** Показать все расчеты для одной позиции

##### 1.6.1 Обновить PositionsListV3 (2 часа)

**Файл:** `static/js/v3/PositionsListV3.js`

```javascript
// Добавить в template карточки позиции

template: `
<div class="positions-list">
    <!-- ... фильтры и поиск ... -->
    
    <div class="positions-grid">
        <div v-for="position in positions" :key="position.id" class="position-card">
            <!-- ... (изображение, название, описание) ... -->
            
            <!-- ✅ NEW: История расчетов -->
            <div v-if="position.calculations && position.calculations.length > 0" class="calculations-history">
                <h5 style="font-size: 12px; font-weight: 600; margin-bottom: 8px; color: #6b7280;">
                    История расчетов ({{ position.calculations.length }})
                </h5>
                
                <div 
                    v-for="calc in position.calculations.slice(0, 3)" 
                    :key="calc.id"
                    class="calculation-item"
                    @click="openCalculation(calc)"
                >
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 11px; color: #9ca3af;">
                                {{ formatDate(calc.created_at) }}
                            </div>
                            <div style="font-size: 12px; color: #374151;">
                                {{ calc.quantity }} шт × {{ calc.markup }}
                            </div>
                        </div>
                        <button class="btn-icon-small">→</button>
                    </div>
                </div>
                
                <button 
                    v-if="position.calculations.length > 3"
                    @click="showAllCalculations(position)"
                    class="btn-text-small"
                    style="width: 100%; margin-top: 4px;"
                >
                    Показать еще {{ position.calculations.length - 3 }}
                </button>
            </div>
            
            <!-- ... (кнопки действий) ... -->
        </div>
    </div>
</div>
`,

methods: {
    async loadPositions() {
        try {
            const positionsAPI = window.usePositionsV3();
            
            // ✅ Загружаем с расчетами
            const positions = await positionsAPI.getPositions({
                include_calculations: true,  // NEW параметр
                limit: 20
            });
            
            this.positions = positions;
            console.log('✅ Позиции загружены с расчетами:', positions.length);
            
        } catch (error) {
            console.error('❌ Ошибка загрузки позиций:', error);
        }
    },
    
    openCalculation(calc) {
        console.log('📊 Открыть расчет:', calc.id);
        
        // Эмитим событие для открытия расчета
        this.$emit('open-calculation', calc);
    },
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return 'Сегодня';
        if (diffDays === 1) return 'Вчера';
        if (diffDays < 7) return `${diffDays} дн. назад`;
        
        return date.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    },
    
    showAllCalculations(position) {
        // TODO: Показать модал со всеми расчетами
        console.log('Показать все расчеты для позиции:', position.id);
    }
}
```

---

##### 1.6.2 Обновить API endpoint (1 час)

**Файл:** `api/v3/positions.py`

```python
@router.get("/", response_model=List[PositionResponse])
def get_positions(
    skip: int = 0,
    limit: int = 100,
    include_calculations: bool = False,  # ✅ NEW параметр
    db: Session = Depends(get_db)
):
    """
    Получить список позиций
    
    Args:
        include_calculations: Включить последние расчеты для каждой позиции
    """
    query = db.query(Position).offset(skip).limit(limit)
    
    if include_calculations:
        # Eager load calculations (последние 5)
        from sqlalchemy.orm import joinedload
        query = query.options(
            joinedload(Position.calculations).limit(5)
        )
    
    positions = query.all()
    return positions
```

---

### 🟡 ФАЗА 2: Архитектурные улучшения (10 часов)

#### Блок 2.1: Calculation Store (Pinia) (6 часов)

**Цель:** Единое хранилище состояния расчетов

**Задачи:**
1. Установить Pinia (1 час)
2. Создать `stores/calculationStore.js` (3 часа)
3. Интегрировать в компоненты (2 часа)

**Примечание:** Можно отложить до завершения Фазы 1

---

### 🟢 ФАЗА 3: Новые фичи (24 часа)

**Примечание:** Только ПОСЛЕ завершения Фазы 1!

---

## ✅ КРИТЕРИИ ГОТОВНОСТИ

### Фаза 1 считается завершенной когда:

- [ ] Модель `Calculation` обновлена с полями для результатов
- [ ] Связь `Position` ↔ `Calculations` работает
- [ ] API `POST /api/v3/calculations` создает и сохраняет расчет
- [ ] API `PUT /api/v3/calculations/{id}` пересчитывает с новыми параметрами
- [ ] `RouteEditorV3` редактирует каждый маршрут отдельно
- [ ] `QuickEditModalV3` изменяет цену/количество/наценку
- [ ] `CategoryChangeModalV3` меняет категорию с пересчетом
- [ ] `PositionsListV3` показывает историю расчетов
- [ ] Все компоненты интегрированы и протестированы
- [ ] Деплой на Railway успешен

---

## 📅 ГРАФИК РАБОТ (4 рабочих дня)

### День 1 (8 часов)
- Блок 1.1: Модель данных (4 ч)
- Блок 1.2: API для пересчета (3 ч)
- Перерыв и деплой на Railway (1 ч)

### День 2 (8 часов)
- Блок 1.3: RouteEditorV3 (4 ч)
- Блок 1.4: Быстрое редактирование (3 ч)
- Тестирование (1 ч)

### День 3 (6 часов)
- Блок 1.5: Изменение категории (3 ч)
- Блок 1.6: История расчетов (3 ч)

### День 4 (2 часа)
- Финальное тестирование
- Исправление багов
- Документация

---

## 🚀 НАЧИНАЕМ С...

### Прямо сейчас (следующие 2 часа):

**Задача 1.1.1: Обновить модель Calculation**

```bash
cd /Users/bakirovresad/Downloads/Reshad\ 1/projects/price_calculator

# Открыть файл модели
code models_v3/calculation.py

# После изменений - создать миграцию
alembic revision --autogenerate -m "add_calculations_result_fields"

# Проверить миграцию
code alembic/versions/*.py

# Применить локально
alembic upgrade head

# Деплой на Railway
git add -A
git commit -m "feat: add Calculation result fields and relationships"
git push origin main

# Применить миграцию на Railway
railway run alembic upgrade head
```

**ВАЖНО:** После каждого блока - деплой и тестирование!

---

## 📞 КОНТРОЛЬНЫЕ ТОЧКИ

После каждого блока - проверка:
1. ✅ Код работает локально
2. ✅ Миграции применены
3. ✅ Деплой на Railway успешен
4. ✅ API endpoints работают
5. ✅ Frontend интегрирован

**Если что-то не работает - СТОП! Исправляем перед следующим блоком.**

---

## 🎯 ГОТОВЫ НАЧАТЬ?

Скажите "начинаем" и я создам первый файл: обновленную модель `Calculation`! 🚀

