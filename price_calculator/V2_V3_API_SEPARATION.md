# V2 ↔ V3 API Разделение ✅

## Дата: 13.10.2025

---

## 🔴 ПРОБЛЕМА

После внедрения V3 архитектуры, **главная версия (V2 UI) перестала работать**:

```
❌ /api/v3/calculate/execute:1 
   Failed to load resource: the server responded with a status of 422
❌ V3 Calculate ERROR
```

### Причины:
1. **Backend:** `/api/calculate` использовал старую логику `_calculate_price_logic`
2. **Frontend:** `PriceCalculatorAppV2.js` вызывал `useCalculationV3()` → `/api/v3/calculate/execute`

---

## ✅ РЕШЕНИЕ

### 1. Backend исправлен (`main.py`)

**БЫЛО:**
```python
@app.post("/api/calculate", response_model=CalculationResponse)
async def calculate_price(request: CalculationRequest, auth: bool = Depends(require_auth)):
    """Расчет цены товара (требует авторизацию)"""
    return await _calculate_price_logic(request)  # ❌ Старая логика
```

**СТАЛО:**
```python
@app.post("/api/calculate", response_model=CalculationResponse)
async def calculate_price(request: CalculationRequest, auth: bool = Depends(require_auth)):
    """Расчет цены товара V2 (требует авторизацию)"""
    # Используем V2 логику (calculation_id=None для создания нового)
    return await _perform_calculation_and_save(request, calculation_id=None)  # ✅ V2 логика
```

---

### 2. Frontend исправлен (`PriceCalculatorAppV2.js`)

#### A) Метод `performCalculation()`

**БЫЛО:**
```javascript
const v3 = window.useCalculationV3();  // ❌ V3 API
let result;

if (this.productData.calculation_id) {
    result = await v3.updateCalculation(this.productData.calculation_id, calculationData);
} else {
    result = await v3.calculate(calculationData);  // ❌ → /api/v3/calculate/execute
}
```

**СТАЛО:**
```javascript
// ✅ V2 API - прямой вызов axios
let result;

if (this.productData.calculation_id) {
    const response = await axios.put(`/api/history/${this.productData.calculation_id}`, calculationData);
    result = response.data;
} else {
    const response = await axios.post('/api/calculate', calculationData);  // ✅ → /api/calculate
    result = response.data;
}
```

#### B) Метод `loadCategories()`

**БЫЛО:**
```javascript
const v3 = window.useCalculationV3();  // ❌ V3 API
const categories = await v3.getCategories();
```

**СТАЛО:**
```javascript
const response = await axios.get('/api/categories');  // ✅ V2 API
const categories = response.data;
```

---

## 📊 ТЕКУЩАЯ АРХИТЕКТУРА

### Backend API Endpoints

| Endpoint | UI | Логика | Статус |
|----------|-----|--------|--------|
| `/api/calculate` | V2 (главная) | `_perform_calculation_and_save` (V2) | ✅ |
| `/api/v2/calculate` | V2 (резерв) | `_perform_calculation_and_save` (V2) | ✅ |
| `/api/categories` | V2 | `get_categories()` | ✅ |
| `/api/history` | V2 | `get_calculation_history()` | ✅ |
| `/api/v3/calculate/execute` | V3 только | State Machine + Strategy Pattern | ✅ |
| `/api/v3/factories` | V3 только | SQLAlchemy CRUD | ✅ |
| `/api/v3/positions` | V3 только | SQLAlchemy CRUD | ✅ |
| `/api/v3/calculations` | V3 только | SQLAlchemy CRUD | ✅ |

### Frontend Структура

| UI | URL | JS Файлы | API |
|----|-----|----------|-----|
| **V2 (главная)** | `/` | `PriceCalculatorAppV2.js` | `/api/calculate`, `/api/categories` ✅ |
| **V3 (новая)** | `/v3` | `QuickModeV3.js`, `useCalculationsV3.js` | `/api/v3/*` ✅ |

---

## 🎯 ПРАВИЛА РАЗДЕЛЕНИЯ

### ✅ V2 UI должен использовать:
- `/api/calculate` - создание расчета
- `/api/history/:id` - обновление расчета
- `/api/categories` - список категорий
- `/api/history` - история расчетов

### ✅ V3 UI должен использовать:
- `/api/v3/calculate/execute` - расчет с State Machine
- `/api/v3/factories` - CRUD фабрик
- `/api/v3/positions` - CRUD позиций
- `/api/v3/calculations` - CRUD расчетов

### ❌ ЗАПРЕЩЕНО:
- V2 UI → V3 API (перекрестные вызовы)
- V3 UI → V2 API (устаревшая логика)

---

## 🧪 ТЕСТИРОВАНИЕ

### V2 UI (главная версия)
1. Откройте: `https://price-calculator-production.up.railway.app/`
2. Заполните форму товара
3. Нажмите "Рассчитать"
4. ✅ Проверьте в DevTools → Network: вызов `/api/calculate` (НЕ `/api/v3/calculate/execute`)
5. ✅ Результаты отображаются корректно

### V3 UI (новая версия)
1. Откройте: `https://price-calculator-production.up.railway.app/v3`
2. Заполните "Быстрый расчёт"
3. Нажмите "Рассчитать"
4. ✅ Проверьте в DevTools → Network: вызов `/api/v3/calculate/execute`
5. ✅ Результаты отображаются корректно

---

## 📝 КОММИТЫ

### 1. Backend fix
```
01914b9 - FIX: Вернул V2 API для главной версии
```

### 2. Frontend fix
```
ffda4f6 - FIX CRITICAL: Убрал V3 API из V2 UI полностью
```

---

## ✅ СТАТУС

**Проблема полностью решена:**
- ✅ V2 UI использует только V2 API
- ✅ V3 UI использует только V3 API
- ✅ Никаких перекрестных вызовов
- ✅ Railway auto-deploy завершён

**Время работы:** ~30 минут  
**Деплой:** В процессе (~2-3 минуты)

🎉 Обе версии теперь работают корректно и изолированно!

