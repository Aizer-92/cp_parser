# 🔄 Workflow для добавления новых структур таблиц

**Дата**: 08.10.2025  
**Цель**: Пошаговый алгоритм для парсинга таблиц с новыми структурами

---

## 📊 Текущий статус

### Распарсено:
- ✅ **272 проекта** из 3,261 (8.3%)
- ✅ **1,825 completed** проектов (включая ранее распарсенные)
- ✅ Шаблон 1: Стандартная структура
- ✅ Шаблон 2: С колонкой "Итого, руб"
- ✅ Шаблон 3: С "Образцом" вместо АВИА

### Ожидают парсинга:
- ⏳ **1,431 pending** проектов (43.9%)
- ⏳ Возможны новые шаблоны структур

---

## 🎯 Workflow для новых структур

### Этап 1: Анализ структуры

```bash
# Шаг 1.1: Анализируем pending проекты
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.structure_parser import CommercialProposalParser

parser = CommercialProposalParser()

# Анализируем первые 100 pending проектов
pending_files = Path('storage/excel_files').glob('project_*.xlsx')
results = []

for i, file in enumerate(pending_files):
    if i >= 100:
        break
    
    # Парсим структуру
    structure = parser.parse_table_structure(str(file))
    
    if not structure['is_valid']:
        results.append({
            'file': file.name,
            'reason': structure['validation_errors']
        })

# Группируем по причинам
print("\n📊 ПРИЧИНЫ НЕВАЛИДНОСТИ:\n")
reasons = {}
for r in results:
    reason = r['reason'][0] if r['reason'] else 'Unknown'
    reasons[reason] = reasons.get(reason, 0) + 1

for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
    print(f"{count:3d} файлов: {reason}")
EOF
```

**Что искать:**
- Новые названия колонок
- Новые маршруты (кроме ЖД/АВИА/Образец)
- Другое расположение данных (не с 4-й строки)
- Дополнительные поля

---

### Этап 2: Создание профиля новой структуры

```bash
# Шаг 2.1: Создаем файл с описанием нового шаблона
cat << 'EOF' > new_structure_profile.json
{
  "template_name": "Шаблон 4",
  "characteristics": {
    "data_start_row": 5,  // Пример: данные с 5-й строки
    "columns": {
      "A": "Photo",
      "B": "Name",
      "C": "Article",     // Новая колонка: артикул
      "D": "Description",
      "E": "Brand",        // Новая колонка: бренд
      "F": "Quantity",
      "G": "Price_USD"
    },
    "routes": [
      {
        "type": "EXPRESS",  // Новый тип маршрута
        "columns": {
          "qty": 6,
          "usd": 7,
          "rub": 8,
          "delivery": 9
        }
      }
    ]
  },
  "validation_rules": {
    "required_columns": ["A", "B", "C"],  // Артикул обязателен
    "min_routes": 1
  }
}
EOF
```

---

### Этап 3: Обновление валидатора

**Файл**: `src/structure_parser.py`

```python
class CommercialProposalParser:
    
    KNOWN_TEMPLATES = {
        'standard': {
            'data_start_row': 4,
            'required_columns': ['A', 'B'],
            'route_patterns': ['ЖД', 'АВИА']
        },
        'with_total': {
            'data_start_row': 4,
            'required_columns': ['A', 'B'],
            'route_patterns': ['ЖД', 'АВИА'],
            'skip_columns': ['Итого']  # Пропускаем эти колонки
        },
        'with_sample': {
            'data_start_row': 4,
            'required_columns': ['A', 'B'],
            'route_patterns': ['ЖД', 'Образец']
        },
        # 🆕 Добавляем новый шаблон
        'express_route': {
            'data_start_row': 5,
            'required_columns': ['A', 'B', 'C'],  # + артикул
            'route_patterns': ['EXPRESS', 'STANDARD']
        }
    }
    
    def detect_template(self, worksheet):
        """Определяет тип шаблона таблицы"""
        # Проверяем заголовки
        headers = self._extract_headers(worksheet)
        
        # Проверяем каждый шаблон
        for template_name, template_config in self.KNOWN_TEMPLATES.items():
            if self._matches_template(headers, template_config):
                return template_name, template_config
        
        return None, None
```

---

