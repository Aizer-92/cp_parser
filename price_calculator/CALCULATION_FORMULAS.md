# 📐 Формулы расчета стоимости товаров

**Дата создания:** 08.10.2025
**Версия:** 2.0
**Статус:** Актуально

---

## 🎯 Общая концепция

Система рассчитывает себестоимость товара по 4 маршрутам логистики:

1. **Highway ЖД** - железнодорожная доставка
2. **Highway Авиа** - авиа доставка
3. **Highway под контракт** - фиксированные ставки с пошлинами
4. **Prologix** - расчет по кубометрам

---

## 💰 Базовые переменные

### Курсы валют

- `yuan_to_usd` = 0.139
- `usd_to_rub` = 85
- `yuan_to_rub` = 11.68

### Комиссии

- `toni_commission` = 5% (пошлина за выкуп)
- `transfer_commission` = 18% (комиссия за перевод, только для Highway ЖД/Авиа)

### Дополнительные расходы

- `local_delivery` = 2 юаней/кг (локальная доставка в Китае)
- `msk_pickup` = 1000 руб (забор в Москве на весь тираж)
- `other_costs` = 2.5% от (цена товара + локальная доставка)

---

## 🚂 Highway ЖД / ✈️ Highway Авиа

### Структура затрат (за 1 шт):

```
Стоимость в Китае:
├─ Цена в юанях (базовая)
├─ Пошлина за выкуп (5%)
├─ Комиссия за перевод (18%)
└─ Локальная доставка

Логистика:
└─ общий_вес × (базовая_ставка + надбавка_за_плотность)

Прочие расходы:
├─ Забор МСК (фикс)
└─ Прочие расходы (2.5%)
```

### Формула полная:

```python
# 1. Стоимость товара с комиссиями
base_price_rub = price_yuan * yuan_to_rub
toni_commission_rub = base_price_rub * 0.05
transfer_commission_rub = (base_price_rub + toni_commission_rub) * 0.18
factory_price = base_price_rub + toni_commission_rub + transfer_commission_rub

# 2. Локальная доставка
local_delivery = local_delivery_yuan_per_kg * weight_kg * yuan_to_rub

# 3. Логистика
# 3.1 Базовая ставка (из категории товара)
base_rate_rail = category["rates"]["rail_base"]  # например, 7.5 $/кг
base_rate_air = category["rates"]["air_base"]    # например, 9.6 $/кг (rail + 2.1)

# 3.2 Надбавка за плотность (если density < порог)
density_kg_m3 = packing_box_weight / (length * width * height)
density_surcharge_usd = get_density_surcharge(density_kg_m3, delivery_type)

# 3.3 Итоговая логистика
logistics_rate = base_rate + density_surcharge
logistics_cost = weight_kg * logistics_rate * usd_to_rub

# 4. Прочие расходы
msk_pickup = 1000 / quantity  # на единицу
other_costs = (factory_price + local_delivery) * 0.025

# 5. ИТОГО себестоимость за 1 шт
cost_per_unit = factory_price + local_delivery + logistics_cost + msk_pickup + other_costs
```

### Отличие Авиа от ЖД:

```python
# Авиа = ЖД + 2.1 $/кг
air_base_rate = rail_base_rate + 2.1
```

---

## 📦 Highway под контракт

### Структура затрат (за 1 шт):

```
Стоимость в Китае:
├─ Цена в юанях (базовая)
├─ Пошлина за выкуп (5%)
└─ Локальная доставка

Логистика:
├─ общий_вес × (ставка_контракт + надбавка_за_плотность)
├─ Пошлины (таможенная_стоимость × duty_rate)
└─ НДС ((таможенная_стоимость + пошлины) × vat_rate)

Прочие расходы:
├─ Забор МСК (фикс)
├─ Прочие расходы (2.5%)
└─ Фиксированные расходы (25,000 руб)
```

**Таможенная стоимость** = товар + локальная доставка + логистика

### Формула полная:

