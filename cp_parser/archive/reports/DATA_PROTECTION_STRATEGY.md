# 🛡️ Стратегия защиты спарсенных данных

**Дата создания:** 06.10.2025  
**Цель:** Защитить 1,556 спарсенных проектов от случайного изменения/удаления

---

## 🎯 ПРОБЛЕМА

У нас есть:
- ✅ **1,556 успешно спарсенных проектов** с 7,967 товарами
- ✅ **23,075 изображений** в облаке
- ⚠️ **1,700 pending проектов** для парсинга

**Риски:**
1. Случайное перезаписывание существующих данных
2. Дублирование товаров/изображений
3. Потеря данных при миграции
4. Смешивание старых и новых данных

---

## ✅ РЕШЕНИЕ: Многоуровневая защита

### **Уровень 1: Пометка "защищенных" проектов в БД**

```sql
-- Добавляем поле для защиты
ALTER TABLE projects ADD COLUMN is_protected BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN protected_at TIMESTAMP;
ALTER TABLE projects ADD COLUMN protection_reason TEXT;

-- Защищаем все успешно спарсенные проекты
UPDATE projects 
SET 
    is_protected = TRUE,
    protected_at = NOW(),
    protection_reason = 'Successfully parsed and migrated to production'
WHERE parsing_status = 'completed' 
  AND id IN (SELECT DISTINCT project_id FROM products);
```

**Результат:** 1,556 проектов будут помечены как защищенные

---

### **Уровень 2: Создание snapshot БД**

```bash
# Создаем резервную копию ТОЛЬКО защищенных данных
python3 create_protected_snapshot.py

# Результат:
# - protected_projects_snapshot.json
# - protected_products_snapshot.json  
# - protected_images_snapshot.json
```

**Что это дает:**
- Быстрое восстановление в случае ошибки
- Возможность сравнения "до/после"
- Независимая копия данных

---

### **Уровень 3: Логика парсера с проверками**

```python
def can_parse_project(project_id, db_session):
    """Проверяет, можно ли парсить проект"""
    
    # Проверка 1: Проект защищен?
    project = db_session.query(Project).filter_by(id=project_id).first()
    if project and project.is_protected:
        logger.warning(f"❌ Проект {project_id} защищен! Парсинг запрещен.")
        return False
    
    # Проверка 2: Уже есть товары?
    products_count = db_session.query(Product).filter_by(project_id=project_id).count()
    if products_count > 0:
        logger.warning(f"❌ Проект {project_id} уже содержит {products_count} товаров!")
        return False
    
    # Проверка 3: Статус pending?
    if project and project.parsing_status != 'pending':
        logger.warning(f"❌ Проект {project_id} имеет статус {project.parsing_status}")
        return False
    
    return True

def safe_insert_product(product_data, db_session):
    """Безопасная вставка товара с проверками"""
    
    # Проверка на дубликаты
    existing = db_session.query(Product).filter_by(
        project_id=product_data['project_id'],
        name=product_data['name'],
        article_number=product_data['article_number']
    ).first()
    
    if existing:
        logger.warning(f"⚠️ Товар уже существует: {product_data['name']}")
        return existing.id
    
    # Вставка нового товара
    product = Product(**product_data)
    db_session.add(product)
    db_session.flush()
    
    return product.id
```

---

### **Уровень 4: Разделение на production и staging**

#### **Вариант A: Две отдельные БД**

```python
# config.py
PRODUCTION_DB = "postgresql://...railway.../railway"  # Защищенные данные
STAGING_DB = "sqlite:///staging.db"  # Новые данные для тестирования

# Workflow:
# 1. Парсим новые КП в STAGING_DB
# 2. Проверяем качество данных
# 3. Мигрируем в PRODUCTION_DB только проверенные данные
```

**Плюсы:**
- ✅ Полная изоляция
- ✅ Можно экспериментировать в staging
- ✅ Нулевой риск для production

**Минусы:**
- ❌ Нужны две БД
- ❌ Дополнительная миграция

---