### Этап 4: Обновление парсера

**Файл**: `parse_validated_files.py` (новый)

```python
def parse_with_template(file_path, template_config):
    """
    Универсальный парсер на основе конфигурации шаблона
    """
    wb = load_workbook(file_path, data_only=True)
    ws = wb.active
    
    data_start_row = template_config['data_start_row']
    required_columns = template_config['required_columns']
    route_patterns = template_config['route_patterns']
    
    products = []
    
    for row in range(data_start_row, ws.max_row + 1):
        # Извлекаем название
        name = ws.cell(row, 2).value  # B колонка
        if not name or len(str(name).strip()) < 3:
            continue
        
        # Извлекаем доп. поля (если есть)
        article = None
        if 'C' in required_columns:
            article = ws.cell(row, 3).value
        
        # Парсим предложения для каждого маршрута
        offers = []
        for route_pattern in route_patterns:
            route_offers = parse_route_offers(
                ws, row, route_pattern, template_config
            )
            offers.extend(route_offers)
        
        if offers:
            products.append({
                'name': name,
                'article': article,
                'offers': offers
            })
    
    return products
```

---

### Этап 5: Тестирование

```bash
# Шаг 5.1: Тестируем на 10 файлах нового типа
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

# Список файлов нового типа
test_files = [
    'project_1001_xxx.xlsx',
    'project_1002_yyy.xlsx',
    # ... еще 8 файлов
]

for file in test_files:
    result = parse_with_template(file, new_template_config)
    
    print(f"\n📁 {file}:")
    print(f"   Товары: {len(result['products'])}")
    print(f"   Предложения: {result['total_offers']}")
    print(f"   Изображения: {result['total_images']}")
    
    # Проверяем качество
    if result['total_offers'] / len(result['products']) < 2:
        print(f"   ⚠️  Мало предложений на товар!")
EOF
```

**Критерии успеха:**
- ✅ Все товары с названием >= 3 символов
- ✅ Минимум 2 предложения на товар
- ✅ Минимум 1 изображение на товар
- ✅ Цены в реалистичных диапазонах

---

### Этап 6: Массовый парсинг

```bash
# Шаг 6.1: Валидация всех файлов нового типа
python3 validate_new_template_files.py

# Шаг 6.2: Парсинг валидных файлов
python3 parse_new_template_files.py

# Ожидаемый вывод:
# ✅ Распарсено: 150 файлов
# ✅ Товары: 450 (3 на файл в среднем)
# ✅ Предложения: 1,350 (3 на товар)
# ✅ Изображения: 3,600 (8 на товар)
```

---

### Этап 7: Загрузка изображений

```bash
# Используем существующий скрипт
python3 upload_images_multithread.py
```

**Автоматически:**
- Находит все новые изображения (без `image_url`)
- Загружает на FTP
- Обновляет `image_url` в БД

---

### Этап 8: Миграция на Railway

```bash
# Используем существующий скрипт
python3 migrate_new_products_to_railway.py
```

**Автоматически:**
- Находит новые проекты по `parsing_status = 'completed'`
- Мигрирует только те, которых нет на Railway
- Обновляет счетчики

---

### Этап 9: Проверка

```bash
# Статистика Railway
python3 check_railway_data.py

# Генерация отчета для проверки качества
python3 create_random_100_report.py
```

---

## 📝 Чеклист для новой структуры

### Перед началом:
- [ ] Проанализировано минимум 10 файлов нового типа
- [ ] Создан профиль структуры (JSON)
- [ ] Определены обязательные поля
- [ ] Определены типы маршрутов

### Разработка:
- [ ] Обновлен `structure_parser.py` (валидация)
- [ ] Обновлен `parse_validated_files.py` (парсинг)
- [ ] Добавлены тесты для нового шаблона
- [ ] Протестировано на 10 файлах

### Массовый парсинг:
- [ ] Валидация всех файлов нового типа
- [ ] Парсинг валидных файлов
- [ ] Проверка качества (>= 2 offers/product)
- [ ] Загрузка изображений на FTP
- [ ] Миграция на Railway
- [ ] Финальная проверка

### Документация:
- [ ] Обновлен `DATABASE_SCHEMA_AND_VALIDATION.md`
- [ ] Добавлен пример нового шаблона
- [ ] Обновлена статистика
- [ ] Создан changelog

