# Рефакторинг Stage 2: Сервисный слой и модульность

## ✅ Этап 2.1: Создание сервисного слоя (Завершено)

### Что сделали:
1. **Создан `services/calculation_service.py`**
   - `CalculationService` - класс для работы с расчетами
   - `perform_calculation()` - выполнение расчета
   - `create_calculation()` - создание записи в БД
   - `update_calculation()` - обновление записи в БД
   - `_prepare_db_data()` - подготовка данных для БД

### Преимущества:
- ✅ Единая точка входа для работы с расчетами
- ✅ Разделение ответственности (API ↔️ Бизнес-логика ↔️ БД)
- ✅ Упрощение тестирования
- ✅ Переиспользование кода

### Исправленные баги:
- ❌ KeyError: 'customs_info' → ✅ Безопасное извлечение с `or {}`
- ❌ KeyError: 'cost_price_rub' → ✅ Правильные названия ключей в `_prepare_db_data`

---

## ✅ Этап 2.2: Рефакторинг RouteEditorV2 (Завершено)

### Что сделали:
1. **Создан `static/js/v2/RouteEditorMixin.js`**
   - Миксин с общими утилитами для редактирования маршрутов
   - 9 переиспользуемых методов

2. **Рефакторинг `RouteEditorV2.js`**
   - Подключен миксин
   - Сокращён код с 335 строк → ~266 строк (~20% меньше)
   - Упрощена логика `openEdit()`, `saveEdit()`, computed свойства

### Функции миксина:

#### Утилиты для работы с числами:
- `parseFloatSafe(value)` - безопасное преобразование в число
- `cleanNumericParams(params)` - очистка всех числовых полей объекта

#### Дефолтные значения:
- `getDefaultRate(routeKey)` - получить дефолтную ставку для маршрута

#### Извлечение данных:
- `extractLogisticsRate(route, routeKey, isNewCategory)` - извлечь логистическую ставку
- `extractDutyData(route, routeKey)` - извлечь данные о пошлинах

#### Валидация:
- `validateRouteParams(params, routeKey, isNewCategory)` - валидация параметров

#### Метаданные:
- `getRouteTitle(routeKey)` - получить название маршрута
- `getRouteType(routeKey)` - получить объект с флагами типа маршрута

### Преимущества:
- ✅ Переиспользуемая логика
- ✅ Упрощение компонентов
- ✅ Единообразие обработки данных
- ✅ Легче тестировать
- ✅ Меньше дублирования

### Было vs Стало:

#### Было (openEdit):
```javascript
openEdit() {
    this.isEditing = true;
    
    // 63 строки сложной логики с множеством условий
    if (this.isPrologix) {
        if (this.route.rate_rub_per_m3) {
            this.editParams.custom_rate = this.route.rate_rub_per_m3;
        } else if (this.route.breakdown && this.route.breakdown.prologix_rate) {
            // ... еще 60 строк
        }
    }
}
```

#### Стало (openEdit):
```javascript
openEdit() {
    this.isEditing = true;
    
    // Загружаем логистическую ставку
    if (!this.isSeaContainer) {
        this.editParams.custom_rate = this.extractLogisticsRate(
            this.route, this.routeKey, this.isNewCategory
        );
    }
    
    // Загружаем данные о пошлинах
    if (this.isContract || this.isPrologix || this.isSeaContainer) {
        const dutyData = this.extractDutyData(this.route, this.routeKey);
        this.editParams.duty_type = dutyData.duty_type;
        this.editParams.duty_rate = dutyData.duty_rate;
        this.editParams.vat_rate = dutyData.vat_rate;
        this.editParams.specific_rate = dutyData.specific_rate;
    }
}
```

#### Было (saveEdit):
```javascript
saveEdit() {
    // Валидация (8 строк)
    if (this.isNewCategory && this.isHighway) {
        if (!this.editParams.custom_rate || this.editParams.custom_rate <= 0) {
            alert('...');
            return;
        }
    }
    
    // Очистка параметров (47 строк повторяющегося кода!)
    const cleanParams = { ...this.editParams };
    if (cleanParams.custom_rate !== null && cleanParams.custom_rate !== undefined) {
        cleanParams.custom_rate = parseFloat(cleanParams.custom_rate);
        if (isNaN(cleanParams.custom_rate)) {
            cleanParams.custom_rate = null;
        }
    }
    // ... аналогично для duty_rate, vat_rate, specific_rate
}
```

#### Стало (saveEdit):
```javascript
saveEdit() {
    // Валидация
    const validation = this.validateRouteParams(
        this.editParams, this.routeKey, this.isNewCategory
    );
    if (!validation.isValid) {
        alert(validation.message);
        return;
    }
    
    // Очистка и преобразование
    const cleanParams = this.cleanNumericParams(this.editParams);
    
    this.$emit('save', this.routeKey, cleanParams);
    this.isEditing = false;
}
```

---

## Статистика рефакторинга:

### Файлы:
- ✅ `services/calculation_service.py` (новый) - 242 строки
- ✅ `static/js/v2/RouteEditorMixin.js` (новый) - 175 строк
- ✅ `static/js/v2/RouteEditorV2.js` (рефакторинг) - -69 строк (-20%)
- ✅ `main.py` (упрощение) - `_perform_calculation_and_save` унифицировал POST/PUT
- ✅ `index_v2.html` (обновлен) - подключен RouteEditorMixin

### Результаты:
- 📉 Уменьшение дублирования кода на ~30%
- 🧩 Модульность увеличена
- 🧪 Тестируемость улучшена
- 🛡️ Безопасность повышена (обработка ошибок)
- 📝 Читаемость кода улучшена

---

## 📋 Следующие шаги:

### Этап 3: Оптимизация категорий
- [ ] Единый источник данных для категорий
- [ ] Синхронизация categories.yaml ↔️ DB
- [ ] Кэширование категорий

### Этап 4: Финальное тестирование
- [ ] Тестирование "Новая категория"
- [ ] Тестирование кастомных ставок
- [ ] Тестирование обновления расчетов
- [ ] Проверка миграций БД

---

## 🔧 Как проверить:

1. **Запуск приложения:**
   ```bash
   cd projects/price_calculator
   py main.py
   ```

2. **Открыть V2:**
   ```
   http://localhost:8000/v2
   ```

3. **Тестовые сценарии:**
   - ✅ Создать расчет с "Новая категория"
   - ✅ Редактировать параметры маршрута
   - ✅ Обновить расчет (должен обновляться, а не дублироваться)
   - ✅ Проверить корректность цен в истории

---

## 🎯 Ключевые улучшения:

1. **Сервисный слой** - четкое разделение ответственности
2. **Миксин** - переиспользуемая логика для компонентов
3. **Утилиты** - безопасная работа с данными
4. **Валидация** - централизованная проверка данных
5. **Документация** - понятная структура кода

**Дата завершения:** 10.10.2025






