# КРИТИЧЕСКИ ВАЖНО: Проверка Google APIs

## ❌ Ошибка 403 ВСЕГДА означает что APIs не включены!

Даже если Service Account новый с правами - **APIs нужно включить отдельно!**

---

## ✅ ТОЧНАЯ ИНСТРУКЦИЯ:

### Шаг 1: Открой Google Cloud Console

**Ссылка:** https://console.cloud.google.com

**ВАЖНО:** Выбери **ПРАВИЛЬНЫЙ ПРОЕКТ** в верхнем выпадающем списке!  
(Тот же project_id, что в твоем JSON credentials)

### Шаг 2: Перейди в APIs & Services

1. Слева в меню: **APIs & Services** → **Dashboard**
2. Или прямая ссылка: https://console.cloud.google.com/apis/dashboard

### Шаг 3: Проверь что APIs ВКЛЮЧЕНЫ

В Dashboard должны быть видны:
- ✅ **Google Sheets API** - статус: **Enabled**
- ✅ **Google Drive API** - статус: **Enabled**

**Если их НЕТ в списке** → они НЕ ВКЛЮЧЕНЫ!

### Шаг 4: Включи APIs (если не включены)

#### 4.1. Google Sheets API

**Прямая ссылка:**  
https://console.cloud.google.com/apis/library/sheets.googleapis.com

1. Кликни на ссылку
2. **Убедись что выбран ПРАВИЛЬНЫЙ проект** (вверху справа)
3. Кликни большую синюю кнопку **ENABLE** (Включить)
4. Дождись "API enabled" (1-2 минуты)

#### 4.2. Google Drive API

**Прямая ссылка:**  
https://console.cloud.google.com/apis/library/drive.googleapis.com

1. Кликни на ссылку
2. **Убедись что выбран ПРАВИЛЬНЫЙ проект** (вверху справа)
3. Кликни большую синюю кнопку **ENABLE** (Включить)
4. Дождись "API enabled" (1-2 минуты)

### Шаг 5: Проверь в Dashboard

Вернись в Dashboard: https://console.cloud.google.com/apis/dashboard

Должно быть видно:
```
APIs:
- Google Sheets API     [Enabled]
- Google Drive API      [Enabled]
```

### Шаг 6: Подожди 2-3 минуты

**APIs активируются НЕ МГНОВЕННО!**

Даже если написано "Enabled" - подожди 2-3 минуты перед тестом.

### Шаг 7: Перезапусти Railway

Railway → Your App → **Restart**

---

## 🔍 КАК ПОНЯТЬ ЧТО ПРОЕКТ ПРАВИЛЬНЫЙ?

В твоем JSON credentials есть:
```json
{
  "project_id": "твой-проект-123456",
  ...
}
```

В Google Cloud Console **вверху справа** должен быть выбран:
```
Project: твой-проект-123456
```

**Если выбран другой проект** → APIs включены не там!

---

## 📋 БЫСТРЫЙ ЧЕКЛИСТ:

- [ ] Открыл https://console.cloud.google.com
- [ ] **Выбрал ПРАВИЛЬНЫЙ ПРОЕКТ** (вверху справа)
- [ ] Перешел в APIs & Services → Dashboard
- [ ] **Проверил что Google Sheets API = Enabled**
- [ ] **Проверил что Google Drive API = Enabled**
- [ ] Если не включены - включил через Library
- [ ] Подождал 2-3 минуты
- [ ] Перезапустил Railway
- [ ] Попробовал создать Google Sheets снова

---

## 🎯 100% СПОСОБ ПРОВЕРИТЬ:

### Команда в gcloud CLI (если установлен):

```bash
# Установи нужный проект
gcloud config set project твой-проект-123456

# Проверь включенные APIs
gcloud services list --enabled

# Должно быть в выводе:
# sheets.googleapis.com     Google Sheets API
# drive.googleapis.com      Google Drive API
```

### Если APIs не включены - включи:

```bash
gcloud services enable sheets.googleapis.com
gcloud services enable drive.googleapis.com
```

---

## ❗ ВАЖНО:

**403 "The caller does not have permission" ВСЕГДА означает:**

1. APIs не включены ИЛИ
2. APIs включены в ДРУГОМ проекте (не там где Service Account)

**Никакие права Service Account НЕ ПОМОГУТ, если APIs не включены!**

---

## 📸 СКРИНШОТ ДЛЯ ПРОВЕРКИ:

Сделай скриншот страницы:
https://console.cloud.google.com/apis/dashboard

И отправь - я увижу включены ли APIs!


