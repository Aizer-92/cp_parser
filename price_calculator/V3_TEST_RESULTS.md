# V3 API - Результаты тестирования

## Дата: 13.10.2025

---

## 🧪 ТЕСТЫ V3 API

### ✅ ТЕСТ 1: Статус V3 API
```bash
GET /api/v3/status
```

**Результат: ✅ ОК**
```json
{
    "v3_loaded": true,
    "error": null,
    "available_routes": [
        "/api/v3/factories",
        "/api/v3/positions",
        "/api/v3/calculations"
    ]
}
```

---

### ✅ ТЕСТ 2: Расчёт без категории
```bash
POST /api/v3/calculate/execute
{
  "product_name": "Тестовая футболка",
  "price_yuan": 50,
  "quantity": 1000,
  "weight_kg": 0.2,
  "markup": 1.7
}
```

**Результат: ✅ ОК (ожидаемое поведение)**
```json
{
  "category": "Новая категория",
  "needs_custom_params": true,
  "message": "Для этой категории требуется указать кастомные параметры логистики",
  "routes": {
    "highway_rail": { "placeholder": true, "needs_params": true },
    "highway_air": { "placeholder": true, "needs_params": true },
    "highway_contract": { "placeholder": true, "needs_params": true }
  }
}
```

✅ **Правильно:** Для неизвестной категории возвращаются placeholder маршруты

---

### ✅ ТЕСТ 3: Получение категорий
```bash
GET /api/v3/categories
```

**Результат: ✅ ОК**
```json
{
  "total": 105,
  "version": "3.0",
  "source": "PostgreSQL (Railway)",
  "categories": [
    {
      "category": "Авоськи",
      "material": "акрил",
      "duty_rate": "15%",
      "vat_rate": "20%",
      "tnved_code": "5608900000",
      "rates": { "air_base": 6.5, "rail_base": 4.4 }
    },
    ...
  ]
}
```

✅ **Правильно:** Загружено 105 категорий из PostgreSQL

---

### ✅ ТЕСТ 4: Расчёт с известной категорией
```bash
POST /api/v3/calculate/execute
{
  "product_name": "Тестовая футболка",
  "forced_category": "футболка",
  "price_yuan": 50,
  "quantity": 1000,
  "weight_kg": 0.2,
  "markup": 1.7
}
```

**Результат: ✅ ОК**
```
category: футболка
needs_custom_params: False
routes: 3 маршрутов
  highway_rail: 895.88₽/шт, placeholder=False
  highway_air: 931.16₽/шт, placeholder=False
  highway_contract: 923.99₽/шт, placeholder=False
```

✅ **Правильно:** Расчёт выполнен для всех маршрутов с реальными ценами

---

### ❌ ТЕСТ 5: Детальный расчёт с упаковкой
```bash
POST /api/v3/calculate/execute
{
  "product_name": "Футболка с упаковкой",
  "forced_category": "футболка",
  "price_yuan": 50,
  "quantity": 1000,
  "markup": 1.7,
  "is_precise_calculation": true,
  "packing_units_per_box": 50,
  "packing_box_weight": 10,
  "packing_box_length": 0.6,
  "packing_box_width": 0.4,
  "packing_box_height": 0.3
}
```

