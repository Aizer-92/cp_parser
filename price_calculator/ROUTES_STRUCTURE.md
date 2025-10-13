# 🚚 Структура маршрутов логистики

## 📊 Текущие маршруты (4 шт)

### 1. **highway_rail** - Highway ЖД
```python
routes["highway_rail"] = {
    "name": "Highway ЖД",
    "delivery_days": 25,
    
    # Основные поля (новый формат)
    "cost_rub": 123456.78,      # Общая себестоимость в рублях
    "cost_usd": 1234.56,        # Общая себестоимость в долларах
    "per_unit": 123.45,         # Себестоимость за 1 шт в рублях
    "sale_rub": 234567.89,      # Продажная цена общая (с наценкой)
    "sale_usd": 2345.67,        # Продажная цена в долларах
    "sale_per_unit": 234.56,    # Продажная за 1 шт
    
    # Совместимость (старые поля, дублируют новые)
    "cost_per_unit_rub": 123.45,
    "cost_per_unit_usd": 1.23,
    "total_cost_rub": 123456.78,
    "total_cost_usd": 1234.56,
    "sale_per_unit_rub": 234.56,
    "sale_total_rub": 234567.89,
    
    # Логистика
    "logistics_rate_usd": 5.8,           # Итоговая ставка $/кг
    "base_rate_usd": 3.7,                # Базовая ставка $/кг
    "density_surcharge_usd": 2.1,        # Надбавка за плотность $/кг
    "has_density_surcharge": True,       # Есть ли надбавка
    
    # Детальная структура затрат
    "breakdown": {
        # Стоимость в Китае
        "base_price_yuan": 100.0,
        "base_price_rub": 1300.0,
        "toni_commission_pct": 5.0,
        "toni_commission_rub": 65.0,
        "transfer_commission_pct": 18.0,
        "transfer_commission_rub": 234.0,
        "factory_price": 1599.0,         # С комиссиями
        "local_delivery": 50.0,
        
        # Логистика
        "logistics": 580.0,              # На 1 шт
        "logistics_rate": 5.8,
        "base_rate": 3.7,
        "density_surcharge": 2.1,
        "weight_kg": 1.0,
        "total_weight_kg": 1000.0,
        
        # Прочие
        "msk_pickup": 1.0,               # 1000₽ / кол-во
        "other_costs": 50.0              # 2.5% от себестоимости
    }
}
```

**Формула расчета:**
```python
# 1. Стоимость в Китае
goods_cost = price_yuan * yuan_to_rub * (1 + 0.05 + 0.18)

# 2. Логистика
logistics_rate = base_rate + density_surcharge  # $/кг
logistics_cost = weight_kg * logistics_rate * usd_to_rub * quantity

# 3. Прочие
local_delivery = 130₽ * quantity
msk_pickup = 1000₽
other_costs = (goods + logistics + local_delivery) * 0.025

# 4. Итого
cost_per_unit = (goods_cost + logistics_cost + local_delivery + msk_pickup + other_costs) / quantity
```

---

### 2. **highway_air** - Highway Авиа
Структура **идентична** `highway_rail`, но:
- `delivery_days: 15` (быстрее)
- `base_rate_usd: base_rail + 2.1` (дороже на $2.1/кг)

**Отличия:**
```python
air_base_rate = rail_base_rate + 2.1  # 3.7 + 2.1 = 5.8 $/кг
```

---

### 3. **highway_contract** - Highway под контракт
```python
routes["highway_contract"] = {
    "name": "Highway под контракт",
    "delivery_days": 25,
    
    # Основные поля (аналогично highway_rail)
    "cost_rub": ...,
    "cost_usd": ...,
    "per_unit": ...,
    "sale_rub": ...,
    "sale_usd": ...,
    "sale_per_unit": ...,
    
    # Логистика
    "logistics_rate_usd": 3.4,           # Фиксированная ставка
    "base_rate_usd": 3.4,
    "density_surcharge_usd": 2.1,        # Надбавка за плотность
    "fixed_cost_rub": 25000.0,           # ⚠️ УНИКАЛЬНО: Фиксированные расходы
    
    "breakdown": {
        # ⚠️ ОТЛИЧИЕ: БЕЗ комиссии за перевод (18%)
        "transfer_commission_pct": 0.0,
        "transfer_commission_rub": 0.0,
        
        # ⚠️ ДОБАВЛЕНО: Пошлины + НДС
        "customs_duty_rub": 1500.0,      # По категории товара
        "vat_rub": 3000.0,               # НДС 20%
        "customs_total_rub": 4500.0,
        
        # ⚠️ ДОБАВЛЕНО: Фиксированные расходы
        "fixed_costs_rub": 25000.0       # Разовый платеж
    }
}
```