#### **Вариант B: Одна БД с флагами**

```python
# Добавляем поля
ALTER TABLE projects ADD COLUMN data_source VARCHAR(20) DEFAULT 'production';
ALTER TABLE projects ADD COLUMN batch_id VARCHAR(50);

# Помечаем существующие данные
UPDATE projects SET data_source = 'production', batch_id = 'initial_migration';

# Новые данные помечаем как staging
INSERT INTO projects (..., data_source, batch_id) 
VALUES (..., 'staging', 'batch_2025_10_06');
```

**Плюсы:**
- ✅ Одна БД
- ✅ Легко фильтровать: `WHERE data_source = 'production'`
- ✅ Можно "повысить" staging -> production

**Минусы:**
- ⚠️ Нужна дисциплина в коде

---

### **Уровень 5: Миграция с проверками**

```python
def safe_migrate_to_postgresql(source_db, target_db):
    """Безопасная миграция с защитой от перезаписи"""
    
    with source_db.get_session() as src_session, \
         target_db.get_session() as tgt_session:
        
        # 1. Получаем MAX ID в target БД
        max_project_id = tgt_session.execute(
            text("SELECT COALESCE(MAX(id), 0) FROM projects")
        ).scalar()
        
        max_product_id = tgt_session.execute(
            text("SELECT COALESCE(MAX(id), 0) FROM products")
        ).scalar()
        
        print(f"📊 Target БД: max_project_id={max_project_id}, max_product_id={max_product_id}")
        
        # 2. Мигрируем ТОЛЬКО новые записи (id > max_id)
        new_projects = src_session.execute(
            text(f"SELECT * FROM projects WHERE id > {max_project_id}")
        ).fetchall()
        
        print(f"✅ Найдено {len(new_projects)} новых проектов для миграции")
        
        # 3. Проверяем на дубликаты по table_id
        for project in new_projects:
            existing = tgt_session.execute(
                text("SELECT id FROM projects WHERE table_id = :table_id"),
                {"table_id": project.table_id}
            ).fetchone()
            
            if existing:
                print(f"⚠️ Проект с table_id={project.table_id} уже существует! Пропускаем.")
                continue
            
            # Вставка нового проекта
            # ...
        
        print(f"✅ Миграция завершена без потери данных")
```

---

## 🎯 РЕКОМЕНДУЕМАЯ СТРАТЕГИЯ

### **Для вашего случая: Вариант B + Уровень 3**

**Шаг 1: Защитить существующие данные (СЕЙЧАС)**

```sql
-- 1. Добавляем поля защиты
ALTER TABLE projects ADD COLUMN is_protected BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN data_source VARCHAR(20) DEFAULT 'production';
ALTER TABLE projects ADD COLUMN batch_id VARCHAR(50);

-- 2. Защищаем все спарсенные проекты
UPDATE projects 
SET 
    is_protected = TRUE,
    data_source = 'production',
    batch_id = 'initial_1556_projects',
    protected_at = NOW()
WHERE parsing_status = 'completed' 
  AND id IN (SELECT DISTINCT project_id FROM products);

-- 3. Помечаем pending проекты
UPDATE projects 
SET 
    data_source = 'staging',
    batch_id = 'pending_1700_projects'
WHERE parsing_status = 'pending';
```

**Шаг 2: Создать snapshot (резервная копия)**

```bash
python3 create_protected_snapshot.py
# Создаст: protected_data_snapshot_2025_10_06.json
```

**Шаг 3: Обновить парсер**

```python
# В начале парсинга
if project.is_protected:
    raise ValueError(f"Проект {project.id} защищен! Парсинг запрещен.")

# Перед вставкой товара
existing_product = check_duplicate(product_data)
if existing_product:
    logger.warning("Товар уже существует, пропускаем")
    continue
```

**Шаг 4: Парсить новые КП**

```python
# Парсим ТОЛЬКО pending проекты
pending_projects = session.query(Project).filter(
    Project.parsing_status == 'pending',
    Project.is_protected == False  # Двойная защита
).all()
```

---

