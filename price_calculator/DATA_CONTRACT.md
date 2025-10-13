# Data Contract - Frontend ↔️ Backend API

**Версия:** 3.0  
**Дата:** 12.10.2025  
**Цель:** Единая спецификация обмена данными между Vue.js фронтендом и FastAPI бэкендом

---

## 🎯 Принципы

1. **Single Source of Truth**: Один формат данных для всех операций
2. **Type Safety**: Явные типы и структуры данных
3. **Consistency**: Одинаковые названия полей везде
4. **Validation**: Валидация на обоих сторонах
5. **Versioning**: API версионирование для обратной совместимости

---

## 📦 Core Data Types

### ProductInput (Frontend → Backend)

Данные товара при создании расчёта.

```typescript
interface ProductInput {
  product_name: string;              // Название товара
  product_url?: string;              // URL товара (опционально)
  price_yuan: number;                // Цена за единицу в юанях
  quantity: number;                  // Количество
  weight_kg: number;                 // Вес единицы товара в кг
  markup: number;                    // Наценка (1.7 = 70%)
  
  // Опциональные параметры для точного расчёта
  is_precise_calculation?: boolean;  // Флаг точного расчёта
  packing_units_per_box?: number;    // Единиц в коробке
  packing_box_weight?: number;       // Вес коробки в кг
  packing_box_length?: number;       // Длина коробки в см
  packing_box_width?: number;        // Ширина коробки в см
  packing_box_height?: number;       // Высота коробки в см
  
  // Переопределение категории и параметров
  forced_category?: string;          // Принудительная категория
  custom_logistics?: CustomLogistics; // Кастомные параметры логистики
}
```

**Валидация:**
- `price_yuan > 0`
- `quantity > 0`
- `weight_kg > 0`
- `markup >= 1.0`

---

### CustomLogistics

Кастомные параметры логистики для переопределения базовых ставок.

```typescript
interface CustomLogistics {
  // Логистические ставки ($/кг)
  highway_rail_rate?: number;      // ЖД ставка
  highway_air_rate?: number;       // Авиа ставка
  
  // Пошлины и НДС (%)
  duty_rate?: number;              // Адвалорная пошлина (0-100)
  vat_rate?: number;               // НДС (обычно 20)
  specific_rate?: number;          // Специфическая ставка (€/кг)
  
  // Тип пошлины
  duty_type?: 'percent' | 'specific' | 'combined';
}
```

**Валидация:**
- Все ставки >= 0
- `duty_rate`, `vat_rate`: 0-100
- `duty_type`: только разрешённые значения

---

### CalculationResult (Backend → Frontend)

Результат расчёта стоимости товара.

```typescript
interface CalculationResult {
  // Базовая информация
  id?: number;                     // ID в БД (если сохранён)
  product_name: string;
  category: string;                // Определённая категория
  unit_price_yuan: number;         // Цена за единицу
  quantity: number;
  weight_kg: number;
  markup: number;
  
  // Флаги состояния
  needs_custom_params?: boolean;   // 🔑 Требуются кастомные параметры
  message?: string;                // Сообщение для пользователя
  
  // Маршруты логистики
  routes: {
    [key: string]: RouteCalculation;
  };
  
  // Дополнительная информация
  packing?: PackingInfo;           // Информация об упаковке
  customs_info?: CustomsInfo;      // Информация о таможне
  density_warning?: DensityWarning; // Предупреждение о плотности
  
  // Метаданные
  created_at?: string;             // ISO timestamp
  updated_at?: string;
}
```

---

### RouteCalculation

Расчёт стоимости по конкретному маршруту.

```typescript
interface RouteCalculation {
  // Основные цены
  per_unit: number;                // Цена за единицу в рублях
  cost_rub: number;                // Общая себестоимость
  cost_usd: number;                // Общая себестоимость в USD
  total_cost_rub: number;          // Итого с наценкой
  
  // Детальная разбивка
  sale_per_unit_rub: number;       // Цена продажи за единицу
  cost_per_unit_rub: number;       // Себестоимость за единицу
  
  // Компоненты стоимости
  logistics?: LogisticsBreakdown;  // Разбивка логистики
  customs?: CustomsBreakdown;      // Разбивка таможни
  
  // Флаги
  placeholder?: boolean;           // Это заглушка (требует заполнения)
  needs_params?: boolean;          // Требуется заполнить параметры
  
  // Дополнительно
  delivery_time_days?: number;     // Срок доставки
  recommended?: boolean;           // Рекомендуемый маршрут
}
```

---

### LogisticsBreakdown

Детальная разбивка логистических затрат.

```typescript
interface LogisticsBreakdown {
  rate_usd_per_kg: number;         // Ставка $/кг
  weight_kg: number;               // Вес груза
  cost_usd: number;                // Стоимость логистики
  cost_rub: number;                // В рублях
  surcharge?: number;              // Надбавка за плотность
}
```

---

### CustomsBreakdown

Детальная разбивка таможенных платежей.

