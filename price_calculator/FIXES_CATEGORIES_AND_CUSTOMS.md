# 🔧 Исправления: Категории и Пошлины

## Дата: 06.10.2025

### ❌ Проблемы:
1. **ID категорий = undefined** при попытке редактирования/удаления
2. **Пошлины не отображаются** в таблице категорий
3. **Дубли категорий** в списке
4. **Миграция БД** выполняется при каждом деплое на Railway

---

## ✅ Исправления:

### 1. **Отключена автоматическая миграция БД**
**Файл:** `main.py`

```python
# ⚠️ МИГРАЦИЯ ОТКЛЮЧЕНА - БД уже настроена на Railway
# init_database()  # Закомментировано чтобы не пытаться изменять схему при каждом деплое
```

**Причина:** БД уже настроена на Railway, повторная миграция вызывала ошибки.

---

### 2. **Улучшена обработка ID категорий (Backend)**
**Файл:** `backend/api/categories.py`

**Изменения:**
- Добавлена явная обработка PostgreSQL JSONB (возвращает `dict` напрямую)
- Добавлено детальное логирование для отладки
- Добавлена финальная проверка наличия ID перед возвратом

```python
# PostgreSQL JSONB возвращает dict напрямую
if isinstance(category_json, dict):
    category_data = category_json.copy()

# КРИТИЧНО: Добавляем ID в данные
category_data['id'] = category_id

print(f"✅ Категория '{category_data.get('category')}': ID={category_id}, has_id={('id' in category_data)}")
```

---

### 3. **Устранены дубли категорий**
**Файл:** `backend/api/categories.py`

**Изменения:**
```python
# PostgreSQL
cursor.execute("SELECT DISTINCT ON (id) id, data FROM categories ORDER BY id")

# SQLite
cursor.execute("SELECT id, data FROM categories GROUP BY id ORDER BY id")
```

---

### 4. **Улучшена обработка ID на Frontend**
**Файл:** `static/js/components/CategoriesPanel.js`

**Изменения в `startEdit`:**
```javascript
// Глубокая копия с явным сохранением ID
var categoryClone = JSON.parse(JSON.stringify(category));

// КРИТИЧНО: Убеждаемся что ID скопирован
if (!categoryClone.id && category.id) {
    categoryClone.id = category.id;
}

console.log('🔧 ID категории:', this.editingCategory.id, 'тип:', typeof this.editingCategory.id);
```

**Изменения в `deleteCategory`:**
```javascript
var categoryId = category.id;
console.log('🗑️ Отправляем DELETE запрос для ID:', categoryId);
axios.delete('/api/categories/' + categoryId)
```

---

### 5. **Добавлено корректное отображение пошлин**
**Файл:** `static/js/components/CategoriesPanel.js`

**Функция `getCustomsInfo`:**
- Проверяет `customs_info` (новый формат)
- Fallback на прямые поля (`duty_rate`, `vat_rate`)
- Поддержка массивов и строк для сертификатов
- Отображение типа пошлины (комб./спец.)

```javascript
getCustomsInfo: function(category) {
    var customs = {
        duty_rate: null,
        vat_rate: null,
        duty_type: null,
        certificates: []
    };
    
    // Проверяем customs_info
    if (category.customs_info) {
        customs.duty_rate = category.customs_info.duty_rate;
        customs.vat_rate = category.customs_info.vat_rate;
        customs.duty_type = category.customs_info.duty_type;
        customs.certificates = category.customs_info.certificates || [];
    }
    
    // Fallback на прямые поля
    if (!customs.duty_rate && category.duty_rate) {
        customs.duty_rate = category.duty_rate;
    }
    // ...
    
    return customs.duty_rate || customs.vat_rate ? customs : null;
}
```

---

### 6. **Улучшена таблица категорий**
**Файл:** `static/js/components/CategoriesPanel.js`

**Новые колонки:**
- **Пошлина** - с бейджем типа (комб./спец.)
- **НДС** - процент НДС
- **Сертификаты** - количество требуемых сертификатов

```html
<td>
    <span v-if="getCustomsInfo(cat)">
        <strong>{{ getCustomsInfo(cat).duty_rate }}</strong>
        <span v-if="getCustomsInfo(cat).duty_type === 'combined'" class="duty-type-badge">комб.</span>
    </span>
</td>
```

---

### 7. **Добавлены стили для пошлин**
**Файл:** `static/css/components/categories-panel.css`

```css
/* Customs Info Badges */
.duty-type-badge {
    display: inline-block;
    margin-left: 6px;
    padding: 2px 6px;
    background: #fef3c7;
    color: #92400e;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
}

.certificates-count {
    display: inline-block;
    padding: 4px 10px;
    background: #dbeafe;
    color: #1e40af;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
}
```

---

### 8. **Добавлен автоматический сброс кеша**
**Файл:** `index.html`

```html
<!-- 🔥 CACHE BUSTER - Очистка Service Worker и кеша -->
<script>
    // Удаляем Service Worker если есть
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(function(registrations) {
            for(let registration of registrations) {
                registration.unregister();
            }
        });
    }
    
    // Очищаем кеш
    if ('caches' in window) {
        caches.keys().then(function(names) {
            for (let name of names) {
                caches.delete(name);
            }
        });
    }
</script>
```

---

## 🧪 Как проверить:

### 1. **Проверка ID категорий:**
```
1. Открой Railway logs
2. Найди строки: "✅ Категория 'XXX': ID=123, has_id=True"
3. Открой консоль браузера (F12)
4. Найди строки: "ID первой категории: 123"
```

### 2. **Проверка редактирования:**
```
1. Открой Настройки → Категории
2. Нажми "Изменить" на любой категории
3. В консоли должно быть:
   "🔧 ID категории: 123 тип: number"
4. Измени данные и сохрани
5. Должно появиться "✅ Категория сохранена!"
```

### 3. **Проверка удаления:**
```
1. Нажми "Удалить" на категории
2. В консоли должно быть:
   "🗑️ ID категории: 123 тип: number"
   "🗑️ Отправляем DELETE запрос для ID: 123"
3. Подтверди удаление
4. Категория должна исчезнуть из списка
```

### 4. **Проверка пошлин:**
```
1. Открой таблицу категорий
2. Колонка "Пошлина" должна показывать проценты
3. Для текстиля (футболки, худи) должен быть бейдж "комб."
4. Колонка "Сертификаты" должна показывать количество
```

---

## 📊 Ожидаемый результат:

✅ Категории загружаются с ID  
✅ Редактирование работает  
✅ Удаление работает  
✅ Пошлины отображаются корректно  
✅ Сертификаты показывают количество  
✅ Нет дублей категорий  
✅ Миграция БД не запускается при деплое  

---

## 🚀 Следующие шаги:

1. **Протестировать на Railway** после деплоя
2. **Проверить логи** на наличие ошибок
3. **Убедиться** что все CRUD операции работают
4. **Внедрить Vue Router** (аккуратно, без ломания UI)
