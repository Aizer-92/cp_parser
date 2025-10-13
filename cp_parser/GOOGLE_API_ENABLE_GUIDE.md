# Google Sheets API - Включение и настройка

## ❌ Ошибка: 403 "The caller does not have permission"

**Причина:** Service Account не имеет прав на создание Google Sheets.

---

## ✅ РЕШЕНИЕ: Включить APIs в Google Cloud Console

### Шаг 1: Открой Google Cloud Console

1. Перейди на: https://console.cloud.google.com
2. Выбери свой проект (тот же, что в `project_id` из credentials)

### Шаг 2: Включи Google Sheets API

1. Перейди: **APIs & Services** → **Library**
2. Найди: **"Google Sheets API"**
3. Кликни на него
4. Нажми **"ENABLE"** (Включить)

### Шаг 3: Включи Google Drive API

1. Снова: **APIs & Services** → **Library**
2. Найди: **"Google Drive API"**
3. Кликни на него
4. Нажми **"ENABLE"** (Включить)

### Шаг 4: Проверь Service Account

1. Перейди: **IAM & Admin** → **Service Accounts**
2. Найди свой Service Account (email из credentials)
3. Убедись что он существует и активен

---

## 📋 БЫСТРАЯ ПРОВЕРКА

### 1. Проверь `GOOGLE_CREDENTIALS_JSON` в Railway:

```json
{
  "type": "service_account",
  "project_id": "твой-проект-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "service-account-name@твой-проект.iam.gserviceaccount.com",
  ...
}
```

**⚠️ Важно:**
- `client_email` должен быть полным (с `@...iam.gserviceaccount.com`)
- `private_key` должен содержать `\n` (переводы строк как `\n`, не настоящие переводы!)

### 2. Включены ли APIs?

Проверь на странице: https://console.cloud.google.com/apis/dashboard

Должны быть ENABLED:
- ✅ **Google Sheets API**
- ✅ **Google Drive API**

---

## 🔧 АЛЬТЕРНАТИВНЫЙ СПОСОБ: Включить через gcloud CLI

```bash
# Если у тебя установлен gcloud CLI
gcloud services enable sheets.googleapis.com
gcloud services enable drive.googleapis.com
```

---

## 🧪 ТЕСТ ПОСЛЕ ВКЛЮЧЕНИЯ

1. Включи APIs (Sheets + Drive)
2. Подожди **1-2 минуты** (APIs активируются не мгновенно)
3. Перезапусти приложение на Railway
4. Попробуй создать Google Sheets снова

---

## 📞 ЕСЛИ ОШИБКА ОСТАЛАСЬ:

### Проверь логи Railway:

```
✅ [Google Sheets] API инициализирован
```

Если видишь:
```
⚠️ [Google Sheets] GOOGLE_CREDENTIALS_JSON не найден в .env
```
→ Credentials не загружены, проверь переменную окружения

Если видишь:
```
❌ [Google Sheets] Ошибка инициализации API: ...
```
→ Credentials невалидные, проверь JSON формат

---

## 🎯 QUICK FIX CHECKLIST:

- [ ] Google Cloud Console → APIs & Services → Library
- [ ] Включил **Google Sheets API** (ENABLE)
- [ ] Включил **Google Drive API** (ENABLE)
- [ ] Подождал 1-2 минуты
- [ ] Перезапустил приложение на Railway
- [ ] Проверил что `GOOGLE_CREDENTIALS_JSON` корректный

---

## 💡 СОВЕТ:

Если APIs уже включены, но ошибка осталась:
1. Попробуй **создать новый Service Account**
2. Скачай новые credentials
3. Обнови `GOOGLE_CREDENTIALS_JSON` в Railway
4. Перезапусти

---

**После включения APIs - всё заработает!** 🚀