---

## 🎯 Целевые показатели

### Качество парсинга:
- ✅ Успешность >= 95%
- ✅ Предложений на товар >= 2.0
- ✅ Изображений на товар >= 5.0
- ✅ Все цены в реалистичных диапазонах

### Производительность:
- ✅ Парсинг: ~20-30 файлов/мин
- ✅ Загрузка изображений: ~3-4 img/sec
- ✅ Миграция: ~50-100 products/sec

---

## 🔍 Анализ оставшихся проектов

### Текущая статистика:
```
Всего проектов:   3,261
├─ Completed:     1,825 (56.0%)
├─ Pending:       1,431 (43.9%)  ← ЦЕЛЬ
└─ Error:             5 (0.2%)
```

### Примерная структура pending:
```
Шаблон 1-3 (уже поддерживаются): ~800 файлов (56%)
Шаблон 4 (новые поля):           ~300 файлов (21%)
Шаблон 5 (матричные цены):       ~200 файлов (14%)
Другие/поврежденные:             ~131 файлов (9%)
```

---

## 🚀 План действий

### Приоритет 1: Шаблоны 1-3
**~800 файлов** уже должны подходить под существующие шаблоны

```bash
# Анализируем почему они не распарсились
python3 analyze_failed_validations.py

# Возможные причины:
# - Проблемы с кодировкой
# - Поврежденные файлы
# - Нужна донастройка валидатора
```

### Приоритет 2: Шаблон 4 (новые поля)
**~300 файлов** с дополнительными колонками

```bash
# Создаем новый профиль
# Обновляем парсер
# Тестируем на 10 файлах
# Запускаем массовый парсинг
```

### Приоритет 3: Шаблон 5 (матричные цены)
**~200 файлов** с матрицей цен (цена зависит от 2+ параметров)

```bash
# Требуется новая логика парсинга
# Возможно, отдельная таблица в БД
```

---

## 📞 Контакты

**Проект**: Commercial Proposals Parser  
**Автор**: Reshad  
**Дата**: 08.10.2025

---

**Готово к работе с новыми структурами! 🎉**







**Дата**: 08.10.2025  
**Цель**: Пошаговый алгоритм для парсинга таблиц с новыми структурами

---

## 📊 Текущий статус

### Распарсено:
- ✅ **272 проекта** из 3,261 (8.3%)
- ✅ **1,825 completed** проектов (включая ранее распарсенные)
- ✅ Шаблон 1: Стандартная структура
- ✅ Шаблон 2: С колонкой "Итого, руб"
- ✅ Шаблон 3: С "Образцом" вместо АВИА

### Ожидают парсинга:
- ⏳ **1,431 pending** проектов (43.9%)
- ⏳ Возможны новые шаблоны структур

---

## 🎯 Workflow для новых структур

### Этап 1: Анализ структуры

```bash
# Шаг 1.1: Анализируем pending проекты
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.structure_parser import CommercialProposalParser

parser = CommercialProposalParser()

# Анализируем первые 100 pending проектов
pending_files = Path('storage/excel_files').glob('project_*.xlsx')
results = []

for i, file in enumerate(pending_files):
    if i >= 100:
        break
    
    # Парсим структуру
    structure = parser.parse_table_structure(str(file))
    
    if not structure['is_valid']:
        results.append({
            'file': file.name,
            'reason': structure['validation_errors']
        })

# Группируем по причинам
print("\n📊 ПРИЧИНЫ НЕВАЛИДНОСТИ:\n")
reasons = {}
for r in results:
    reason = r['reason'][0] if r['reason'] else 'Unknown'
    reasons[reason] = reasons.get(reason, 0) + 1

for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
    print(f"{count:3d} файлов: {reason}")
EOF
```

**Что искать:**
- Новые названия колонок
- Новые маршруты (кроме ЖД/АВИА/Образец)
- Другое расположение данных (не с 4-й строки)
- Дополнительные поля

---

### Этап 2: Создание профиля новой структуры

