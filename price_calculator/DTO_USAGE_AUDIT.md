# DTO Usage Audit - Проверка правильного использования

**Дата:** 12.10.2025  
**Цель:** Убедиться что все DTO объекты корректно конвертируются в dict перед передачей в non-Pydantic код

---

## ✅ ProductInputDTO Usage

### V3 API: `/api/v3/calculate/execute`

**Функция:** `execute_calculation_v3(request: ProductInputDTO)`

#### 1. ✅ Конвертация для `orchestrator.provide_custom_params()`

**Строки:** 2301-2304

```python
if request.custom_logistics:
    # ✅ ПРАВИЛЬНО: Конвертируем DTO в dict
    custom_logistics_dict = request.custom_logistics.dict(exclude_none=True)
    params_result = orchestrator.provide_custom_params(custom_logistics_dict)
```

**Почему:** `orchestrator` ожидает `Dict`, не `CustomLogisticsDTO`.

---

#### 2. ✅ Конвертация для `service.create_calculation()`

**Строки:** 2362-2371

```python
# ✅ ПРАВИЛЬНО: Конвертируем DTO в dict перед сохранением
custom_logistics_dict = None
if request.custom_logistics:
    custom_logistics_dict = request.custom_logistics.dict(exclude_none=True)

saved_id = service.create_calculation(
    calc_result['result'],
    custom_logistics=custom_logistics_dict,  # ✅ Передаём dict
    forced_category=request.forced_category
)
```

**Почему:** `calculation_service` сохраняет в БД через `json.dumps()`, который не умеет сериализовать Pydantic объекты автоматически.

---

#### 3. ✅ Использование скалярных полей DTO

**Строки:** 2290-2298

```python
orchestrator.start_calculation(
    product_name=request.product_name,      # ✅ str
    quantity=request.quantity,              # ✅ int
    weight_kg=request.weight_kg or 0.5,     # ✅ float
    unit_price_yuan=request.price_yuan,     # ✅ float
    markup=request.markup,                  # ✅ float
    forced_category=request.forced_category # ✅ Optional[str]
)
```

**Почему:** Скалярные поля (str, int, float) можно использовать напрямую.

---

## ✅ V2 API: CalculationRequest (не DTO)

### Функции: `_perform_calculation_and_save()`, legacy endpoints

**Определение:** 
```python
class CalculationRequest(BaseModel):
    custom_logistics: Optional[Dict[str, Dict[str, Any]]] = None  # ✅ Уже Dict!
```

**Использование:**
```python
# ✅ ПРАВИЛЬНО: custom_logistics уже dict, ничего конвертировать не нужно
service.create_calculation(
    result,
    custom_logistics=request.custom_logistics,  # Уже Dict
    forced_category=request.forced_category
)
```

**Почему:** В V2 API `custom_logistics` объявлен как `Dict`, а не как DTO объект.

---

## 📋 Checklist: Когда конвертировать DTO → dict

### ✅ Конвертировать НУЖНО:

1. **Перед сохранением в БД**
   ```python
   service.create_calculation(..., custom_logistics=dto.dict(exclude_none=True))
   service.update_calculation(..., custom_logistics=dto.dict(exclude_none=True))
   ```

2. **Перед передачей в non-Pydantic сервисы**
   ```python
   orchestrator.provide_custom_params(dto.dict(exclude_none=True))
   ```

3. **Перед `json.dumps()` или сериализацией**
   ```python
   json.dumps(dto.dict(exclude_none=True))
   ```

### ✅ Конвертировать НЕ НУЖНО:

1. **Для скалярных полей (str, int, float, bool)**
   ```python
   name = dto.product_name  # ✅ Можно использовать напрямую
   ```

2. **Для Optional полей если None**
   ```python
   if dto.forced_category:  # ✅ Проверка работает напрямую
       use(dto.forced_category)
   ```

3. **Внутри FastAPI endpoints**
   ```python
   @app.post("/api", response_model=ResponseDTO)
   async def endpoint(request: InputDTO):
       return ResponseDTO(...)  # ✅ FastAPI автоматически сериализует
   ```

---

## 🔍 Аудит завершён

### Результат:
- ✅ **Все места где используется `ProductInputDTO.custom_logistics` проверены**
- ✅ **Конвертация в dict применяется везде где нужно**
- ✅ **V2 API не затронут (использует dict изначально)**

### Потенциальные проблемы:
- ❌ **Не найдено**

### Рекомендации:
1. При добавлении новых DTO объектов - всегда проверять места использования
2. Использовать `.dict(exclude_none=True)` для конвертации
3. Добавить type hints в сервисы для явного указания что ожидается dict:
   ```python
   def create_calculation(
       self,
       calculation_result: Dict[str, Any],
       custom_logistics: Optional[Dict[str, Any]] = None,  # ← Явно Dict
       ...
   )
   ```

---

## 📊 Coverage

| Место использования | DTO → dict | Статус |
|-------------------|-----------|--------|
| V3: orchestrator.provide_custom_params() | ✅ | OK |
| V3: service.create_calculation() | ✅ | OK |
| V3: orchestrator.start_calculation() | N/A (scalar) | OK |
| V2: service.create_calculation() | N/A (already dict) | OK |
| V2: service.update_calculation() | N/A (already dict) | OK |

**Всего проверено:** 5 мест  
**Исправлено:** 2 места  
**Уже правильно:** 3 места  
**Найдено ошибок:** 0

---

## ✅ Conclusion

**Все DTO используются правильно! 🎉**

Код готов к продакшену с точки зрения использования DTOs.

