# 🏗️ СТРУКТУРА ПРОЕКТОВ - Два отдельных проекта

## ⚠️ ВАЖНО: Теперь у нас ДВА ОТДЕЛЬНЫХ ПРОЕКТА

Проблема с ветками решена! Теперь у нас **два физически разных проекта**:

---

## 🎯 ПРОЕКТ 1: `mockup_generator` (ПРОДАКШЕН)

### **📁 Расположение:**
```
/projects/mockup_generator/
```

### **🌿 Git ветка:**
```bash
git branch: main
```

### **📋 Содержимое:**
```
mockup_generator/
├── app_clean.py             # 🎯 ГЛАВНОЕ приложение (стабильное)
├── refactor/                # 📁 Папка для экспериментов
│   ├── app.py              # 🧪 Тестовая версия
│   ├── simple_analyzer.py  # 🔍 Тестовый анализатор
│   └── api/routes/         # 🌐 Тестовые API
├── main.py                  # 🚀 Railway entry point
└── Procfile                 # ⚙️ Railway: app_clean.py
```

### **🌐 Railway деплой:**
- **URL**: https://mockups-production.up.railway.app
- **Главная страница**: Оригинальный mockup generator
- **Роут `/refactor`**: Тестовый анализатор (простая версия)

### **🎯 Назначение:**
- ✅ **Продакшен версия** - стабильная, проверенная
- ✅ **Основной функционал** без анализатора
- ✅ **Тестирование** новых функций в папке `refactor/`

---

## 🚀 ПРОЕКТ 2: `mockup_generator_refactor` (REFACTOR)

### **📁 Расположение:**
```
/projects/mockup_generator_refactor/
```

### **🌿 Git ветка:**
```bash
git branch: refactor-railway
```

### **📋 Содержимое:**
```
mockup_generator_refactor/
├── app.py                   # 🎯 ГЛАВНОЕ приложение (с анализатором)
├── main_railway.py          # 🚀 Railway entry point
├── simple_analyzer.py       # 🔍 Анализатор товаров
├── categories.json          # 📋 11 категорий с правилами
├── api/routes/single.py     # 🌐 API с комбинированным анализом
└── Procfile                 # ⚙️ Railway: main_railway.py
```

### **🌐 Railway деплой:**
- **URL**: Будет отдельный Railway проект
- **Главная страница**: REFACTOR с анализатором товаров
- **Полный функционал**: Комбинированный анализ + генерация

### **🎯 Назначение:**
- ✅ **REFACTOR версия** - с полным анализатором
- ✅ **Независимое тестирование** от продакшена
- ✅ **Экспериментальные функции**

---

## 🔧 АЛГОРИТМ РАБОТЫ

### **📋 Работа с ПРОДАКШЕН проектом:**
```bash
cd /projects/mockup_generator/
git status  # Должно показать: main branch

# Разработка новых функций
cd refactor/
python app.py  # Тестируем локально

# Обновление продакшена
git add .
git commit -m "feat: обновление продакшен версии"
git push origin main
```

### **📋 Работа с REFACTOR проектом:**
```bash
cd /projects/mockup_generator_refactor/
git status  # Должно показать: refactor-railway branch

# Разработка REFACTOR функций
python app.py  # Тестируем локально

# Деплой на Railway
git add .
git commit -m "feat: обновление REFACTOR версии"
git push origin refactor-railway
```

### **🔄 Перенос функций между проектами:**
```bash
# Из REFACTOR в ПРОДАКШЕН (когда функция стабильна)
cp mockup_generator_refactor/simple_analyzer.py mockup_generator/refactor/

# Из ПРОДАКШЕН в REFACTOR (базовые обновления)
cp mockup_generator/app_clean.py mockup_generator_refactor/app_base.py
```

---

## 📊 ПРЕИМУЩЕСТВА НОВОЙ СТРУКТУРЫ

### **✅ Четкое разделение:**
- **Продакшен** = стабильный, рабочий проект
- **REFACTOR** = экспериментальный проект с анализатором

### **✅ Независимые деплои:**
- **Продакшен Railway** = основной URL, стабильная версия
- **REFACTOR Railway** = отдельный URL, тестовая версия

### **✅ Простое управление:**
- **Нет путаницы с ветками** в одной папке
- **Ясная структура** файлов в каждом проекте
- **Независимая разработка** без конфликтов

### **✅ Безопасность:**
- **Продакшен защищен** от экспериментальных изменений
- **REFACTOR изолирован** для безопасного тестирования

---

## 🎯 ТЕКУЩЕЕ СОСТОЯНИЕ

### **✅ ПРОДАКШЕН (`mockup_generator`):**
- **Статус**: ✅ Готов, стабилен
- **Railway**: ✅ Развернут на https://mockups-production.up.railway.app
- **Функционал**: ✅ Основной mockup generator + тестовый анализатор

### **✅ REFACTOR (`mockup_generator_refactor`):**
- **Статус**: ✅ Готов к деплою
- **Railway**: ⏳ Нужно подключить как новый проект
- **Функционал**: ✅ Полный анализатор + комбинированная генерация

---

**🎯 Теперь структура проектов четкая и понятная!**








