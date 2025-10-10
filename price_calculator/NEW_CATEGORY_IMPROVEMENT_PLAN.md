# План улучшения архитектуры "Новая категория"

## 🔴 Текущие проблемы

### Проблема 1: История показывает цены без пользовательской ставки
**Что происходит:**
- Пользователь вводит кастомную ставку для "Новая категория"
- Расчёт выполняется корректно
- Но в истории отображается цена БЕЗ учёта кастомной ставки

**Причина:**
```javascript
// В HistoryPanelV2.js отображается category, но НЕ custom_logistics
{
  "category": "Новая категория",
  "cost_price_rub": 1000,  // Без кастомной ставки?
  "custom_logistics": {     // Эти данные не используются при отображении
    "highway_rail": { "custom_rate": 8.5 }
  }
}
```

### Проблема 2: Форма редактирования открывается постоянно
**Что происходит:**
- При каждом открытии расчёта с "Новая категория"
- Автоматически открывается форма редактирования параметров
- Даже если параметры уже заполнены и сохранены

**Причина:**
```javascript
// RouteEditorV2.js, mounted()
mounted() {
    if (this.isNewCategory) {
        this.openEdit();  // Открывается ВСЕГДА для "Новая категория"
    }
}
```

---

## 🎯 Целевая архитектура

### Принципы:
1. **Разделение ответственности**: "Новая категория" ≠ "требует ввода параметров"
2. **Состояние заполненности**: отслеживать, введены ли кастомные параметры
3. **Корректное отображение**: история показывает финальные цены с учётом всех кастомов
4. **UX без навязчивости**: форма открывается только когда действительно нужна

---

## 📋 Архитектурный план

### Вариант A: "Умная проверка заполненности" (Рекомендуется ✅)

#### Концепция:
Не привязываемся к названию категории "Новая категория", а проверяем **состояние данных**.

#### Ключевые изменения:

**1. Определение "требует параметров"**

Вместо:
```javascript
isNewCategory = (category === "Новая категория")
```

Используем:
```javascript
requiresCustomParams = (
    // Категория помечена как требующая параметров
    category.requires_manual_input === true
    ||
    // ИЛИ базовые ставки равны 0
    (category.rates.rail_base === 0 && category.rates.air_base === 0)
    ||
    // ИЛИ это действительно "Новая категория" без сохранённых параметров
    (category.category === "Новая категория" && !hasCustomLogistics)
)
```

**2. Проверка "параметры уже заполнены"**

```javascript
hasCustomLogistics = (
    custom_logistics && 
    Object.keys(custom_logistics).length > 0 &&
    // Проверяем что хотя бы один маршрут имеет custom_rate
    Object.values(custom_logistics).some(route => route.custom_rate > 0)
)
```

**3. Логика открытия формы**

```javascript
mounted() {
    // Открываем форму ТОЛЬКО если:
    // 1. Требуются кастомные параметры И
    // 2. Параметры ещё НЕ заполнены
    if (this.requiresCustomParams && !this.hasCustomLogistics) {
        this.openEdit();
    }
}
```

**4. Отображение в истории**

```javascript
// HistoryPanelV2.js
computed: {
    displayPrice() {
        // Если есть custom_logistics - показываем цену С учётом кастомов
        if (this.item.custom_logistics) {
            return this.item.cost_price_rub; // Уже рассчитано правильно
        }
        return this.item.cost_price_rub;
    },
    
    hasCustomRates() {
        return this.item.custom_logistics && 
               Object.keys(this.item.custom_logistics).length > 0;
    }
}
```

#### Структура данных:

**В categories.yaml:**
```yaml
- category: Новая категория
  material: ''
  requires_manual_input: true  # 🆕 Явный флаг
  rates:
    rail_base: 0
    air_base: 0
```

**В БД (calculation):**
```json
{
  "id": 123,
  "category": "Новая категория",
  "custom_logistics": {
    "highway_rail": {
      "custom_rate": 8.5,
      "duty_rate": 10,
      "vat_rate": 20
    },
    "highway_air": {
      "custom_rate": 12.0,
      "duty_rate": 10,
      "vat_rate": 20
    }
  },
  "cost_price_rub": 15000,  // С учётом custom_rate=8.5!
  "forced_category": "Новая категория"
}
```

---

### Вариант B: "Категория с шаблоном" (Альтернатива)

#### Концепция:
Создавать для каждого нераспознанного товара **временную кастомную категорию**.

**Workflow:**
1. Товар не распознан → "Новая категория"
2. Пользователь вводит параметры
3. Система создаёт в БД новую категорию с именем товара
4. Следующий расчёт этого товара использует сохранённую категорию

**Преимущества:**
- ✅ Переиспользование параметров для похожих товаров
- ✅ История параметров

**Недостатки:**
- ❌ Засорение БД категориями
- ❌ Сложнее управление
- ❌ Может создать путаницу

**Вердикт:** Не рекомендуется для текущего use case.

---

### Вариант C: "Отдельная сущность CustomProduct" (Избыточно)

