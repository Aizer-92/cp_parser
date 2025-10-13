# V3 UI - План приближения стилей к V2

## Дата: 13.10.2025

## 🎨 АНАЛИЗ СТИЛЕЙ V2 vs V3

### V2 Стили (reference)
```css
body {
    background: #f3f4f6;  /* ✅ Совпадает */
    color: #111827;       /* ✅ Совпадает */
}

/* V2 использует встроенные стили в компонентах */
```

### V3 Стили (текущие)
```css
/* Слишком много переменных */
--color-primary: #3b82f6;    /* Синий - слишком яркий */
--border-radius: 8px;         /* ✅ ОК */
--shadow-md: 0 4px 6px...    /* Слишком заметная тень */
```

---

## 🔴 ОСНОВНЫЕ РАЗЛИЧИЯ

### 1. Цветовая схема

| Элемент | V2 | V3 | Исправление |
|---------|----|----|-------------|
| Primary | Нет яркого синего | `#3b82f6` (яркий синий) | Использовать `#3b82f6` только для акцентов |
| Кнопки | Простые, без градиентов | Тени и hover эффекты | Упростить |
| Фон карточек | `background: white` | `box-shadow: 0 4px 6px` | Уменьшить тень |
| Активный таб | Не такой яркий | Яркий синий фон | Сделать тоньше |

### 2. Табы навигации

**V2 подход:** Минималистичный
```css
/* V2 не имеет отдельных табов - это один экран */
```

**V3 подход:** Выделенные табы
```css
.tabs-nav {
    background: white;
    padding: 12px;
    box-shadow: 0 1px 2px...
}

.tab-active {
    background: #3b82f6;  /* Слишком яркий */
    color: white;
}
```

**Исправление:**
```css
.tabs-nav {
    background: transparent;  /* Без фона */
    padding: 0;
    border-bottom: 1px solid #e5e7eb;
}

.tab {
    padding: 12px 20px;
    border-bottom: 3px solid transparent;
}

.tab-active {
    background: transparent;
    color: #3b82f6;
    border-bottom-color: #3b82f6;
}
```

### 3. Карточки (Cards)

**V2:** Простые, без теней
```css
/* В V2 карточки встроены inline */
background: white;
padding: 20px;
border-radius: 8px;
border: 1px solid #e5e7eb;  /* Тонкая рамка */
```

**V3:** С тенями
```css
.card {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
    padding: 24px;
}
```

**Исправление:**
```css
.card {
    background: white;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    padding: 20px;  /* Меньше padding */
    margin-bottom: 16px;  /* Меньше margin */
}
```

### 4. Форма (Form)

**V2:** Компактная
```css
gap: 12px;  /* Между полями */
```

**V3:** Просторная
```css
gap: 16px;  /* Слишком много */
```

**Исправление:**
```css
.form {
    gap: 12px;
}

.form-group {
    gap: 6px;  /* Между label и input */
}
```

### 5. Кнопки (Buttons)

**V2:** Простые
```css
button {
    padding: 10px 20px;
    background: #3b82f6;
    border: none;
    border-radius: 6px;
    /* Без теней */
}

button:hover {
    opacity: 0.9;
}
```

**V3:** С эффектами
```css
.btn-primary {
    padding: 10px 20px;
    background: #3b82f6;
    border-radius: 8px;
    transition: all 0.2s;
}

.btn-primary:hover {
    background: #2563eb;  /* Изменение цвета */
}
```

**Исправление:** Оставить V3 подход, но упростить

### 6. Inputs

**V2:** Стандартные
```css
input {
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
}

input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
```

**V3:** ✅ Совпадает!

---

## 🎯 ПЛАН ДЕЙСТВИЙ

### Этап 1: Табы навигации
```css
/* ЗАМЕНИТЬ */
.tabs-nav {
    display: flex;
    gap: 0;
    background: transparent;
    padding: 0;
    border-bottom: 1px solid #e5e7eb;
    box-shadow: none;
    margin-bottom: 20px;
}

.tab {
    flex: 0;
    padding: 12px 20px;
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    font-size: 15px;
    font-weight: 500;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s;
}

.tab:hover {
    color: #3b82f6;
    background: transparent;
}

.tab-active {
    background: transparent;
    color: #3b82f6;
    border-bottom-color: #3b82f6;
}
```