```typescript
interface CustomsBreakdown {
  duty_type: 'percent' | 'specific' | 'combined';
  duty_rate?: number;              // % ставка
  specific_rate?: number;          // €/кг ставка
  vat_rate: number;                // НДС %
  
  duty_amount_usd: number;         // Пошлина
  vat_amount_usd: number;          // НДС
  total_customs_cost_usd: number;  // Итого таможня
  total_customs_cost_rub: number;  // В рублях
}
```

---

### PackingInfo

Информация об упаковке товара.

```typescript
interface PackingInfo {
  units_per_box: number;           // Единиц в коробке
  box_weight_kg: number;           // Вес коробки
  box_length_cm: number;           // Габариты
  box_width_cm: number;
  box_height_cm: number;
  
  total_boxes: number;             // Всего коробок
  total_volume_m3: number;         // Объём
  total_weight_kg: number;         // Общий вес
}
```

---

### CustomsInfo

Информация о таможенном оформлении.

```typescript
interface CustomsInfo {
  tnved_code?: string;             // Код ТН ВЭД
  duty_rate?: number;              // Ставка пошлины
  vat_rate?: number;               // Ставка НДС
  certificates?: string[];         // Требуемые сертификаты
  required_documents?: string;     // Необходимые документы
}
```

---

### DensityWarning

Предупреждение о плотности груза.

```typescript
interface DensityWarning {
  message: string;                 // Текст предупреждения
  calculated_density: number;      // Расчётная плотность кг/м³
  category_density?: number;       // Типичная плотность категории
  severity: 'info' | 'warning' | 'error';
}
```

---

## 🔄 API Endpoints

### POST /api/v3/calculate/execute

Выполнение расчёта стоимости товара.

**Request:**
```json
{
  "product_name": "Футболка хлопковая",
  "price_yuan": 50,
  "quantity": 1000,
  "weight_kg": 0.2,
  "markup": 1.7,
  "forced_category": "футболка",
  "custom_logistics": {
    "highway_rail_rate": 15.5,
    "duty_rate": 13,
    "vat_rate": 20
  }
}
```

**Response (Success):**
```json
{
  "id": 123,
  "product_name": "Футболка хлопковая",
  "category": "футболка",
  "unit_price_yuan": 50,
  "quantity": 1000,
  "weight_kg": 0.2,
  "markup": 1.7,
  "routes": {
    "highway_rail": {
      "per_unit": 450.5,
      "cost_rub": 300000,
      "cost_usd": 3200,
      "total_cost_rub": 510000,
      "sale_per_unit_rub": 510,
      "cost_per_unit_rub": 300,
      "delivery_time_days": 25
    },
    "highway_air": { /* ... */ },
    "highway_contract": { /* ... */ },
    "prologix": { /* ... */ }
  },
  "created_at": "2025-10-12T15:30:00Z"
}
```

**Response (Needs Params):**
```json
{
  "product_name": "Неизвестный товар",
  "category": "Новая категория",
  "unit_price_yuan": 100,
  "quantity": 500,
  "weight_kg": 0.5,
  "markup": 1.7,
  "needs_custom_params": true,
  "message": "Для этой категории требуется указать кастомные параметры логистики",
  "routes": {
    "highway_rail": {
      "per_unit": 0,
      "cost_rub": 0,
      "cost_usd": 0,
      "total_cost_rub": 0,
      "sale_per_unit_rub": 0,
      "cost_per_unit_rub": 0,
      "placeholder": true,
      "needs_params": true
    },
    /* ... остальные маршруты с placeholder: true */
  }
}
```

**Response (Error):**
```json
{
  "detail": "Описание ошибки"
}
```

---

### GET /api/v3/categories

Получение списка категорий.

**Response:**
```json
{
  "total": 105,
  "version": "3.0",
  "source": "PostgreSQL (Railway)",
  "categories": [
    {
      "category": "футболка",
      "material": "хлопок",
      "rail_base": 9.5,
      "air_base": 11.6,
      "duty_rate": 13,
      "vat_rate": 20,
      "tnved_code": "6109100000",
      "keywords": ["футболка", "tshirt", "майка"],
      "requirements": {
        "requires_logistics_rate": false,
        "requires_duty_rate": false,
        "requires_vat_rate": false,
        "requires_specific_rate": false
      }
    }
    /* ... */
  ]
}
```

---

## 🛡️ Validation Rules

### Backend (Pydantic)

```python
from pydantic import BaseModel, Field, validator

class ProductInput(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=500)
    price_yuan: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    weight_kg: float = Field(..., gt=0)
    markup: float = Field(default=1.7, ge=1.0)
    forced_category: Optional[str] = None
    custom_logistics: Optional[Dict] = None
    
    @validator('markup')
    def validate_markup(cls, v):
        if v < 1.0:
            raise ValueError('Наценка должна быть >= 1.0 (100%)')
        return v
```

### Frontend (Vue + Vuelidate)