```bash
# Шаг 2.1: Создаем файл с описанием нового шаблона
cat << 'EOF' > new_structure_profile.json
{
  "template_name": "Шаблон 4",
  "characteristics": {
    "data_start_row": 5,  // Пример: данные с 5-й строки
    "columns": {
      "A": "Photo",
      "B": "Name",
      "C": "Article",     // Новая колонка: артикул
      "D": "Description",
      "E": "Brand",        // Новая колонка: бренд
      "F": "Quantity",
      "G": "Price_USD"
    },
    "routes": [
      {
        "type": "EXPRESS",  // Новый тип маршрута
        "columns": {
          "qty": 6,
          "usd": 7,
          "rub": 8,
          "delivery": 9
        }
      }
    ]
  },
  "validation_rules": {
    "required_columns": ["A", "B", "C"],  // Артикул обязателен
    "min_routes": 1
  }
}
EOF
```

---

### Этап 3: Обновление валидатора

**Файл**: `src/structure_parser.py`

```python
class CommercialProposalParser:
    
    KNOWN_TEMPLATES = {
        'standard': {
            'data_start_row': 4,
            'required_columns': ['A', 'B'],
            'route_patterns': ['ЖД', 'АВИА']
        },
        'with_total': {
            'data_start_row': 4,
            'required_columns': ['A', 'B'],
            'route_patterns': ['ЖД', 'АВИА'],
            'skip_columns': ['Итого']  # Пропускаем эти колонки
        },
        'with_sample': {
            'data_start_row': 4,
            'required_columns': ['A', 'B'],
            'route_patterns': ['ЖД', 'Образец']
        },
        # 🆕 Добавляем новый шаблон
        'express_route': {
            'data_start_row': 5,
            'required_columns': ['A', 'B', 'C'],  # + артикул
            'route_patterns': ['EXPRESS', 'STANDARD']
        }
    }
    
    def detect_template(self, worksheet):
        """Определяет тип шаблона таблицы"""
        # Проверяем заголовки
        headers = self._extract_headers(worksheet)
        
        # Проверяем каждый шаблон
        for template_name, template_config in self.KNOWN_TEMPLATES.items():
            if self._matches_template(headers, template_config):
                return template_name, template_config
        
        return None, None
```

---

### Этап 4: Обновление парсера

**Файл**: `parse_validated_files.py` (новый)

```python
def parse_with_template(file_path, template_config):
    """
    Универсальный парсер на основе конфигурации шаблона
    """
    wb = load_workbook(file_path, data_only=True)
    ws = wb.active
    
    data_start_row = template_config['data_start_row']
    required_columns = template_config['required_columns']
    route_patterns = template_config['route_patterns']
    
    products = []
    
    for row in range(data_start_row, ws.max_row + 1):
        # Извлекаем название
        name = ws.cell(row, 2).value  # B колонка
        if not name or len(str(name).strip()) < 3:
            continue
        
        # Извлекаем доп. поля (если есть)
        article = None
        if 'C' in required_columns:
            article = ws.cell(row, 3).value
        
        # Парсим предложения для каждого маршрута
        offers = []
        for route_pattern in route_patterns:
            route_offers = parse_route_offers(
                ws, row, route_pattern, template_config
            )
            offers.extend(route_offers)
        
        if offers:
            products.append({
                'name': name,
                'article': article,
                'offers': offers
            })
    
    return products
```

---

### Этап 5: Тестирование

```bash
# Шаг 5.1: Тестируем на 10 файлах нового типа
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

# Список файлов нового типа
test_files = [
    'project_1001_xxx.xlsx',
    'project_1002_yyy.xlsx',
    # ... еще 8 файлов
]

for file in test_files:
    result = parse_with_template(file, new_template_config)
    
    print(f"\n📁 {file}:")
    print(f"   Товары: {len(result['products'])}")
    print(f"   Предложения: {result['total_offers']}")
    print(f"   Изображения: {result['total_images']}")
    
    # Проверяем качество
    if result['total_offers'] / len(result['products']) < 2:
        print(f"   ⚠️  Мало предложений на товар!")
EOF
```

**Критерии успеха:**
- ✅ Все товары с названием >= 3 символов
- ✅ Минимум 2 предложения на товар
- ✅ Минимум 1 изображение на товар
- ✅ Цены в реалистичных диапазонах

---

### Этап 6: Массовый парсинг

