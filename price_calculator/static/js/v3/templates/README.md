# Vue Templates (Вынесенные)

Эта папка содержит **вынесенные template strings** из Vue компонентов.

## 🎯 Зачем?

### ДО рефакторинга:
```javascript
// PositionFormV3.js (640 строк)
window.PositionFormV3 = {
    template: `<div>...310 строк HTML...</div>`,
    data() { return {} },      // 20 строк
    methods: { ... }            // 300 строк
}
```

**Проблемы:**
- ❌ Тяжело читать (99% файла = HTML)
- ❌ Нет syntax highlighting для HTML
- ❌ IDE плохо форматирует
- ❌ Сложно найти логику среди HTML

### ПОСЛЕ рефакторинга:
```javascript
// PositionFormV3.js (342 строки чистой логики)
import { POSITION_FORM_TEMPLATE } from './templates/position-form.template.js';

window.PositionFormV3 = {
    template: POSITION_FORM_TEMPLATE,  // ← Чистая ссылка
    data() { return {} },               // 20 строк
    methods: { ... }                    // 300 строк
}

// templates/position-form.template.js (360 строк)
export const POSITION_FORM_TEMPLATE = `
    <div class="position-form-fullscreen">
        <!-- Весь HTML здесь -->
    </div>
`;
```

**Преимущества:**
- ✅ **Разделение ответственности** (SoC): логика отдельно, UI отдельно
- ✅ **Легче читать** логику (файл в 2 раза короче)
- ✅ **IDE поддержка**: с расширением можно подсвечивать HTML в template literals
- ✅ **Переиспользование**: можно использовать один template в нескольких компонентах
- ✅ **НЕ НУЖЕН build step**: работает через ES modules (native browser import)

---

## 📁 Структура

```
templates/
├── README.md                          ← Этот файл
├── position-form.template.js          ← PositionFormV3 (360 строк)
├── quick-mode.template.js             ← QuickModeV3 (предстоит)
├── categories-panel.template.js       ← CategoriesPanelV3 (предстоит)
├── calculation-results.template.js    ← CalculationResultsV3 (предстоит)
├── positions-list.template.js         ← PositionsListV3 (предстоит)
└── settings-panel.template.js         ← SettingsPanelV3 (предстоит)
```

---

## 🛠️ Как использовать

### 1. Создать новый template

```javascript
// templates/my-component.template.js
/**
 * Template для MyComponent
 * Описание что этот компонент делает
 */
export const MY_COMPONENT_TEMPLATE = `
<div class="my-component">
    <h2>{{ title }}</h2>
    <button @click="handleClick">Click me</button>
</div>
`;
```

### 2. Импортировать в компонент

```javascript
// MyComponent.js
import { MY_COMPONENT_TEMPLATE } from './templates/my-component.template.js';

window.MyComponent = {
    template: MY_COMPONENT_TEMPLATE,
    
    data() {
        return {
            title: 'Hello'
        };
    },
    
    methods: {
        handleClick() {
            console.log('Clicked!');
        }
    }
};
```

### 3. Зарегистрировать в index.html

```html
<!-- index_v3.html -->
<!-- Сначала загружаем template -->
<script type="module" src="/static/js/v3/templates/my-component.template.js"></script>

<!-- Потом компонент -->
<script type="module" src="/static/js/v3/MyComponent.js"></script>
```

---

## 🎨 VS Code расширения

Для лучшей поддержки HTML в template literals:

```json
// .vscode/extensions.json
{
    "recommendations": [
        "Tobermory.es6-string-html",     // ← Подсветка HTML в template strings
        "octref.vetur",                   // ← Vue syntax
        "formulahendry.auto-close-tag"
    ]
}
```

После установки добавьте комментарий перед template:

```javascript
// /* html */
export const MY_TEMPLATE = `
    <div>...</div>
`;
```

---

## 📊 Статистика рефакторинга

| Компонент | Было (строк) | Стало (логика) | Template | Выгода |
|-----------|--------------|----------------|----------|--------|
| PositionFormV3 | 640 | 342 | 360 | -47% размер логики |
| QuickModeV3 | 506 | TBD | TBD | TBD |
| CategoriesPanelV3 | 473 | TBD | TBD | TBD |

---

## ✅ Преимущества подхода

1. **NO BUILD STEP** ⚡
   - Работает через ES modules (поддержка во всех браузерах 2020+)
   - Не нужен Webpack/Vite/Rollup
   - Просто деплой статики

2. **Читаемость** 📖
   - Логика компонента = 1 файл (меньше и чище)
   - Template = другой файл (можно редактировать отдельно)

3. **Поддержка** 🛠️
   - Frontend-разработчик работает с templates/
   - Backend-разработчик работает с логикой
   - Меньше конфликтов при merge

4. **Переиспользование** ♻️
   - Один template можно использовать в нескольких местах
   - Легко создавать вариации (extend)

---

## 🚀 Следующие шаги

- [x] PositionFormV3 (640 → 342 строки)
- [ ] QuickModeV3 (506 строк)
- [ ] CategoriesPanelV3 (473 строки)
- [ ] CalculationResultsV3 (409 строк)
- [ ] PositionsListV3 (357 строк)
- [ ] SettingsPanelV3 (382 строки)

---

**Автор:** Senior Developer Analysis & Refactoring
**Дата:** 14 октября 2025