**Результат: ❌ ОШИБКА 422**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "weight_kg"],
      "msg": "Field required"
    },
    {
      "type": "value_error",
      "loc": ["body", "packing_units_per_box"],
      "msg": "Для точного расчёта требуются все параметры упаковки"
    }
  ]
}
```

❌ **Проблема:** Pydantic схема требует `weight_kg` даже при `is_precise_calculation=true`

---

## 📊 ИТОГИ ТЕСТИРОВАНИЯ

| Тест | Endpoint | Статус | Результат |
|------|----------|--------|-----------|
| 1 | `/api/v3/status` | ✅ | V3 API загружен корректно |
| 2 | `/api/v3/calculate/execute` (без категории) | ✅ | Placeholder маршруты |
| 3 | `/api/v3/categories` | ✅ | 105 категорий из БД |
| 4 | `/api/v3/calculate/execute` (футболка) | ✅ | Реальные цены: 895-931₽/шт |
| 5 | `/api/v3/calculate/execute` (детальный) | ❌ | Ошибка схемы |

**Статус:** 4/5 тестов пройдено (80%)

---

## 🐛 ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ

### Проблема #1: weight_kg обязательно при детальном расчёте

**Файл:** `schemas/calculation_schemas.py` или `main.py`

**Описание:**
- При `is_precise_calculation=true` поле `weight_kg` должно быть `Optional`
- Вес рассчитывается автоматически: `weight_kg = packing_box_weight / packing_units_per_box`
- Но Pydantic схема требует `weight_kg` в обязательном порядке

**Решение:**
```python
class CalculationRequest(BaseModel):
    weight_kg: Optional[float] = None  # ← Сделать optional
    
    @model_validator(mode='after')
    def validate_calculation_mode(self):
        if self.is_precise_calculation:
            # Проверяем все поля упаковки
            if not all([
                self.packing_units_per_box,
                self.packing_box_weight,
                self.packing_box_length,
                self.packing_box_width,
                self.packing_box_height
            ]):
                raise ValueError("Для точного расчёта требуются все параметры упаковки")
            
            # Рассчитываем вес если не указан
            if not self.weight_kg:
                self.weight_kg = self.packing_box_weight / self.packing_units_per_box
        else:
            # Для быстрого режима weight_kg обязателен
            if not self.weight_kg:
                raise ValueError("Для быстрого расчёта укажите вес единицы товара")
        
        return self
```

---

## ✅ ЧТО РАБОТАЕТ ОТЛИЧНО

### 1. V3 API Architecture
- ✅ State Machine корректно определяет необходимость кастомных параметров
- ✅ Placeholder маршруты для неизвестных категорий
- ✅ Реальные расчёты для известных категорий

### 2. PostgreSQL Integration
- ✅ 105 категорий загружаются из БД
- ✅ Метаданные категорий (rates, duty_rate, vat_rate) доступны

### 3. API Response Format
- ✅ Структурированные ответы с routes, logistics, customs
- ✅ Флаги `needs_custom_params`, `placeholder` работают

---

## 🧪 ТЕСТИРОВАНИЕ V3 UI

### Ручное тестирование (в браузере)

**URL:** https://price-calculator-production.up.railway.app/v3

**Сценарий 1: Быстрый расчёт (по весу)**
1. ✅ Откройте /v3
2. ✅ Заполните:
   - Название: "Тестовая футболка"
   - Категория: "футболка" (автоопределение)
   - Цена: 50¥
   - Количество: 1000
   - Вес: 0.2 кг
   - Наценка: 1.7
3. ✅ Нажмите "Рассчитать"
4. ✅ Проверьте результаты: ЖД, Авиа, Контракт

**Ожидаемый результат:** 
- Категория определилась автоматически
- 3 маршрута с ценами ~895-931₽/шт

---

**Сценарий 2: Детальный расчёт (упаковка)**
1. ✅ Откройте /v3
2. ✅ Переключите на "Детальный расчёт"
3. ❌ Заполните упаковку (50шт, 10кг, 0.6x0.4x0.3м)
4. ❌ Нажмите "Рассчитать"

**Текущий результат:** ❌ Ошибка 422 (weight_kg required)
**Ожидаемый после фикса:** ✅ Расчёт выполняется, вес определяется автоматически

---

## 📝 РЕКОМЕНДАЦИИ

### Приоритет 1 (Критично)
1. **Исправить схему для детального расчёта**
   - Сделать `weight_kg` optional
   - Добавить автоматический расчёт веса из упаковки

### Приоритет 2 (Важно)
2. **Протестировать UI вручную**
   - Проверить автоопределение категории
   - Проверить переключение режимов (вес/упаковка)
   - Проверить отображение результатов

### Приоритет 3 (Улучшения)
3. **Добавить integration тесты**
   - Автоматическое тестирование UI
   - E2E тесты для всех сценариев

---

## ✅ ИТОГОВЫЙ ВЕРДИКТ

**V3 API работает на 80%:**

✅ **Что работает:**
- V3 API роутеры загружены
- Расчёт с категорией работает (895-931₽/шт для футболки)
- Placeholder маршруты для неизвестных категорий
- PostgreSQL с 105 категориями

❌ **Что не работает:**
- Детальный расчёт с упаковкой (ошибка схемы)

🔧 **Требуется:**
- Исправить Pydantic схему для `weight_kg`
- Протестировать V3 UI в браузере

**Время тестирования:** ~15 минут  
**Найдено проблем:** 1 критическая