```bash
# Шаг 6.1: Валидация всех файлов нового типа
python3 validate_new_template_files.py

# Шаг 6.2: Парсинг валидных файлов
python3 parse_new_template_files.py

# Ожидаемый вывод:
# ✅ Распарсено: 150 файлов
# ✅ Товары: 450 (3 на файл в среднем)
# ✅ Предложения: 1,350 (3 на товар)
# ✅ Изображения: 3,600 (8 на товар)
```

---

### Этап 7: Загрузка изображений

```bash
# Используем существующий скрипт
python3 upload_images_multithread.py
```

**Автоматически:**
- Находит все новые изображения (без `image_url`)
- Загружает на FTP
- Обновляет `image_url` в БД

---

### Этап 8: Миграция на Railway

```bash
# Используем существующий скрипт
python3 migrate_new_products_to_railway.py
```

**Автоматически:**
- Находит новые проекты по `parsing_status = 'completed'`
- Мигрирует только те, которых нет на Railway
- Обновляет счетчики

---

### Этап 9: Проверка

```bash
# Статистика Railway
python3 check_railway_data.py

# Генерация отчета для проверки качества
python3 create_random_100_report.py
```

---

## 📝 Чеклист для новой структуры

### Перед началом:
- [ ] Проанализировано минимум 10 файлов нового типа
- [ ] Создан профиль структуры (JSON)
- [ ] Определены обязательные поля
- [ ] Определены типы маршрутов

### Разработка:
- [ ] Обновлен `structure_parser.py` (валидация)
- [ ] Обновлен `parse_validated_files.py` (парсинг)
- [ ] Добавлены тесты для нового шаблона
- [ ] Протестировано на 10 файлах

### Массовый парсинг:
- [ ] Валидация всех файлов нового типа
- [ ] Парсинг валидных файлов
- [ ] Проверка качества (>= 2 offers/product)
- [ ] Загрузка изображений на FTP
- [ ] Миграция на Railway
- [ ] Финальная проверка

### Документация:
- [ ] Обновлен `DATABASE_SCHEMA_AND_VALIDATION.md`
- [ ] Добавлен пример нового шаблона
- [ ] Обновлена статистика
- [ ] Создан changelog

---

## 🎯 Целевые показатели

### Качество парсинга:
- ✅ Успешность >= 95%
- ✅ Предложений на товар >= 2.0
- ✅ Изображений на товар >= 5.0
- ✅ Все цены в реалистичных диапазонах

### Производительность:
- ✅ Парсинг: ~20-30 файлов/мин
- ✅ Загрузка изображений: ~3-4 img/sec
- ✅ Миграция: ~50-100 products/sec

---

## 🔍 Анализ оставшихся проектов

### Текущая статистика:
```
Всего проектов:   3,261
├─ Completed:     1,825 (56.0%)
├─ Pending:       1,431 (43.9%)  ← ЦЕЛЬ
└─ Error:             5 (0.2%)
```

### Примерная структура pending:
```
Шаблон 1-3 (уже поддерживаются): ~800 файлов (56%)
Шаблон 4 (новые поля):           ~300 файлов (21%)
Шаблон 5 (матричные цены):       ~200 файлов (14%)
Другие/поврежденные:             ~131 файлов (9%)
```

---

## 🚀 План действий

### Приоритет 1: Шаблоны 1-3
**~800 файлов** уже должны подходить под существующие шаблоны

```bash
# Анализируем почему они не распарсились
python3 analyze_failed_validations.py

# Возможные причины:
# - Проблемы с кодировкой
# - Поврежденные файлы
# - Нужна донастройка валидатора
```

### Приоритет 2: Шаблон 4 (новые поля)
**~300 файлов** с дополнительными колонками

```bash
# Создаем новый профиль
# Обновляем парсер
# Тестируем на 10 файлах
# Запускаем массовый парсинг
```

### Приоритет 3: Шаблон 5 (матричные цены)
**~200 файлов** с матрицей цен (цена зависит от 2+ параметров)

```bash
# Требуется новая логика парсинга
# Возможно, отдельная таблица в БД
```

---

## 📞 Контакты

**Проект**: Commercial Proposals Parser  
**Автор**: Reshad  
**Дата**: 08.10.2025

---

**Готово к работе с новыми структурами! 🎉**