#### Концепция:
Создать отдельную таблицу `custom_products` для нераспознанных товаров.

**Недостатки:**
- ❌ Усложнение архитектуры
- ❌ Дублирование логики
- ❌ Избыточно для текущих требований

**Вердикт:** Overkill для текущей задачи.

---

## ✅ Рекомендуемое решение: Вариант A

### Этап 1: Обновление модели категорий

**1.1. Добавить флаг `requires_manual_input` в categories.yaml**
```yaml
- category: Новая категория
  requires_manual_input: true
```

**1.2. Обновить синхронизацию с БД**
- sync_categories.py учитывает новый флаг

### Этап 2: Обновление фронтенда

**2.1. RouteEditorV2.js - умная проверка заполненности**
```javascript
computed: {
    requiresCustomParams() {
        // Проверяем нужны ли кастомные параметры
        return this.category?.requires_manual_input === true ||
               (this.category?.rates?.rail_base === 0 && 
                this.category?.rates?.air_base === 0);
    },
    
    hasCustomLogistics() {
        // Проверяем есть ли уже сохранённые параметры
        return this.customLogistics && 
               Object.keys(this.customLogistics).length > 0;
    },
    
    shouldAutoOpen() {
        // Открываем форму только если нужны параметры И их нет
        return this.requiresCustomParams && !this.hasCustomLogistics;
    }
},

mounted() {
    if (this.shouldAutoOpen) {
        this.openEdit();
    }
}
```

**2.2. HistoryPanelV2.js - отображение кастомных параметров**
```javascript
<div v-if="item.custom_logistics" class="custom-params-badge">
    🔧 Кастомные параметры
</div>

<div class="price-breakdown">
    <div>Себестоимость: {{ formatPrice(item.cost_price_rub) }}</div>
    <div v-if="hasCustomRates" class="custom-rate-indicator">
        ⚙️ С учётом кастомной ставки
    </div>
</div>
```

**2.3. PriceCalculatorAppV2.js - передача custom_logistics в редактор**
```javascript
// При загрузке расчёта из истории
loadCalculation(calculationId) {
    const calc = await axios.get(`/api/v2/calculation/${calculationId}`);
    
    this.formData = {
        // ...
        custom_logistics: calc.data.custom_logistics || {}
    };
}
```

### Этап 3: Обновление бэкенда

**3.1. price_calculator.py - корректный расчёт с кастомными параметрами**

Проверить что:
```python
# При наличии custom_logistics они ВСЕГДА применяются к расчёту
if custom_logistics_params:
    for route_key, params in custom_logistics_params.items():
        if 'custom_rate' in params and params['custom_rate'] is not None:
            # Применяем кастомную ставку
            result['routes'][route_key]['logistics_rate_usd'] = params['custom_rate']
            # ВАЖНО: пересчитываем стоимость!
            result['routes'][route_key]['cost_price'] = recalculate_with_custom_rate(...)
```

**3.2. database.py - сохранение финальных цен**

Проверить что в БД сохраняются цены **С учётом** custom_logistics:
```python
def save_calculation_to_db():
    # result уже содержит пересчитанные цены с кастомными ставками
    cost_price_rub = result['cost_price']['total']['rub']  # Финальная цена!
```

### Этап 4: Тестирование

**Сценарий 1: Первое создание с "Новая категория"**
1. Ввести товар "абракадабра123"
2. Выбирается "Новая категория"
3. ✅ Автоматически открывается форма параметров
4. Ввести custom_rate = 8.5
5. Нажать "Применить"
6. ✅ Расчёт обновляется с новой ставкой
7. ✅ В истории отображается цена с учётом 8.5

**Сценарий 2: Повторное открытие**
1. Открыть расчёт из истории (с "Новая категория")
2. ✅ Форма параметров НЕ открывается автоматически
3. ✅ Видна кнопка "Параметры" для ручного редактирования
4. ✅ Отображается индикатор "🔧 Кастомные параметры"

**Сценарий 3: Редактирование параметров**
1. Открыть расчёт с кастомными параметрами
2. Нажать "Параметры" → "Изменить параметры"
3. Изменить custom_rate с 8.5 на 10.0
4. Нажать "Применить"
5. ✅ Расчёт пересчитывается
6. ✅ История обновляется с новой ценой

---

## 📊 Сравнение До/После

### До (текущая реализация):

**Проблемы:**
- ❌ История показывает неправильные цены
- ❌ Форма открывается постоянно
- ❌ Привязка к названию "Новая категория"
- ❌ Нет индикации кастомных параметров

**Логика:**
```
if (category === "Новая категория") {
    openForm();  // ВСЕГДА
}
```

### После (улучшенная реализация):

**Решения:**
- ✅ История показывает финальные цены
- ✅ Форма открывается только при необходимости
- ✅ Проверка состояния данных, не названия
- ✅ Визуальные индикаторы кастомных параметров

**Логика:**
```
if (requiresCustomParams && !hasCustomLogistics) {
    openForm();  // Только если нужны параметры И их нет
}
```

---

