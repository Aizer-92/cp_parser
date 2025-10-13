# 🚀 Следующие шаги для price_calculator

**Текущий статус:** Этап 1.1 завершен - Надбавки за плотность работают!

---

## ✅ Что уже работает

### Надбавки за плотность (Highway Company)

**Backend:** 
- ✅ `config/density_surcharges.yaml` - таблицы для ЖД и Авиа
- ✅ `price_calculator.py` - функции расчета с интерполяцией
- ✅ `main.py` - API поддержка, модель `CalculationResponse`

**Frontend:**
- ✅ `ResultsDisplay.js` - детализация логистики
- ✅ Отображение: базовая ставка + надбавка = итоговая

**Как работает:**
```
Плотность = вес_коробки / (длина × ширина × высота)
Надбавка = таблица[плотность, тип_доставки]
Итоговая_ставка = базовая + надбавка
```

---

## 🎯 Следующая задача: Добавить 4 новых маршрута

### 1. Prologix (приоритет: ВЫСОКИЙ)

**Что нужно:**
- [ ] Получить таблицу тарифов Prologix ($/м³ в зависимости от объема)
- [ ] Создать `config/prologix_rates.yaml`
- [ ] Добавить функцию в `logistics_calculator.py` (новый файл)

**Формула:**
```python
total_volume = box_volume × boxes_count
rate_per_m3 = prologix_table[total_volume]  # диапазоны
cost = total_volume × rate_per_m3
```

**Пример тарифов (ЗАПРОСИТЬ У КЛИЕНТА):**
```yaml
prologix_rates:
  volume_tiers:
    - max_volume: 5      # до 5 м³
      rate_usd: 60
    - max_volume: 10     # 5-10 м³
      rate_usd: 50
    - max_volume: 20     # 10-20 м³
      rate_usd: 45
    - max_volume: 999999 # >20 м³
      rate_usd: 40
  delivery_days_avg: 30
```

---

### 2. Контейнер (приоритет: СРЕДНИЙ)

**Что нужно:**
- [ ] Стоимость контейнеров 20ft и 40ft
- [ ] Создать `config/container_rates.yaml`
- [ ] Логика выбора типа контейнера

**Формула:**
```python
# Емкость контейнеров
capacity_20ft = 33  # м³
capacity_40ft = 67  # м³

total_volume = box_volume × boxes_count

if total_volume <= capacity_20ft:
    cost_per_m3 = price_20ft / capacity_20ft
elif total_volume <= capacity_40ft:
    cost_per_m3 = price_40ft / capacity_40ft
else:
    # Несколько контейнеров
    containers_needed = ceil(total_volume / capacity_40ft)
    cost = containers_needed × price_40ft

total_cost = total_volume × cost_per_m3
```

**Данные (ЗАПРОСИТЬ):**
```yaml
container_rates:
  container_20ft:
    price_usd: 2500
    capacity_m3: 33
    delivery_days_avg: 45
  container_40ft:
    price_usd: 4500
    capacity_m3: 67
    delivery_days_avg: 45
```

---

### 3. Cargo (Казахстан) (приоритет: СРЕДНИЙ)

**Что нужно:**
- [ ] Базовая ставка $/кг для Cargo
- [ ] Добавить в `config/logistics_rates.yaml`

**Формула:**
```python
total_weight = box_weight × boxes_count
rate_per_kg = cargo_rate  # константа
cost = total_weight × rate_per_kg
```

**Данные (ЗАПРОСИТЬ):**
```yaml
cargo_rates:
  kazakhstan:
    rate_usd_per_kg: 4.20
    delivery_days_avg: 25
    delivery_days_min: 20
    delivery_days_max: 30
```

---

### 4. Объединить Quick и Precise (приоритет: НИЗКИЙ)

**Идея:** Добавить checkbox "Считать только по весу"

**Изменения:**
- [ ] `ProductFormPrecise.js` - добавить checkbox
- [ ] При включенном checkbox: не запрашивать габариты
- [ ] Backend: использовать категорийную плотность вместо расчета

---

## 📁 Структура файлов (план)

```
price_calculator/
├── config/
│   ├── density_surcharges.yaml     ✅ ЕСТЬ
│   ├── prologix_rates.yaml         🔜 TODO
│   ├── container_rates.yaml        🔜 TODO
│   └── cargo_rates.yaml            🔜 TODO (или в logistics_rates.yaml)
│
├── backend/
│   └── logistics/                  🔜 TODO (новая папка)
│       ├── __init__.py
│       ├── prologix.py
│       ├── container.py
│       └── cargo.py
│
├── static/js/components/
│   ├── ResultsDisplay.js           ✅ ОБНОВЛЕН
│   ├── ProductFormPrecise.js       🔜 TODO (checkbox)
│   └── RoutesComparison.js         🔜 TODO (новый компонент)
│
├── price_calculator.py             ✅ ОБНОВЛЕН
├── main.py                         ✅ ОБНОВЛЕН
└── logistics_calculator.py         🔜 TODO (новый файл)
```

---

## 🛠️ Как начать работу над новым маршрутом

### Шаблон для нового маршрута

**1. Создать конфиг:** `config/prologix_rates.yaml`

```yaml
# Название маршрута
name: "Prologix"
description: "Расчет по кубометрам"

# Тарифы
rates:
  # ... структура зависит от маршрута

# Метаданные
delivery_days_avg: 30
min_volume: 1  # м³
max_volume: 100  # м³
```