## 📋 ЧЕКЛИСТ ПЕРЕД ПАРСИНГОМ НОВЫХ КП

- [ ] ✅ Создан snapshot защищенных данных
- [ ] ✅ Все спарсенные проекты помечены `is_protected=TRUE`
- [ ] ✅ Парсер проверяет `is_protected` перед обработкой
- [ ] ✅ Парсер проверяет дубликаты товаров
- [ ] ✅ Используется `uploaded_images_index.json` для проверки изображений
- [ ] ✅ Новые данные помечаются `batch_id='batch_YYYY_MM_DD'`

---

## 🔧 ВОССТАНОВЛЕНИЕ В СЛУЧАЕ ОШИБКИ

```python
# Если что-то пошло не так:
python3 restore_from_snapshot.py protected_data_snapshot_2025_10_06.json

# Или откат конкретного batch:
DELETE FROM products WHERE project_id IN (
    SELECT id FROM projects WHERE batch_id = 'batch_2025_10_07'
);
DELETE FROM projects WHERE batch_id = 'batch_2025_10_07';
```

---

## 📊 МОНИТОРИНГ

```sql
-- Проверка защищенных данных
SELECT 
    data_source,
    COUNT(*) as projects,
    SUM(CASE WHEN is_protected THEN 1 ELSE 0 END) as protected
FROM projects
GROUP BY data_source;

-- Ожидаемый результат:
-- production | 1556 | 1556
-- staging    | 1700 | 0
```

---

## 💡 ИТОГО

**Лучший подход:**
1. ✅ Добавить `is_protected`, `data_source`, `batch_id` в БД
2. ✅ Защитить все 1,556 спарсенных проектов
3. ✅ Создать snapshot перед любыми изменениями
4. ✅ Обновить парсер с проверками
5. ✅ Парсить новые КП с пометкой `staging`
6. ✅ После проверки качества → `data_source='production'`

**Это даст:**
- 🛡️ Защиту от случайной перезаписи
- 📊 Возможность отката
- 🔍 Прозрачность (видно откуда данные)
- ⚡ Минимальные изменения в коде








**Дата создания:** 06.10.2025  
**Цель:** Защитить 1,556 спарсенных проектов от случайного изменения/удаления

---

## 🎯 ПРОБЛЕМА

У нас есть:
- ✅ **1,556 успешно спарсенных проектов** с 7,967 товарами
- ✅ **23,075 изображений** в облаке
- ⚠️ **1,700 pending проектов** для парсинга

**Риски:**
1. Случайное перезаписывание существующих данных
2. Дублирование товаров/изображений
3. Потеря данных при миграции
4. Смешивание старых и новых данных

---

## ✅ РЕШЕНИЕ: Многоуровневая защита

### **Уровень 1: Пометка "защищенных" проектов в БД**

```sql
-- Добавляем поле для защиты
ALTER TABLE projects ADD COLUMN is_protected BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN protected_at TIMESTAMP;
ALTER TABLE projects ADD COLUMN protection_reason TEXT;

-- Защищаем все успешно спарсенные проекты
UPDATE projects 
SET 
    is_protected = TRUE,
    protected_at = NOW(),
    protection_reason = 'Successfully parsed and migrated to production'
WHERE parsing_status = 'completed' 
  AND id IN (SELECT DISTINCT project_id FROM products);
```

**Результат:** 1,556 проектов будут помечены как защищенные

---

### **Уровень 2: Создание snapshot БД**

```bash
# Создаем резервную копию ТОЛЬКО защищенных данных
python3 create_protected_snapshot.py

# Результат:
# - protected_projects_snapshot.json
# - protected_products_snapshot.json  
# - protected_images_snapshot.json
```

**Что это дает:**
- Быстрое восстановление в случае ошибки
- Возможность сравнения "до/после"
- Независимая копия данных

---

### **Уровень 3: Логика парсера с проверками**