```python
# 1. Стоимость товара (БЕЗ комиссии за перевод 18%)
base_price_rub = price_yuan * yuan_to_rub
toni_commission_rub = base_price_rub * 0.05
factory_price = base_price_rub + toni_commission_rub

# 2. Локальная доставка
local_delivery = local_delivery_yuan_per_kg * weight_kg * yuan_to_rub

# 3. Логистика под контракт
# 3.1 Фиксированные ставки
contract_base_rate = 3.4  # $/кг для ЖД (5.5 для авиа)

# 3.2 Надбавка за плотность
density_surcharge = get_density_surcharge(density_kg_m3, delivery_type)

# 3.3 Итоговая логистика
contract_logistics_rate = contract_base_rate + density_surcharge
contract_logistics_cost = weight_kg * contract_logistics_rate * usd_to_rub

# 4. Пошлины и НДС
# ВАЖНО: Пошлины и НДС рассчитываются от таможенной стоимости
# но в текущей реализации включены в общую стоимость
duty_rate = category["duty_rate"]  # например, 10%
vat_rate = category["vat_rate"]    # например, 20%

# 5. Фиксированные расходы
fixed_cost = 25000 / quantity  # 25,000 руб на весь тираж

# 6. Прочие расходы
msk_pickup = 1000 / quantity
other_costs = (factory_price + local_delivery) * 0.025

# 7. ИТОГО себестоимость за 1 шт
cost_per_unit = (
    factory_price + 
    local_delivery + 
    contract_logistics_cost + 
    msk_pickup + 
    other_costs + 
    fixed_cost
)
```

### Ключевые отличия от Highway ЖД/Авиа:

- ❌ **НЕТ** комиссии за перевод 18%
- ✅ **ЕСТЬ** фиксированные ставки логистики (3.4 или 5.5 $/кг)
- ✅ **ЕСТЬ** фиксированные расходы 25,000 руб
- ✅ **ЕСТЬ** информация о пошлинах и НДС (отображается справочно)

---

## 🚚 Prologix

### Структура затрат (за 1 шт):

```
Стоимость в Китае:
├─ Цена в юанях (базовая)
├─ Пошлина за выкуп (5%)
└─ Локальная доставка

Логистика:
├─ общий_объем × ставка_prologix (руб/м³)
├─ Пошлины (таможенная_стоимость × duty_rate)
└─ НДС ((таможенная_стоимость + пошлины) × vat_rate)

Прочие расходы:
├─ Забор МСК (фикс)
├─ Прочие расходы (2.5%)
└─ Фиксированные расходы (25,000 руб)
```

**Таможенная стоимость** = товар + локальная доставка + логистика

### Формула полная:

```python
# 1. Стоимость товара (БЕЗ комиссии за перевод 18%)
base_price_rub = price_yuan * yuan_to_rub
toni_commission_rub = base_price_rub * 0.05
factory_price = base_price_rub + toni_commission_rub

# 2. Локальная доставка
local_delivery = local_delivery_yuan_per_kg * weight_kg * yuan_to_rub

# 3. Логистика Prologix (по кубометрам)
# 3.1 Расчет общего объема
box_volume_m3 = length * width * height  # размеры в метрах!
boxes_count = quantity / packing_units_per_box
total_volume_m3 = box_volume_m3 * boxes_count

# 3.2 Определение ставки по тарифной сетке
if 2 <= total_volume_m3 < 8:
    rate_rub_per_m3 = 41000
elif 8 <= total_volume_m3 < 20:
    rate_rub_per_m3 = 20000
elif 20 <= total_volume_m3 < 30:
    rate_rub_per_m3 = 15000
elif total_volume_m3 >= 30:
    rate_rub_per_m3 = 13000

# 3.3 Итоговая логистика
prologix_logistics_cost = total_volume_m3 * rate_rub_per_m3

# 4. Пошлины и НДС
duty_rate = category["duty_rate"]  # например, 10%
vat_rate = category["vat_rate"]    # например, 20%

# 5. Фиксированные расходы
fixed_cost = 25000 / quantity

# 6. Прочие расходы
msk_pickup = 1000 / quantity
other_costs = (factory_price + local_delivery) * 0.025

# 7. ИТОГО себестоимость за 1 шт
cost_per_unit = (
    factory_price + 
    local_delivery + 
    prologix_logistics_cost / quantity +
    msk_pickup + 
    other_costs + 
    fixed_cost
)
```

### Тарифная сетка Prologix:

| Объем (м³) | Ставка (руб/м³) | Срок доставки |
| ----------------- | -------------------------- | ------------------------- |
| 2-8               | 41,000                     | 25-35 дней            |
| 8-20              | 20,000                     | 25-35 дней            |
| 20-30             | 15,000                     | 25-35 дней            |
| 30+               | 13,000                     | 25-35 дней            |

---

## 📊 Надбавка за плотность

### Логика:

Если плотность товара **ниже** определенного порога, применяется надбавка к логистической ставке.

### Источник данных:

`config/density_surcharges.yaml`

### Пример структуры:

