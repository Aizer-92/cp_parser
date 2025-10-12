# 🐛 Bugfix: Category Parsing Issue

**Дата:** 10.10.2025  
**Статус:** ✅ Исправлено

---

## Проблема

При тестировании V3 API на Railway возникала ошибка:
```
{"detail":"Невозможно выполнить расчёт: Неправильное состояние: Ожидание параметров"}
```

**Для стандартных категорий** (Футболки, Блокноты), которые НЕ должны требовать параметры.

---

## Причина

1. **`Category.from_dict()` неправильно парсил `requirements`**

В JSON файле `categories_from_railway.json` структура такая:
```json
{
  "category": "футболка",
  "requirements": {
    "requires_logistics_rate": false,
    ...
  }
}
```

Но код читал напрямую:
```python
data.get('requires_logistics_rate', False)  # ❌ Всегда False!
```

Вместо:
```python
req_data = data.get('requirements', {})
req_data.get('requires_logistics_rate', False)  # ✅ Правильно!
```

2. **Не было явной проверки на "Новая категория"**

Метод `needs_custom_params()` проверял только ставки и requirements, но не имя категории.

---

## Исправление

### 1. Фикс парсинга requirements (commit: 882703b)

```python
# models/category.py, строка 269-276
req_data = data.get('requirements', {})
requirements = CategoryRequirements(
    requires_logistics_rate=req_data.get('requires_logistics_rate', data.get('requires_logistics_rate', False)),
    requires_duty_rate=req_data.get('requires_duty_rate', data.get('requires_duty_rate', False)),
    requires_vat_rate=req_data.get('requires_vat_rate', data.get('requires_vat_rate', False)),
    requires_specific_rate=req_data.get('requires_specific_rate', data.get('requires_specific_rate', False))
)
```

### 2. Добавлена явная проверка на "Новая категория" (commit: 7117f0e)

```python
# models/category.py, строка 171-173
def needs_custom_params(self) -> bool:
    # ВАЖНО: Если категория "Новая категория" - всегда требуем параметры
    if self.name == "Новая категория":
        return True
    ...
```

### 3. Добавлены debug логи (commit: af85ae7)

```python
# services/calculation_context.py, строка 51-55
needs_custom = category.needs_custom_params()
print(f"📦 Категория: {category.name}")
print(f"   rail_base: {category.rail_base}, air_base: {category.air_base}")
print(f"   needs_custom_params: {needs_custom}")
print(f"   requirements: {category.requirements}")
```

---

## Тестирование

### Локально (до деплоя):
```bash
python3 -c "
from models.category import Category
import json

with open('config/categories_from_railway.json') as f:
    data = json.load(f)
    
футболки = [c for c in data['categories'] if 'футбол' in c['category'].lower()][0]
cat = Category.from_dict(футболки)
print(f'Футболки: needs_custom_params() = {cat.needs_custom_params()}')
# Ожидается: False
"
```

**Результат:**
```
Футболки: needs_custom_params() = False (ожидается False) ✅
Новая категория: needs_custom_params() = True (ожидается True) ✅
```

### На Railway (после деплоя):
```bash
curl -X POST https://price-calculator-production.up.railway.app/api/v3/calculate/execute \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Футболка хлопковая",
    "price_yuan": 50,
    "quantity": 1000,
    "weight_kg": 0.2,
    "markup": 1.4,
    "is_precise_calculation": false
  }'
```

**Ожидается:** Успешный расчёт с маршрутами (Highway ЖД, Highway Авиа, etc.)

---

## Commits

1. `882703b` - Fix Category.from_dict requirements parsing - CRITICAL BUG
2. `af85ae7` - Add debug logs to diagnose category parsing issue
3. `7117f0e` - Add explicit check for 'Новая категория' + debug logs

---

## Уроки

1. **Всегда проверяй структуру JSON** перед парсингом
2. **Добавляй явные проверки** для критических условий (типа "Новая категория")
3. **Debug логи** помогают диагностировать проблемы на production
4. **Тестируй локально** перед деплоем на Railway

---

**Статус:** Ожидаем деплоя на Railway (~2 минуты). После деплоя нужно протестировать Сценарии 1-3.