**Формула расчета:**
```python
# 1. Стоимость в Китае (БЕЗ 18% комиссии)
goods_cost = price_yuan * yuan_to_rub * (1 + 0.05)

# 2. Логистика
logistics_rate = 3.4 + density_surcharge  # $/кг
logistics_cost = weight_kg * logistics_rate * usd_to_rub * quantity

# 3. Пошлины + НДС (по категории)
customs_duty = goods_cost * duty_rate  # Из categories.yaml
vat = (goods_cost + logistics_cost + customs_duty) * 0.20

# 4. Прочие
local_delivery = 130₽ * quantity
msk_pickup = 1000₽
other_costs = (goods + logistics + local + customs + vat) * 0.025
fixed_costs = 25000₽  # ⚠️ Разовый платеж

# 5. Итого
cost_per_unit = (goods_cost + logistics_cost + local_delivery + 
                 customs_duty + vat + msk_pickup + other_costs + fixed_costs) / quantity
```

---

### 4. **prologix** - Prologix (по кубометрам)
```python
routes["prologix"] = {
    "name": "Prologix",
    "delivery_days": 30,  # Среднее из диапазона
    
    # Основные поля (аналогично highway_rail)
    "cost_rub": ...,
    "cost_usd": ...,
    "per_unit": ...,
    "sale_rub": ...,
    "sale_usd": ...,
    "sale_per_unit": ...,
    
    # ⚠️ УНИКАЛЬНЫЕ ПОЛЯ: Расчет по объему
    "rate_rub_per_m3": 20000.0,          # Ставка за 1 м³
    "total_volume_m3": 15.5,             # Общий объем груза
    "logistics_cost_rub": 310000.0,      # Логистика = volume × rate
    "fixed_cost_rub": 25000.0,           # Фиксированные расходы
    
    "breakdown": {
        # Стоимость в Китае (БЕЗ 18% комиссии)
        "transfer_commission_pct": 0.0,
        "transfer_commission_rub": 0.0,
        
        # ⚠️ УНИКАЛЬНО: Расчет по объему
        "prologix_rate": 20000.0,        # ₽/м³
        "total_volume_m3": 15.5,
        "packing_box_volume_m3": 0.155,  # Объем 1 коробки
        "boxes_count": 100,
        
        # ⚠️ ДОБАВЛЕНО: Пошлины + НДС
        "customs_duty_rub": 1500.0,
        "vat_rub": 3000.0,
        "customs_total_rub": 4500.0,
        
        # ⚠️ ДОБАВЛЕНО: Фиксированные расходы
        "fixed_costs_rub": 25000.0
    }
}
```

**Формула расчета:**
```python
# 1. Стоимость в Китае (БЕЗ 18% комиссии)
goods_cost = price_yuan * yuan_to_rub * (1 + 0.05)

# 2. Логистика (по объему!)
box_volume = length * width * height / 1_000_000  # м³
total_volume = box_volume * (quantity / units_per_box)

# Тарифы по объему
if total_volume <= 2:      rate = 41000  # ₽/м³
elif total_volume <= 8:    rate = 20000
elif total_volume <= 20:   rate = 15000
elif total_volume <= 30:   rate = 13000
else:                      rate = 13000

logistics_cost = total_volume * rate

# 3. Пошлины + НДС (по категории)
customs_duty = goods_cost * duty_rate
vat = (goods_cost + logistics_cost + customs_duty) * 0.20

# 4. Прочие
local_delivery = 130₽ * quantity
msk_pickup = 1000₽
other_costs = (goods + logistics + local + customs + vat) * 0.025
fixed_costs = 25000₽

# 5. Итого
cost_per_unit = (goods_cost + logistics_cost + local_delivery + 
                 customs_duty + vat + msk_pickup + other_costs + fixed_costs) / quantity
```

**Тарифы Prologix:**
```python
def get_prologix_rate(volume_m3):
    if volume_m3 <= 2:    return 41000
    if volume_m3 <= 8:    return 20000
    if volume_m3 <= 20:   return 15000
    if volume_m3 <= 30:   return 13000
    return 13000
```

---

## 🆕 Как добавить новый маршрут

### Пример: Добавление **Карго** и **Контейнер**

#### 1️⃣ Определи параметры маршрута

**Карго:**
- Ключ: `cargo`
- Название: "Карго"
- Доставка: 20 дней
- Логистика: $4.2/кг + надбавка за плотность
- Комиссия за перевод: 18% (как ЖД)
- Пошлины: НЕТ (как ЖД)

**Контейнер:**
- Ключ: `container`
- Название: "Контейнер 20 футов"
- Доставка: 35 дней
- Логистика: $2.8/кг + надбавка за плотность
- Комиссия за перевод: 0% (как контракт)
- Пошлины: ДА (как контракт)
- Фиксированные расходы: 80000₽ (аренда контейнера)