```python
def can_parse_project(project_id, db_session):
    """Проверяет, можно ли парсить проект"""
    
    # Проверка 1: Проект защищен?
    project = db_session.query(Project).filter_by(id=project_id).first()
    if project and project.is_protected:
        logger.warning(f"❌ Проект {project_id} защищен! Парсинг запрещен.")
        return False
    
    # Проверка 2: Уже есть товары?
    products_count = db_session.query(Product).filter_by(project_id=project_id).count()
    if products_count > 0:
        logger.warning(f"❌ Проект {project_id} уже содержит {products_count} товаров!")
        return False
    
    # Проверка 3: Статус pending?
    if project and project.parsing_status != 'pending':
        logger.warning(f"❌ Проект {project_id} имеет статус {project.parsing_status}")
        return False
    
    return True

def safe_insert_product(product_data, db_session):
    """Безопасная вставка товара с проверками"""
    
    # Проверка на дубликаты
    existing = db_session.query(Product).filter_by(
        project_id=product_data['project_id'],
        name=product_data['name'],
        article_number=product_data['article_number']
    ).first()
    
    if existing:
        logger.warning(f"⚠️ Товар уже существует: {product_data['name']}")
        return existing.id
    
    # Вставка нового товара
    product = Product(**product_data)
    db_session.add(product)
    db_session.flush()
    
    return product.id
```

---

### **Уровень 4: Разделение на production и staging**

#### **Вариант A: Две отдельные БД**

```python
# config.py
PRODUCTION_DB = "postgresql://...railway.../railway"  # Защищенные данные
STAGING_DB = "sqlite:///staging.db"  # Новые данные для тестирования

# Workflow:
# 1. Парсим новые КП в STAGING_DB
# 2. Проверяем качество данных
# 3. Мигрируем в PRODUCTION_DB только проверенные данные
```

**Плюсы:**
- ✅ Полная изоляция
- ✅ Можно экспериментировать в staging
- ✅ Нулевой риск для production

**Минусы:**
- ❌ Нужны две БД
- ❌ Дополнительная миграция

---

#### **Вариант B: Одна БД с флагами**

```python
# Добавляем поля
ALTER TABLE projects ADD COLUMN data_source VARCHAR(20) DEFAULT 'production';
ALTER TABLE projects ADD COLUMN batch_id VARCHAR(50);

# Помечаем существующие данные
UPDATE projects SET data_source = 'production', batch_id = 'initial_migration';

# Новые данные помечаем как staging
INSERT INTO projects (..., data_source, batch_id) 
VALUES (..., 'staging', 'batch_2025_10_06');
```

**Плюсы:**
- ✅ Одна БД
- ✅ Легко фильтровать: `WHERE data_source = 'production'`
- ✅ Можно "повысить" staging -> production

**Минусы:**
- ⚠️ Нужна дисциплина в коде

---

### **Уровень 5: Миграция с проверками**

```python
def safe_migrate_to_postgresql(source_db, target_db):
    """Безопасная миграция с защитой от перезаписи"""
    
    with source_db.get_session() as src_session, \
         target_db.get_session() as tgt_session:
        
        # 1. Получаем MAX ID в target БД
        max_project_id = tgt_session.execute(
            text("SELECT COALESCE(MAX(id), 0) FROM projects")
        ).scalar()
        
        max_product_id = tgt_session.execute(
            text("SELECT COALESCE(MAX(id), 0) FROM products")
        ).scalar()
        
        print(f"📊 Target БД: max_project_id={max_project_id}, max_product_id={max_product_id}")
        
        # 2. Мигрируем ТОЛЬКО новые записи (id > max_id)
        new_projects = src_session.execute(
            text(f"SELECT * FROM projects WHERE id > {max_project_id}")
        ).fetchall()
        
        print(f"✅ Найдено {len(new_projects)} новых проектов для миграции")
        
        # 3. Проверяем на дубликаты по table_id
        for project in new_projects:
            existing = tgt_session.execute(
                text("SELECT id FROM projects WHERE table_id = :table_id"),
                {"table_id": project.table_id}
            ).fetchone()
            
            if existing:
                print(f"⚠️ Проект с table_id={project.table_id} уже существует! Пропускаем.")
                continue
            
            # Вставка нового проекта
            # ...
        
        print(f"✅ Миграция завершена без потери данных")
```

