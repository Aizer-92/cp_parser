# 📊 V3 ARCHITECTURE - Новая структура данных

Дата создания: 12.10.2025  
Статус: В разработке (Backend Models готовы)

## 🎯 Цель рефакторинга

Разделить монолитную сущность "Расчёт" на **3 логические сущности**:

1. **Position** (Позиция) - ЧТО мы считаем
2. **Calculation** (Расчёт) - вариант от КОНКРЕТНОЙ фабрики для КОНКРЕТНОГО тиража
3. **LogisticsRoute** (Маршрут) - цены по КОНКРЕТНОМУ маршруту доставки

Плюс **Factory** (Фабрика) - справочник фабрик для селектора.

---

## 📐 Структура данных

### 1️⃣ Factory (Фабрика)
**Справочник фабрик** - можно выбрать из списка или создать новую.

```python
Factory:
    id: int
    name: str                           # "Фабрика А"
    contact: str                        # URL/WeChat/Email
    comment: str                        # "Лучшее качество"
    default_sample_time_days: int       # 5 дней
    default_production_time_days: int   # 15 дней
    default_sample_price_yuan: float    # 150¥
```

### 2️⃣ Position (Позиция)
**Что мы считаем** - абстрактный товар.

```python
Position:
    id: int
    name: str                      # "Бутылка с логотипом"
    description: str               # "Термобутылка 500мл, сталь"
    category: str                  # "Бутылки"
    design_files_urls: List[str]   # Ссылки на облако
    custom_fields: Dict            # Доп. поля
    
    # Relationships:
    calculations: List[Calculation]  # Все расчёты для этой позиции
```

### 3️⃣ Calculation (Расчёт)
**Конкретный вариант** от фабрики для тиража.

```python
Calculation:
    id: int
    position_id: int                 # FK → Position
    factory_id: int                  # FK → Factory (опционально)
    
    # Кастомная фабрика (если не из справочника)
    factory_custom_name: str
    factory_custom_url: str
    
    # Условия от фабрики
    sample_time_days: int            # 5 дней
    production_time_days: int        # 15 дней
    sample_price_yuan: float         # 150¥
    factory_comment: str
    
    # Параметры расчёта
    quantity: int                    # 500, 1000, 2000
    price_yuan: float                # 15¥/шт
    
    # Весовые данные
    calculation_type: str            # "quick" | "precise"
    weight_kg: float                 # Для quick
    
    # Пакинг (для precise)
    packing_units_per_box: int
    packing_box_weight: float
    packing_box_length: float
    packing_box_width: float
    packing_box_height: float
    packing_total_boxes: int
    packing_total_volume: float
    packing_total_weight: float
    
    # Relationships:
    position: Position
    factory: Factory
    logistics_routes: List[LogisticsRoute]
```

### 4️⃣ LogisticsRoute (Маршрут логистики)
**Цены по конкретному маршруту** для расчёта.

```python
LogisticsRoute:
    id: int
    calculation_id: int              # FK → Calculation
    route_name: str                  # "highway_rail", "highway_air", etc.
    
    # Кастомные параметры
    custom_rate: float               # 8.0 $/кг
    duty_rate: float                 # 13%
    vat_rate: float                  # 20%
    specific_rate: float
    
    # Рассчитанные цены (за единицу)
    cost_price_rub: float
    cost_price_usd: float
    sale_price_rub: float
    sale_price_usd: float
    profit_rub: float
    profit_usd: float
    
    # Общие суммы (на весь тираж)
    total_cost_rub: float
    total_cost_usd: float
    total_sale_rub: float
    total_sale_usd: float
    total_profit_rub: float
    total_profit_usd: float
```

### 5️⃣ AuditLog (История изменений)
**Для будущего** - логирование всех изменений.

```python
AuditLog:
    id: int
    entity_type: str                 # "Position", "Calculation", etc.
    entity_id: int
    user_id: int                     # Будущее
    action: str                      # "created", "updated", "deleted"
    changes: Dict                    # {"field": {"old": ..., "new": ...}}
```

---

## 🔗 Связи между таблицами

```
Factory (1) ─── (N) Calculation
Position (1) ─── (N) Calculation
Calculation (1) ─── (N) LogisticsRoute
```

**Пример:**
- Position "Бутылка" (1)
  - Calculation "Фабрика А, 500 шт" (1)
    - LogisticsRoute "Highway ЖД" → 145₽
    - LogisticsRoute "Highway Авиа" → 178₽
  - Calculation "Фабрика Б, 500 шт" (2)
    - LogisticsRoute "Highway ЖД" → 135₽
    - LogisticsRoute "Highway Авиа" → 168₽
  - Calculation "Фабрика А, 1000 шт" (3)
    - ...