---

#### 2️⃣ Добавь расчет в `price_calculator.py`

**Для Карго (похож на Highway ЖД):**

```python
# В методе calculate_cost(), после highway_air (строка ~1054)

# 5. Карго (аналогично Highway ЖД, но другая ставка)
cargo_base_rate = 4.2  # $/кг
cargo_density_surcharge = self.get_density_surcharge(density_kg_m3, 'cargo') if density_kg_m3 else 0
cargo_total_rate = cargo_base_rate + cargo_density_surcharge
cargo_logistics_cost_rub = weight_kg * cargo_total_rate * self.currencies["usd_to_rub"] * quantity

# Используем те же компоненты что и ЖД (с 18% комиссией)
cargo_cost_per_unit_rub = (goods_cost_per_unit_rub + 
                           (cargo_logistics_cost_rub / quantity) + 
                           local_delivery_per_unit_rub +
                           msk_pickup_per_unit_rub + 
                           other_costs_per_unit_rub)
cargo_total_cost_rub = cargo_cost_per_unit_rub * quantity

routes["cargo"] = {
    "name": "Карго",
    "delivery_days": 20,
    "cost_rub": round(cargo_total_cost_rub, 2),
    "cost_usd": round(cargo_total_cost_rub / self.currencies["usd_to_rub"], 2),
    "per_unit": round(cargo_cost_per_unit_rub, 2),
    "sale_rub": round(cargo_total_cost_rub * markup, 2),
    "sale_usd": round((cargo_total_cost_rub * markup) / self.currencies["usd_to_rub"], 2),
    "sale_per_unit": round(cargo_cost_per_unit_rub * markup, 2),
    # Старые поля
    "cost_per_unit_rub": round(cargo_cost_per_unit_rub, 2),
    "cost_per_unit_usd": round(cargo_cost_per_unit_rub / self.currencies["usd_to_rub"], 2),
    "total_cost_rub": round(cargo_total_cost_rub, 2),
    "total_cost_usd": round(cargo_total_cost_rub / self.currencies["usd_to_rub"], 2),
    "sale_per_unit_rub": round(cargo_cost_per_unit_rub * markup, 2),
    "sale_total_rub": round(cargo_total_cost_rub * markup, 2),
    "logistics_rate_usd": round(cargo_total_rate, 2),
    "base_rate_usd": round(cargo_base_rate, 2),
    "density_surcharge_usd": round(cargo_density_surcharge, 2) if cargo_density_surcharge else 0,
    "has_density_surcharge": cargo_density_surcharge > 0,
    # Детальная структура (аналогично ЖД)
    "breakdown": {
        "base_price_yuan": round(price_yuan, 2),
        "base_price_rub": round(price_yuan * self.currencies["yuan_to_rub"], 2),
        "toni_commission_pct": commission_percent,
        "toni_commission_rub": round((price_yuan * self.currencies["yuan_to_rub"]) * (commission_percent / 100), 2),
        "transfer_commission_pct": transfer_percent,
        "transfer_commission_rub": round(goods_cost_per_unit_rub - (price_yuan * self.currencies["yuan_to_rub"]) * (1 + commission_percent / 100), 2),
        "factory_price": round(goods_cost_per_unit_rub, 2),
        "local_delivery": round(local_delivery_per_unit_rub, 2),
        "logistics": round(cargo_logistics_cost_rub / quantity, 2),
        "logistics_rate": round(cargo_total_rate, 2),
        "base_rate": round(cargo_base_rate, 2),
        "density_surcharge": round(cargo_density_surcharge, 2) if cargo_density_surcharge else 0,
        "weight_kg": weight_kg,
        "total_weight_kg": round(weight_kg * quantity, 2),
        "msk_pickup": round(msk_pickup_per_unit_rub, 2),
        "other_costs": round(other_costs_per_unit_rub, 2)
    }
}
```

**Для Контейнера (похож на Highway Контракт):**