### Этап 2: Карточки
```css
/* ЗАМЕНИТЬ */
.card {
    background: white;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    box-shadow: none;  /* Убрать тень */
    padding: 20px;  /* Меньше */
    margin-bottom: 16px;  /* Меньше */
}

.card-title {
    font-size: 18px;  /* Меньше */
    font-weight: 600;
    color: #111827;
    margin: 0 0 16px 0;  /* Меньше отступ */
}
```

### Этап 3: Форма
```css
/* ЗАМЕНИТЬ */
.form {
    display: flex;
    flex-direction: column;
    gap: 12px;  /* Меньше */
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;  /* Меньше */
}

.form-group label {
    font-size: 14px;
    font-weight: 500;
    color: #374151;
}
```

### Этап 4: Результаты - компактный вид
```css
/* НОВЫЙ СТИЛЬ */
.results-compact {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;
}

.result-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #f3f4f6;
}

.result-row:last-child {
    border-bottom: none;
}

.route-name {
    font-weight: 600;
    color: #111827;
    min-width: 80px;
}

.route-prices {
    font-size: 15px;
    color: #6b7280;
}

.route-profit {
    font-size: 14px;
    color: #10b981;
    margin-left: auto;
}
```

### Этап 5: Переключатель режимов
```css
/* ЗАМЕНИТЬ - стиль V2 */
.mode-toggle {
    display: flex;
    gap: 20px;  /* Больше gap */
    padding: 0;  /* Убрать padding */
    background: transparent;  /* Убрать фон */
    border-radius: 0;
    margin: 12px 0;
}

.toggle-label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 14px;
    color: #374151;  /* Темнее */
    font-weight: 500;
}

.toggle-radio {
    width: 16px;
    height: 16px;
    cursor: pointer;
    accent-color: #3b82f6;
}
```

---

## 📊 СРАВНЕНИЕ: ДО и ПОСЛЕ

### ДО (V3 текущий)
- ✅ Современный дизайн
- ❌ Слишком много пространства
- ❌ Яркие цвета
- ❌ Заметные тени
- ❌ Выделенные табы

### ПОСЛЕ (V3 приближенный к V2)
- ✅ Чистый дизайн
- ✅ Компактная форма
- ✅ Нейтральные цвета
- ✅ Минимальные тени
- ✅ Простые табы

---

## 🔧 КОД ДЛЯ ЗАМЕНЫ

### Файл: `static/css/v3-styles.css`

#### 1. Обновить переменные
```css
:root {
    --color-primary: #3b82f6;
    --color-primary-hover: #2563eb;
    --color-success: #10b981;
    --color-danger: #ef4444;
    --color-gray-50: #f9fafb;
    --color-gray-100: #f3f4f6;
    --color-gray-200: #e5e7eb;
    --color-gray-300: #d1d5db;
    --color-gray-500: #6b7280;
    --color-gray-700: #374151;
    --color-gray-900: #111827;
    --border-radius: 8px;
    --spacing-xs: 6px;
    --spacing-sm: 12px;
    --spacing-md: 16px;
    --spacing-lg: 20px;
}
```

#### 2. Применить изменения
- Заменить все `gap: 16px` → `gap: 12px`
- Заменить все `padding: 24px` → `padding: 20px`
- Заменить все `margin-bottom: 20px` → `margin-bottom: 16px`
- Убрать все `box-shadow` из `.card`
- Добавить `border: 1px solid #e5e7eb` в `.card`

---

## ⏱️ ОЦЕНКА ВРЕМЕНИ

| Задача | Время |
|--------|-------|
| Обновить табы | 20 мин |
| Обновить карточки | 20 мин |
| Обновить форму | 20 мин |
| Компактные результаты | 30 мин |
| Переключатель | 10 мин |
| **ИТОГО** | **1.5 часа** |

---

## 📝 КОНТРОЛЬНЫЙ СПИСОК

- [ ] Табы: transparent фон, border-bottom для активного
- [ ] Карточки: без теней, с рамкой
- [ ] Форма: gap 12px вместо 16px
- [ ] Label: gap 6px вместо 8px
- [ ] Padding: 20px вместо 24px
- [ ] Margin: 16px вместо 20px
- [ ] Переключатель: без фона
- [ ] Результаты: компактный вид
- [ ] Кнопки: ✅ оставить как есть
- [ ] Inputs: ✅ оставить как есть