## 🔧 Детальный план реализации

### Шаг 1: Обновление данных категорий (5 мин)
- [ ] Добавить `requires_manual_input: true` в categories.yaml для "Новая категория"
- [ ] Запустить sync_categories.py

### Шаг 2: Обновление RouteEditorV2.js (15 мин)
- [ ] Добавить computed `requiresCustomParams`
- [ ] Добавить computed `hasCustomLogistics`
- [ ] Добавить computed `shouldAutoOpen`
- [ ] Изменить логику mounted() → `if (shouldAutoOpen)`
- [ ] Добавить props для передачи customLogistics

### Шаг 3: Обновление RouteDetailsV2.js (10 мин)
- [ ] Передавать customLogistics в RouteEditorV2
- [ ] Добавить визуальный индикатор "🔧 Кастомные параметры"

### Шаг 4: Обновление HistoryPanelV2.js (15 мин)
- [ ] Добавить computed `hasCustomRates`
- [ ] Добавить индикатор кастомных ставок в UI
- [ ] Добавить tooltip с деталями кастомных параметров

### Шаг 5: Обновление PriceCalculatorAppV2.js (10 мин)
- [ ] При загрузке из истории передавать custom_logistics
- [ ] Обеспечить корректную передачу данных в форму

### Шаг 6: Проверка бэкенда (10 мин)
- [ ] Проверить что price_calculator.py корректно применяет custom_logistics
- [ ] Проверить что финальные цены пересчитываются
- [ ] Проверить что в БД сохраняются правильные цены

### Шаг 7: Тестирование (20 мин)
- [ ] Сценарий 1: Первое создание
- [ ] Сценарий 2: Повторное открытие
- [ ] Сценарий 3: Редактирование
- [ ] Проверка всех маршрутов (Rail, Air, Contract, Prologix)

### Шаг 8: Документация (10 мин)
- [ ] Обновить CATEGORIES_MANAGEMENT.md
- [ ] Добавить секцию "Custom Parameters Workflow"
- [ ] Обновить примеры использования

**Общее время:** ~1.5 часа

---

## 🎯 Ключевые улучшения

### 1. Семантика
**Было:** "Новая категория" = открыть форму  
**Стало:** Проверка состояния данных → решение об открытии

### 2. UX
**Было:** Навязчивое открытие формы  
**Стало:** Умное открытие только при необходимости

### 3. Данные
**Было:** Цены в истории без учёта кастомов  
**Стало:** Финальные цены с учётом всех параметров

### 4. Визуализация
**Было:** Нет индикации кастомных параметров  
**Стало:** Четкие визуальные индикаторы

---

## 🚨 Риски и митигация

### Риск 1: Ломание существующей логики
**Митигация:**
- Пошаговое внедрение
- Тестирование каждого изменения
- Feature flag для новой логики (опционально)

### Риск 2: Несоответствие данных в БД
**Митигация:**
- Проверка что все существующие расчёты загружаются корректно
- Миграция данных если необходимо

### Риск 3: Производительность
**Митигация:**
- Computed properties кэшируются автоматически
- Минимальные дополнительные проверки

---

## 📚 Дополнительные улучшения (опционально)

### 1. Валидация кастомных параметров
```javascript
validateCustomRate(rate, routeType) {
    const limits = {
        highway_rail: { min: 3.0, max: 15.0 },
        highway_air: { min: 5.0, max: 20.0 },
        prologix: { min: 10000, max: 50000 }
    };
    
    const { min, max } = limits[routeType];
    if (rate < min || rate > max) {
        return {
            valid: false,
            message: `Ставка должна быть в диапазоне ${min}-${max}`
        };
    }
    return { valid: true };
}
```

### 2. История изменений параметров
```sql
CREATE TABLE custom_logistics_history (
    id SERIAL PRIMARY KEY,
    calculation_id INT REFERENCES calculations(id),
    route_key VARCHAR(50),
    old_rate DECIMAL,
    new_rate DECIMAL,
    changed_at TIMESTAMP DEFAULT NOW()
);
```

### 3. Шаблоны кастомных параметров
```javascript
// Сохранение шаблона
saveAsTemplate(params, templateName) {
    localStorage.setItem(`template_${templateName}`, JSON.stringify(params));
}

// Применение шаблона
applyTemplate(templateName) {
    const template = localStorage.getItem(`template_${templateName}`);
    if (template) {
        this.editParams = JSON.parse(template);
    }
}
```

---

## ✅ Чеклист готовности к реализации

- [x] Проблемы идентифицированы
- [x] Архитектурное решение выбрано
- [x] План реализации составлен
- [x] Риски оценены
- [x] Тестовые сценарии определены
- [ ] **Готов к реализации** (ждём подтверждения)

---

**Вердикт:** Вариант A (Умная проверка заполненности) - оптимальное решение.

**Время реализации:** ~1.5 часа  
**Сложность:** Средняя  
**Риск:** Низкий (при пошаговой реализации)  
**Польза:** Высокая (решает обе проблемы + улучшает UX)