---

## 📂 Файловая структура

```
models_v3/
├── __init__.py
├── base.py                # Base declarative
├── factory.py             # Factory model
├── position.py            # Position model
├── calculation.py         # Calculation model
├── logistics_route.py     # LogisticsRoute model
└── audit_log.py           # AuditLog model (пока не используется)

services_v3/
├── __init__.py
├── factory_service.py          # CRUD для фабрик
├── position_service.py         # CRUD для позиций
├── calculation_service.py      # CRUD для расчётов
├── logistics_service.py        # CRUD для маршрутов
├── recalculation_service.py    # Пересчёт маршрутов
└── migration_service.py        # Миграция старых данных

api/v3/
├── __init__.py
├── factories.py          # GET/POST/PUT/DELETE /api/v3/factories
├── positions.py          # GET/POST/PUT/DELETE /api/v3/positions
├── calculations.py       # GET/POST/PUT/DELETE /api/v3/calculations
└── logistics.py          # GET/PUT /api/v3/logistics
```

---

## 🚀 План внедрения

### ✅ ЭТАП 1: Backend Models (ГОТОВО)
- [x] Создать SQLAlchemy модели
- [ ] Создать Alembic миграции
- [ ] Применить на Railway test

### 📅 ЭТАП 2: Services (В работе)
- [ ] CRUD сервисы
- [ ] Сервис пересчёта
- [ ] Unit тесты

### 📅 ЭТАП 3: API Endpoints
- [ ] Factories API
- [ ] Positions API
- [ ] Calculations API
- [ ] Integration тесты

### 📅 ЭТАП 4: Data Migration
- [ ] Скрипт миграции
- [ ] Тестирование на копии БД

### 📅 ЭТАП 5: Frontend
- [ ] Список позиций
- [ ] Детали позиции (матрица)
- [ ] Формы добавления/редактирования

### 📅 ЭТАП 6: Deploy
- [ ] Deploy на Railway
- [ ] Миграция production данных
- [ ] Мониторинг

---

## 🎨 UI/UX концепция

### Экран "Позиции"
```
┌──────────────────────────────────────────┐
│ 🍾 Бутылка с логотипом                   │
│ 📊 3 расчёта (2 фабрики, 2 тиража)       │
│ Highway ЖД: от 128₽ до 145₽  ✅         │
│ Highway Авиа: от 135₽ до 178₽          │
└──────────────────────────────────────────┘
```

### Экран "Детали позиции" (Матрица)
```
Тиражи: [500] [1000] [2000]
─────────────────────────────────────────
ТИРАЖ: 500 ШТ

┌─────────────────────────────────────────┐
│ Фабрика A [▼] "Лучшее качество"       │
│ 15¥/шт | 0.45кг | Образец: 5д (150¥)  │
│ Highway ЖД: 145₽ | Авиа: 178₽ ✅      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Фабрика B [▼] "Дешевле, хуже"         │
│ 12¥/шт | 0.50кг | Образец: 7д (100¥)  │
│ Highway ЖД: 135₽ | Авиа: 168₽        │
└─────────────────────────────────────────┘
```

---

## 📝 Примечания

- **Пакинг сохранён** - можно делать точные расчёты с коробками
- **Быстрый ввод** - можно просто указать вес товара
- **Кастомные ставки** - остаются как есть
- **Фабрики** - селектор + возможность добавить новую
- **Сроки** - добавлены поля для образцов и тиражей
- **AuditLog** - таблица создаётся, но пока не используется

---

## 🔄 Обратная совместимость

### Миграция старых данных

```python
# Старая структура:
calculations:
    id, product_name, price_yuan, quantity, custom_logistics, ...

# Новая структура:
Position:
    id, name="product_name", ...

Calculation:
    id, position_id, price_yuan, quantity, ...

LogisticsRoute:
    id, calculation_id, route_name, custom_rate, cost_price_rub, ...
```

### Маппинг полей

| Старое поле | Новая структура |
|-------------|-----------------|
| `product_name` | `Position.name` |
| `product_url` | `Calculation.factory_custom_url` |
| `quantity` | `Calculation.quantity` |
| `price_yuan` | `Calculation.price_yuan` |
| `weight_kg` | `Calculation.weight_kg` |
| `custom_logistics['highway_rail']` | `LogisticsRoute(route_name='highway_rail', ...)` |
| `cost_price_rub` | `LogisticsRoute.cost_price_rub` |
| `sale_price_rub` | `LogisticsRoute.sale_price_rub` |

---

Автор: Cursor AI  
Дата последнего обновления: 12.10.2025



