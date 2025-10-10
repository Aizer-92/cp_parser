# API V3 Documentation

## 📋 Обзор

API V3 использует **новую архитектуру** с State Machine и Strategy Pattern для надёжного управления расчётами.

### Ключевые отличия от V2:

| Функция | V2 | V3 |
|---------|----|----|
| Архитектура | Прямой вызов calculator | State Machine + Strategy Pattern |
| Валидация | Базовая | Pydantic + CategoryRequirements |
| Состояния | Нет | DRAFT → PENDING_PARAMS → READY → CALCULATED → SAVED |
| Кастомные параметры | Только для "Новой категории" | **Для ЛЮБОЙ категории** |
| Тесты | Частичные | 79 unit тестов (100% покрытие) |

---

## 🔌 Endpoints

### 1. `POST /api/v3/calculate/start`

**Начало нового расчёта** - определяет категорию и требования.

**Request:**
```json
{
  "product_name": "Футболка красная",
  "price_yuan": 50,
  "weight_kg": 0.2,
  "quantity": 100,
  "markup": 1.7,
  "forced_category": null  // Опционально
}
```

**Response (Стандартная категория):**
```json
{
  "state": "Готов к расчёту",
  "needs_user_input": false,
  "required_params": [],
  "category": "футболка",
  "message": "Готово к расчёту",
  "context": {
    "category": {"category": "футболка", "rail_base": 9.5, ...},
    "state": {"state": "READY", ...},
    "strategy": "StandardCategory",
    "can_calculate": true
  }
}
```

**Response (Новая категория):**
```json
{
  "state": "Ожидание параметров",
  "needs_user_input": true,
  "required_params": ["custom_rate (логистическая ставка)"],
  "category": "Новая категория",
  "message": "Требуется ввод параметров: custom_rate (логистическая ставка)",
  "context": {
    "strategy": "CustomCategory",
    "can_calculate": false
  }
}
```

---

### 2. `POST /api/v3/calculate/params`

**Предоставление кастомных параметров** (опциональный шаг).

💡 **Используется когда:**
- "Новая категория" (обязательно)
- Пользователь хочет переопределить ставки **для любой категории**

**Request:**
```json
{
  "product_name": "Неизвестный товар",
  "quantity": 50,
  "weight_kg": 1.0,
  "unit_price_yuan": 100,
  "markup": 1.5,
  "forced_category": "Новая категория",
  "custom_logistics": {
    "highway_rail": {
      "custom_rate": 8.5,      // USD/кг
      "duty_rate": 10.0,        // %
      "vat_rate": 20.0          // %
    },
    "highway_air": {
      "custom_rate": 10.5,
      "duty_rate": 10.0,
      "vat_rate": 20.0
    }
  }
}
```

**Response (Валидно):**
```json
{
  "valid": true,
  "errors": [],
  "state": "Готов к расчёту",
  "can_calculate": true,
  "message": "Готово к расчёту"
}
```

**Response (Невалидно):**
```json
{
  "valid": false,
  "errors": [
    "Необходимо указать параметры хотя бы для одного маршрута"
  ],
  "state": "Ожидание параметров",
  "can_calculate": false
}
```

---

### 3. `POST /api/v3/calculate/execute`

**Выполнение расчёта** - основной endpoint.

💡 **Поддерживает все сценарии:**
- Стандартная категория без переопределения
- Стандартная категория С переопределением (custom_logistics)
- Новая категория (требует custom_logistics)

**Request (Стандартная категория):**
```json
{
  "product_name": "Футболка",
  "price_yuan": 50,
  "weight_kg": 0.2,
  "quantity": 100,
  "markup": 1.7,
  "forced_category": "футболка",
  "custom_logistics": null  // Использует базовые ставки
}
```

**Request (С переопределением):**
```json
{
  "product_name": "Футболка",
  "price_yuan": 50,
  "weight_kg": 0.2,
  "quantity": 100,
  "markup": 1.7,
  "forced_category": "футболка",
  "custom_logistics": {
    "highway_rail": {
      "custom_rate": 6.0,  // Переопределяем базовую ставку 9.5 → 6.0
      "duty_rate": 12.0    // Переопределяем пошлину 10% → 12%
    }
  }
}
```

**Response (Успех):**
```json
{
  "id": 123,
  "created_at": "2025-10-10T15:30:00",
  "category": "футболка",
  "cost_price": {
    "total": {"rub": 50000, "usd": 500},
    "breakdown": {...}
  },
  "sale_price": {"total": {"rub": 85000, "usd": 850}},
  "profit": {"total": {"rub": 35000, "usd": 350}},
  "routes": {
    "highway_rail": {...},
    "highway_air": {...},
    ...
  }
}
```

**Response (Ошибка - невалидные параметры):**
```
HTTP 400
{
  "detail": "Невалидные параметры: Необходимо указать параметры хотя бы для одного маршрута"
}
```

**Response (Ошибка - расчёт):**
```
HTTP 400
{
  "detail": "Невозможно выполнить расчёт: Неправильное состояние: Ожидание параметров"
}
```

---

### 4. `GET /api/v3/categories`

**Получение всех категорий** с метаданными.