```yaml
rail:  # ЖД доставка
  - density: 50    # кг/м³
    surcharge: 2.5 # $/кг
  - density: 100
    surcharge: 1.8
  - density: 150
    surcharge: 1.2
  - density: 200
    surcharge: 0.5
  - density: 250
    surcharge: 0.0

air:   # Авиа доставка
  - density: 50
    surcharge: 3.2
  - density: 100
    surcharge: 2.3
  - density: 150
    surcharge: 1.5
  - density: 200
    surcharge: 0.8
  - density: 250
    surcharge: 0.0
```

### Алгоритм расчета:

```python
def get_density_surcharge(density_kg_m3, delivery_type):
    """
    Линейная интерполяция между точками
    """
    surcharge_data = load_yaml("density_surcharges.yaml")[delivery_type]
  
    # Если плотность >= максимальной, надбавка = 0
    if density_kg_m3 >= surcharge_data[-1]["density"]:
        return 0.0
  
    # Если плотность <= минимальной, используем максимальную надбавку
    if density_kg_m3 <= surcharge_data[0]["density"]:
        return surcharge_data[0]["surcharge"]
  
    # Линейная интерполяция между ближайшими точками
    for i in range(len(surcharge_data) - 1):
        d1 = surcharge_data[i]["density"]
        s1 = surcharge_data[i]["surcharge"]
        d2 = surcharge_data[i+1]["density"]
        s2 = surcharge_data[i+1]["surcharge"]
      
        if d1 <= density_kg_m3 <= d2:
            # Линейная интерполяция
            ratio = (density_kg_m3 - d1) / (d2 - d1)
            return s1 + (s2 - s1) * ratio
  
    return 0.0
```

---

## 🎨 Отображение в UI (V2)

### Структура блоков:

```
Стоимость в Китае (XX.X%)
├─ Цена в юанях → X.XX ¥ = XXX.XX ₽
├─ Пошлина за выкуп (5%) → XXX.XX ₽
├─ Комиссия за перевод (18%) → XXX.XX ₽  [только ЖД/Авиа]
└─ Локальная доставка → XXX.XX ₽

Логистика (XX.X%)
├─ [ЖД/Авиа] XXX.X кг × Y.YY $/кг → XXX.XX ₽
├─ [Контракт] XXX.X кг × Y.YY $/кг → XXX.XX ₽
├─ [Prologix] XX.X м³ × YYY ₽/м³ → XXX.XX ₽
└─ [Контракт/Prologix] Пошлины + НДС (XX% + XX%)

Прочие расходы (XX.X%)
├─ Забор МСК → XXX.XX ₽
├─ Прочие (2.5%) → XXX.XX ₽
└─ Фиксированные расходы → XXX.XX ₽  [только Контракт/Prologix]
```

---

## 🔄 История изменений

### v2.0 (08.10.2025)

- ✅ Добавлена детализация затрат в breakdown
- ✅ Разделение Highway ЖД/Авиа от Контракта и Prologix
- ✅ Добавлены проценты от общей себестоимости
- ✅ Общий вес показывается в логистике

### v1.0 (06.10.2025)

- ✅ Реализованы надбавки за плотность
- ✅ Добавлен Prologix с расчетом по кубометрам
- ✅ Highway под контракт с фиксированными ставками

---

## ⚠️ ВАЖНО!

### Ключевые различия маршрутов:

| Параметр                          | Highway ЖД/Авиа         | Highway Контракт | Prologix                 |
| ----------------------------------------- | ----------------------------- | ------------------------ | ------------------------ |
| Комиссия перевод (18%)     | ✅ ДА                       | ❌ НЕТ                | ❌ НЕТ                |
| Расчет логистики           | По весу                 | По весу            | По объему        |
| Фиксированные расходы | ❌ НЕТ                     | ✅ 25,000₽              | ✅ 25,000₽              |
| Пошлины/НДС                     | Не показывается | Отображается | Отображается |
| Надбавка за плотность  | ✅ ДА                       | ✅ ДА                  | ❌ НЕТ                |

### Файлы конфигурации:

- `config/currencies.yaml` - курсы валют
- `config/density_surcharges.yaml` - надбавки за плотность
- `config/prologix_rates.yaml` - тарифы Prologix
- `config/categories.yaml` - категории товаров с ставками

---

## 📞 Контакты

При изменении формул обновлять:

1. **Backend:** `price_calculator.py` (методы `calculate_cost`, `calculate_prologix_cost`)
2. **Frontend:** `static/js/v2/RouteDetailsV2.js` (отображение breakdown)
3. **Этот документ:** `CALCULATION_FORMULAS.md`

**Версия актуальна на:** 08.10.2025