---

## 🎯 РЕКОМЕНДУЕМАЯ СТРАТЕГИЯ

### **Для вашего случая: Вариант B + Уровень 3**

**Шаг 1: Защитить существующие данные (СЕЙЧАС)**

```sql
-- 1. Добавляем поля защиты
ALTER TABLE projects ADD COLUMN is_protected BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN data_source VARCHAR(20) DEFAULT 'production';
ALTER TABLE projects ADD COLUMN batch_id VARCHAR(50);

-- 2. Защищаем все спарсенные проекты
UPDATE projects 
SET 
    is_protected = TRUE,
    data_source = 'production',
    batch_id = 'initial_1556_projects',
    protected_at = NOW()
WHERE parsing_status = 'completed' 
  AND id IN (SELECT DISTINCT project_id FROM products);

-- 3. Помечаем pending проекты
UPDATE projects 
SET 
    data_source = 'staging',
    batch_id = 'pending_1700_projects'
WHERE parsing_status = 'pending';
```

**Шаг 2: Создать snapshot (резервная копия)**

```bash
python3 create_protected_snapshot.py
# Создаст: protected_data_snapshot_2025_10_06.json
```

**Шаг 3: Обновить парсер**

```python
# В начале парсинга
if project.is_protected:
    raise ValueError(f"Проект {project.id} защищен! Парсинг запрещен.")

# Перед вставкой товара
existing_product = check_duplicate(product_data)
if existing_product:
    logger.warning("Товар уже существует, пропускаем")
    continue
```

**Шаг 4: Парсить новые КП**

```python
# Парсим ТОЛЬКО pending проекты
pending_projects = session.query(Project).filter(
    Project.parsing_status == 'pending',
    Project.is_protected == False  # Двойная защита
).all()
```

---

## 📋 ЧЕКЛИСТ ПЕРЕД ПАРСИНГОМ НОВЫХ КП

- [ ] ✅ Создан snapshot защищенных данных
- [ ] ✅ Все спарсенные проекты помечены `is_protected=TRUE`
- [ ] ✅ Парсер проверяет `is_protected` перед обработкой
- [ ] ✅ Парсер проверяет дубликаты товаров
- [ ] ✅ Используется `uploaded_images_index.json` для проверки изображений
- [ ] ✅ Новые данные помечаются `batch_id='batch_YYYY_MM_DD'`

---

## 🔧 ВОССТАНОВЛЕНИЕ В СЛУЧАЕ ОШИБКИ

```python
# Если что-то пошло не так:
python3 restore_from_snapshot.py protected_data_snapshot_2025_10_06.json

# Или откат конкретного batch:
DELETE FROM products WHERE project_id IN (
    SELECT id FROM projects WHERE batch_id = 'batch_2025_10_07'
);
DELETE FROM projects WHERE batch_id = 'batch_2025_10_07';
```

---

## 📊 МОНИТОРИНГ

```sql
-- Проверка защищенных данных
SELECT 
    data_source,
    COUNT(*) as projects,
    SUM(CASE WHEN is_protected THEN 1 ELSE 0 END) as protected
FROM projects
GROUP BY data_source;

-- Ожидаемый результат:
-- production | 1556 | 1556
-- staging    | 1700 | 0
```

---

## 💡 ИТОГО

**Лучший подход:**
1. ✅ Добавить `is_protected`, `data_source`, `batch_id` в БД
2. ✅ Защитить все 1,556 спарсенных проектов
3. ✅ Создать snapshot перед любыми изменениями
4. ✅ Обновить парсер с проверками
5. ✅ Парсить новые КП с пометкой `staging`
6. ✅ После проверки качества → `data_source='production'`

**Это даст:**
- 🛡️ Защиту от случайной перезаписи
- 📊 Возможность отката
- 🔍 Прозрачность (видно откуда данные)
- ⚡ Минимальные изменения в коде
















