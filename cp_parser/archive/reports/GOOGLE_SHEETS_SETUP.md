# Google Sheets Integration - Setup Guide

## ✅ Реализовано

- ✅ Создание Google Spreadsheet через Service Account
- ✅ **Публичные права: anyone with link can EDIT**
- ✅ Автоматическое форматирование (заголовки, курсив, автоширина)
- ✅ API endpoint `/api/kp/generate/google-sheets`
- ✅ UI кнопка (синяя, с иконкой графиков)
- ✅ Автоматическое открытие в новой вкладке

---

## 🔧 Настройка (для Railway)

### 1. Google Service Account

У тебя уже есть Google Cloud credentials! Нужно добавить их в Railway.

### 2. Переменные окружения

Добавь в Railway переменную:

```
GOOGLE_CREDENTIALS_JSON
```

**Значение:** JSON содержимое файла Service Account credentials.

**Формат:**
```json
{
  "type": "service_account",
  "project_id": "ваш-проект",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "service-account@ваш-проект.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

### 3. Проверка

После деплоя:
1. Зайди в `/kp`
2. Добавь товары в КП
3. Кликни синюю кнопку **Google Sheets**
4. Откроется новая вкладка с таблицей
5. **Проверь права:** Share → Anyone with the link → Editor

---

## 📋 Как работает

1. **Создание таблицы:**
   ```python
   spreadsheet = sheets_service.spreadsheets().create(...)
   ```

2. **Установка публичных прав:**
   ```python
   permission = {
       'type': 'anyone',
       'role': 'writer'  # EDITOR права!
   }
   drive_service.permissions().create(...)
   ```

3. **Заполнение данными:**
   ```python
   sheets_service.spreadsheets().values().update(...)
   ```

4. **Форматирование:**
   - Заголовок: жирный, 16px, центр
   - Дата: курсив, центр
   - Автоподбор ширины колонок

---

## 🎨 UI

**Кнопка:** Синяя (bg-blue-600)  
**Иконка:** График (bars chart)  
**Действие:** Открывает таблицу в новой вкладке  
**Уведомление:** "Google Sheets создан! Открываю в новой вкладке..."

---

## 🐛 Troubleshooting

### Ошибка: "GOOGLE_CREDENTIALS_JSON не найден"
- Проверь переменную окружения в Railway
- Убедись что JSON валидный (без переносов строк в ключах)

### Ошибка: "Недостаточно прав"
- Проверь что Service Account имеет права на создание файлов в Google Drive
- Убедись что включены APIs: Google Sheets API, Google Drive API

### Таблица создана, но нет прав на редактирование
- Проверь что `role: 'writer'` в коде (не 'reader')
- Проверь логи Railway: должно быть "Установлены публичные права на редактирование"

---

## 📦 Зависимости

Автоматически установятся при деплое:
- `google-auth==2.23.4`
- `google-auth-oauthlib==1.1.0`
- `google-api-python-client==2.108.0`

---

## 🚀 Готово!

После настройки GOOGLE_CREDENTIALS_JSON в Railway - всё будет работать автоматически!