```python
# 6. Контейнер (аналогично контракту, но с фиксированной стоимостью контейнера)

# Рассчитываем контейнер (используем функцию calculate_highway_contract_cost)
container_data = self.calculate_highway_contract_cost(
    price_yuan=price_yuan,
    weight_kg=weight_kg,
    quantity=quantity,
    category=category,
    density_kg_m3=density_kg_m3,
    markup=markup,
    # Переопределяем параметры для контейнера
    base_rate=2.8,                    # Контейнер дешевле
    fixed_cost_rub=80000,             # Аренда контейнера 20 футов
    custom_logistics_params=custom_logistics_params
)

# Модифицируем данные
container_cost_unit = container_data["per_unit"]["rub"]
container_cost_total = container_data["total"]["rub"]

routes["container"] = {
    "name": "Контейнер 20 футов",
    "delivery_days": 35,
    "cost_rub": container_cost_total,
    "cost_usd": container_data["total"]["usd"],
    "per_unit": container_cost_unit,
    "sale_rub": round(container_cost_total * markup, 2),
    "sale_usd": round(container_data["total"]["usd"] * markup, 2),
    "sale_per_unit": round(container_cost_unit * markup, 2),
    # Старые поля
    "cost_per_unit_rub": container_cost_unit,
    "cost_per_unit_usd": container_data["per_unit"]["usd"],
    "total_cost_rub": container_cost_total,
    "total_cost_usd": container_data["total"]["usd"],
    "sale_per_unit_rub": round(container_cost_unit * markup, 2),
    "sale_total_rub": round(container_cost_total * markup, 2),
    "logistics_rate_usd": 2.8,
    "base_rate_usd": 2.8,
    "density_surcharge_usd": container_data["density_surcharge_usd"],
    "fixed_cost_rub": 80000.0,        # ⚠️ Аренда контейнера
    "has_density_surcharge": container_data["density_surcharge_usd"] > 0,
    # Детальная структура
    "breakdown": container_data["breakdown"]
}
```

---

#### 3️⃣ Обнови настройки плотности (если нужно)

Если новый маршрут использует **другие пороги плотности**, обнови `config/settings.yaml`:

```yaml
density_thresholds:
  rail:
    - threshold: 167  # кг/м³
      surcharge: 0.8  # $/кг
    - threshold: 100
      surcharge: 1.8
    - threshold: 80
      surcharge: 2.7
  
  air:
    - threshold: 167
      surcharge: 1.0
    - threshold: 100
      surcharge: 2.1
    - threshold: 80
      surcharge: 3.2
  
  cargo:  # ⚠️ НОВОЕ
    - threshold: 150  # Другие пороги
      surcharge: 1.2
    - threshold: 90
      surcharge: 2.5
    - threshold: 70
      surcharge: 3.5
```

---

#### 4️⃣ Frontend не требует изменений! ✅

Благодаря **унифицированной структуре `routes`**, frontend автоматически отобразит новые маршруты:

- `RouteEditorV2.js` - редактирование ставок
- `PriceCalculatorAppV2.js` - сравнение маршрутов
- `HistoryPanelV2.js` - история расчетов

**Единственное исключение:**  
Если у маршрута есть **уникальные поля** (например, `container_size: "20ft"`), их нужно добавить в `RouteEditorV2.js` для редактирования.

---

## 📋 Чек-лист добавления маршрута

- [ ] 1. Определены параметры маршрута (название, ключ, дни доставки)
- [ ] 2. Определена формула расчета логистики ($/кг, ₽/м³, фиксированная)
- [ ] 3. Определены комиссии (18% перевода, пошлины, НДС)
- [ ] 4. Определены фиксированные расходы (если есть)
- [ ] 5. Добавлен код расчета в `price_calculator.py` → `calculate_cost()`
- [ ] 6. Добавлена структура маршрута в `routes[ключ]`
- [ ] 7. Заполнены все обязательные поля маршрута
- [ ] 8. Добавлен `breakdown` с детализацией затрат
- [ ] 9. (Опционально) Обновлены пороги плотности в `config/settings.yaml`
- [ ] 10. (Опционально) Добавлены уникальные поля в `RouteEditorV2.js`
- [ ] 11. Протестирован расчет на примере товара
- [ ] 12. Обновлена документация в `CALCULATION_FORMULAS.md`

---

## 🎯 Ключевые принципы

### ✅ Унифицированная структура
Все маршруты используют **одинаковые поля**:
- `name`, `delivery_days`
- `cost_rub`, `cost_usd`, `per_unit`
- `sale_rub`, `sale_usd`, `sale_per_unit`
- `breakdown` с детализацией

### ✅ Совместимость
Старые поля (`cost_per_unit_rub`, `total_cost_rub`) **дублируются** для совместимости с V1.

### ✅ Расширяемость
Новые маршруты **не требуют изменений frontend** - они автоматически отображаются в сравнении.

### ✅ Детализация
Каждый маршрут имеет `breakdown` с **полной детализацией** затрат для прозрачности расчета.

---

## 📚 Связанные документы

- [`CALCULATION_FORMULAS.md`](./CALCULATION_FORMULAS.md) - Полные формулы расчета
- [`config/settings.yaml`](./config/settings.yaml) - Настройки курсов и плотности
- [`config/categories.yaml`](./config/categories.yaml) - Категории товаров и пошлины
- [`README.md`](./README.md) - Общая документация проекта

---

**Версия документа:** 1.0  
**Дата создания:** 09.10.2025  
**Автор:** Price Calculator Team