```javascript
const validationRules = {
  productData: {
    product_name: {
      required,
      minLength: minLength(1),
      maxLength: maxLength(500)
    },
    price_yuan: {
      required,
      numeric,
      minValue: minValue(0.01)
    },
    quantity: {
      required,
      integer,
      minValue: minValue(1)
    },
    weight_kg: {
      required,
      numeric,
      minValue: minValue(0.001)
    },
    markup: {
      required,
      numeric,
      minValue: minValue(1.0)
    }
  }
};
```

---

## 🔧 Implementation Plan

### Phase 1: Backend DTOs (Pydantic Models)

**Файл:** `projects/price_calculator/models/dto.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

class CustomLogisticsDTO(BaseModel):
    """Кастомные параметры логистики"""
    highway_rail_rate: Optional[float] = Field(None, ge=0)
    highway_air_rate: Optional[float] = Field(None, ge=0)
    duty_rate: Optional[float] = Field(None, ge=0, le=100)
    vat_rate: Optional[float] = Field(None, ge=0, le=100)
    specific_rate: Optional[float] = Field(None, ge=0)
    duty_type: Optional[str] = Field(None, regex='^(percent|specific|combined)$')

class ProductInputDTO(BaseModel):
    """Входные данные для расчёта"""
    product_name: str = Field(..., min_length=1, max_length=500)
    product_url: Optional[str] = Field(None, max_length=1000)
    price_yuan: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    weight_kg: float = Field(..., gt=0)
    markup: float = Field(default=1.7, ge=1.0)
    
    is_precise_calculation: Optional[bool] = False
    packing_units_per_box: Optional[int] = Field(None, gt=0)
    packing_box_weight: Optional[float] = Field(None, gt=0)
    packing_box_length: Optional[float] = Field(None, gt=0)
    packing_box_width: Optional[float] = Field(None, gt=0)
    packing_box_height: Optional[float] = Field(None, gt=0)
    
    forced_category: Optional[str] = None
    custom_logistics: Optional[CustomLogisticsDTO] = None

# ... остальные DTO модели
```

### Phase 2: Frontend TypeScript Types

**Файл:** `projects/price_calculator/static/js/v2/types.ts`

```typescript
// Экспорт всех типов для использования в Vue компонентах
export interface ProductInput { /* ... */ }
export interface CustomLogistics { /* ... */ }
export interface CalculationResult { /* ... */ }
export interface RouteCalculation { /* ... */ }
```

### Phase 3: API Layer Refactoring

**Обновить:**
- `main.py` - использовать DTO для валидации
- `useCalculationV3.js` - типизированные API вызовы
- `PriceCalculatorAppV2.js` - типизированные данные

### Phase 4: Database Schema Alignment

**Обновить:**
- `database.py` - использовать единые названия полей
- `calculation_service.py` - маппинг DTO ↔️ DB

---

## 📊 Benefits

1. **Type Safety**: Ошибки типов ловятся на этапе разработки
2. **Auto-completion**: IDE подсказки для всех полей
3. **Validation**: Единая валидация на обоих сторонах
4. **Documentation**: Код = документация
5. **Refactoring**: Легко найти все использования поля
6. **Testing**: Легко создавать тестовые данные

---

## 🚀 Migration Strategy

1. ✅ **Phase 0**: Создать этот документ (DATA_CONTRACT.md)
2. ⏳ **Phase 1**: Создать Pydantic DTOs в `models/dto.py`
3. ⏳ **Phase 2**: Обновить `/api/v3/calculate/execute` на использование DTOs
4. ⏳ **Phase 3**: Создать TypeScript types для фронтенда
5. ⏳ **Phase 4**: Обновить Vue компоненты на typed data
6. ⏳ **Phase 5**: Добавить unit тесты для DTOs
7. ⏳ **Phase 6**: Обновить документацию API

---

## 📝 Naming Conventions

### Поля цен и стоимости

```
✅ CORRECT:
- cost_rub, cost_usd          # Себестоимость
- sale_rub, sale_usd          # Цена продажи
- cost_per_unit_rub           # Себестоимость за единицу
- sale_per_unit_rub           # Цена продажи за единицу
- total_cost_rub              # Итого

❌ WRONG:
- cost_price_total_rub        # Смешанное название
- per_unit                    # Не понятно что именно
- price                       # Слишком общее
```

### Поля логистики

```
✅ CORRECT:
- highway_rail_rate           # Ясно что это ставка ЖД
- logistics_rate_usd_per_kg   # Полное название

❌ WRONG:
- rail_base                   # Не понятно единица измерения
- custom_rate                 # Не понятно какая ставка
```

### Булевы флаги

```
✅ CORRECT:
- is_precise_calculation
- needs_custom_params
- placeholder
- recommended

❌ WRONG:
- precise                     # Не понятно что это флаг
- custom_params               # Выглядит как объект
```

---

## 🔄 Version History

| Version | Date       | Changes |
|---------|------------|---------|
| 3.0     | 2025-10-12 | Initial data contract document |
| 3.1     | TBD        | Add Pydantic DTOs |
| 3.2     | TBD        | Add TypeScript types |

---

## 📚 References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [Vue 3 TypeScript Support](https://vuejs.org/guide/typescript/overview.html)