**2. Создать модуль:** `backend/logistics/prologix.py`

```python
import yaml
from typing import Dict, Optional

class PrologixCalculator:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def calculate(self, 
                  box_volume: float, 
                  boxes_count: int) -> Dict:
        """
        Расчет стоимости по Prologix
        
        Returns:
            {
                'route_name': 'Prologix',
                'total_volume_m3': float,
                'rate_per_m3': float,
                'total_cost_usd': float,
                'total_cost_rub': float,
                'delivery_days': int
            }
        """
        total_volume = box_volume * boxes_count
        rate = self._get_rate_for_volume(total_volume)
        
        return {
            'route_name': 'Prologix',
            'total_volume_m3': total_volume,
            'rate_per_m3': rate,
            'total_cost_usd': total_volume * rate,
            'delivery_days': self.config['delivery_days_avg']
        }
    
    def _get_rate_for_volume(self, volume: float) -> float:
        """Получить ставку по объему"""
        for tier in self.config['rates']['volume_tiers']:
            if volume <= tier['max_volume']:
                return tier['rate_usd']
        return self.config['rates']['volume_tiers'][-1]['rate_usd']
```

**3. Интегрировать в `main.py`:**

```python
from backend.logistics.prologix import PrologixCalculator

# В startup
prologix_calc = PrologixCalculator('config/prologix_rates.yaml')

# В API endpoint
@app.post("/api/calculate-all-routes")
async def calculate_all_routes(request: CalculationRequest):
    # Базовый расчет
    result = calc.calculate_cost(...)
    
    # Добавляем Prologix
    if result['density_info']['has_density_data']:
        box_volume = result['density_info']['volume_m3']
        boxes_count = ceil(request.quantity / request.packing_units_per_box)
        
        prologix_result = prologix_calc.calculate(box_volume, boxes_count)
        result['routes']['prologix'] = prologix_result
    
    return result
```

---

## 📋 Чеклист для каждого маршрута

- [ ] Собрать данные (тарифы, сроки)
- [ ] Создать YAML конфиг
- [ ] Написать класс калькулятора
- [ ] Добавить unit тесты
- [ ] Интегрировать в API
- [ ] Обновить UI (таблица сравнения)
- [ ] Протестировать вручную
- [ ] Обновить документацию

---

## 🧪 Тестирование

### Тестовые данные для всех маршрутов

**Легкий товар:**
```
Название: плюшевая игрушка
Цена: 15¥
Вес единицы: 0.2 кг
Количество: 1000

Упаковка:
- В коробке: 20 шт
- Вес коробки: 3 кг
- Размеры: 0.5 × 0.4 × 0.3 м
- Объем коробки: 0.06 м³
- Плотность: 50 кг/м³

Всего:
- Коробок: 50
- Вес: 150 кг
- Объем: 3 м³
```

**Средний товар:**
```
Название: кружка
Цена: 25¥
Вес единицы: 0.35 кг
Количество: 500

Упаковка:
- В коробке: 24 шт
- Вес коробки: 8 кг
- Размеры: 0.35 × 0.30 × 0.25 м
- Объем коробки: 0.02625 м³
- Плотность: 305 кг/м³

Всего:
- Коробок: 21
- Вес: 168 кг
- Объем: 0.55 м³
```

**Тяжелый товар:**
```
Название: металлический термос
Цена: 60¥
Вес единицы: 2 кг
Количество: 500

Упаковка:
- В коробке: 12 шт
- Вес коробки: 25 кг
- Размеры: 0.40 × 0.30 × 0.20 м
- Объем коробки: 0.024 м³
- Плотность: 1041 кг/м³

Всего:
- Коробок: 42
- Вес: 1050 кг
- Объем: 1.008 м³
```

---

## 📞 Что запросить у клиента

### Срочно нужны данные:

1. **Prologix тарифы:**
   - Ставка $/м³ для разных объемов (диапазоны)
   - Средний срок доставки
   - Минимальный и максимальный объем

2. **Контейнер:**
   - Стоимость 20ft контейнера
   - Стоимость 40ft контейнера
   - Срок доставки

3. **Cargo (Казахстан):**
   - Ставка $/кг
   - Средний срок (говорили ~25 дней)
   - Есть ли ограничения по весу/объему

---

## 🎯 Приоритетный план на неделю

### День 1-2: Prologix
- Получить тарифы
- Реализовать калькулятор
- Интегрировать в API

### День 3-4: Cargo
- Получить ставки
- Добавить в конфиг
- Интегрировать в API

### День 5: Контейнер
- Получить данные
- Реализовать логику выбора типа

### День 6-7: UI
- Создать компонент сравнения маршрутов
- Тестирование всех маршрутов

---

**Важно:** Сначала надо **протестировать текущую реализацию** с плотностью! Убедиться что всё работает корректно в UI после последнего фикса (добавление `density_info` в Pydantic модель).

**Команда для запуска:**
```bash
cd /Users/bakirovresad/Downloads/Reshad\ 1/projects/price_calculator
source venv/bin/activate
python main.py
# → http://localhost:8000
```

---

**Последнее обновление:** 06.10.2025  
**См. также:** `PRECISE_CALCULATIONS_VISION.md` - полное видение проекта