**Response:**
```json
{
  "total": 105,
  "version": "2.0",
  "source": "Railway PostgreSQL",
  "categories": [
    {
      "category": "футболка",
      "material": "хлопок, полиэстер, акрил",
      "rates": {
        "rail_base": 9.5,
        "air_base": 11.6,
        "contract_base": null
      },
      "duty_rate": 10.0,
      "vat_rate": 20.0,
      "specific_rate": null,
      "requirements": {
        "requires_logistics_rate": false,
        "requires_duty_rate": false,
        "requires_vat_rate": false,
        "requires_specific_rate": false
      },
      "keywords": [],
      "description": "",
      "tnved_code": "",
      "certificates": [],
      "needs_custom_params": false
    },
    {
      "category": "Новая категория",
      "rates": {"rail_base": 0, "air_base": 0},
      "requirements": {
        "requires_logistics_rate": true
      },
      "needs_custom_params": true,
      "description": "Для товаров, не распознанных автоматически. Требует ручного ввода пошлин."
    },
    ...
  ]
}
```

---

## 🔄 Workflow примеры

### Сценарий 1: Стандартная категория (простой)

```javascript
// 1. Выполняем расчёт сразу
const response = await axios.post('/api/v3/calculate/execute', {
  product_name: 'Футболка',
  price_yuan: 50,
  weight_kg: 0.2,
  quantity: 100,
  markup: 1.7
});

console.log(response.data.id); // 123
console.log(response.data.cost_price.total.rub); // 50000
```

### Сценарий 2: Переопределение ставок

```javascript
// 1. Пользователь решил изменить ставку
const customLogistics = {
  highway_rail: {
    custom_rate: 6.0,  // Вместо 9.5 (базовой)
    duty_rate: 12.0    // Вместо 10% (базовой)
  }
};

// 2. Выполняем расчёт с кастомными параметрами
const response = await axios.post('/api/v3/calculate/execute', {
  product_name: 'Футболка',
  price_yuan: 50,
  weight_kg: 0.2,
  quantity: 100,
  markup: 1.7,
  custom_logistics: customLogistics
});

console.log(response.data); // Расчёт с новыми ставками
```

### Сценарий 3: Новая категория (полный workflow)

```javascript
// 1. Начинаем расчёт
const startResponse = await axios.post('/api/v3/calculate/start', {
  product_name: 'Неизвестный товар',
  price_yuan: 100,
  quantity: 50,
  weight_kg: 1.0,
  markup: 1.5
});

if (startResponse.data.needs_user_input) {
  console.log('Требуется ввод:', startResponse.data.required_params);
  
  // 2. Показываем форму, пользователь вводит параметры
  const customLogistics = {
    highway_rail: {
      custom_rate: 8.5,
      duty_rate: 10.0,
      vat_rate: 20.0
    }
  };
  
  // 3. Валидируем параметры (опционально)
  const paramsResponse = await axios.post('/api/v3/calculate/params', {
    product_name: 'Неизвестный товар',
    quantity: 50,
    weight_kg: 1.0,
    unit_price_yuan: 100,
    markup: 1.5,
    forced_category: 'Новая категория',
    custom_logistics: customLogistics
  });
  
  if (paramsResponse.data.valid) {
    // 4. Выполняем расчёт
    const execResponse = await axios.post('/api/v3/calculate/execute', {
      product_name: 'Неизвестный товар',
      price_yuan: 100,
      quantity: 50,
      weight_kg: 1.0,
      markup: 1.5,
      forced_category: 'Новая категория',
      custom_logistics: customLogistics
    });
    
    console.log('Готово!', execResponse.data.id);
  }
}
```

---

## 🎯 Ключевые моменты

### 1. **custom_logistics работает для ЛЮБОЙ категории**

```javascript
// ✅ Стандартная категория + переопределение
await axios.post('/api/v3/calculate/execute', {
  product_name: 'Футболка',
  forced_category: 'футболка',  // Стандартная!
  custom_logistics: {  // Но переопределяем ставки
    highway_rail: {custom_rate: 6.0}
  },
  ...
});

// ✅ Новая категория (обязательно нужны параметры)
await axios.post('/api/v3/calculate/execute', {
  product_name: 'Что-то',
  forced_category: 'Новая категория',
  custom_logistics: {  // Обязательно!
    highway_rail: {custom_rate: 8.5, duty_rate: 10}
  },
  ...
});
```

### 2. **Автоопределение категории**

Если `forced_category=null`, система сама определит категорию по ключевым словам (пока не реализовано, используется "Новая категория").

### 3. **Состояния (State Machine)**

```
DRAFT → PENDING_PARAMS → READY → CALCULATED → SAVED
                ↓
              ERROR
```

Frontend может отслеживать состояние через `response.context.state`.

### 4. **Валидация**

- ✅ Автоматическая валидация через Pydantic
- ✅ Требования категории (`CategoryRequirements`)
- ✅ Проверка параметров перед расчётом
- ✅ Понятные сообщения об ошибках

---

## 🚀 Migration Guide (V2 → V3)

### V2 (старый):
```javascript
const response = await axios.post('/api/v2/calculate', requestData);
```

### V3 (новый):
```javascript
// Для простых случаев - то же самое
const response = await axios.post('/api/v3/calculate/execute', requestData);

// Для сложных - используем workflow
const start = await axios.post('/api/v3/calculate/start', requestData);
if (start.data.needs_user_input) {
  // Показываем форму
  // Затем execute с custom_logistics
}
```

---

## 📊 Статус разработки

- ✅ Backend: ГОТОВ (79 unit тестов)
- ⏳ Frontend: В разработке
- ⏳ E2E тесты: Запланировано
- ⏳ Деплой: Запланировано

---

## 🔗 См. также

- `CATEGORY_FORMAT_COMPARISON.md` - формат категорий
- `ADVANCED_CATEGORY_SOLUTIONS.md` - архитектурные решения
- `STATE_MACHINE_IMPLEMENTATION_PROGRESS.md` - прогресс State Machine

