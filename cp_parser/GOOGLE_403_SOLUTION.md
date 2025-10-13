# 🔴 РЕШЕНИЕ: Google Sheets API - 403 PERMISSION_DENIED

## Ошибка: "The caller does not have permission"

**Даже если APIs включены**, ошибка 403 может быть из-за:

1. ❌ **Billing не настроен** (обязательно!)
2. ❌ **Service Account не имеет прав**
3. ❌ **APIs включены в ДРУГОМ проекте**

---

## 🎯 БЫСТРАЯ ДИАГНОСТИКА

Запусти локально (с теми же credentials что на Railway):

```bash
cd projects/cp_parser

# Экспортируй переменную
export GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"...",...}'

# Запусти диагностику
py diagnose_google_api.py
```

**Скрипт проверит:**
- ✅ Валидность JSON
- ✅ Формат private_key
- ✅ Доступ к Sheets API
- ✅ Доступ к Drive API
- ✅ Создание тестовой таблицы

---

## ✅ РЕШЕНИЕ 1: НАСТРОЙ BILLING (ОБЯЗАТЕЛЬНО!)

### Google требует привязку карты даже для бесплатного использования!

**Шаг 1: Открой Billing**

Замени `YOUR-PROJECT-ID` на свой project_id:

```
https://console.cloud.google.com/billing/linkedaccount?project=YOUR-PROJECT-ID
```

**Шаг 2: Проверь статус**

Должно быть:
```
✅ Billing account linked: My Billing Account
```

Если написано "No billing account":
```
❌ No billing account linked
```

**ЭТО ПРИЧИНА 403!**

**Шаг 3: Привяжи Billing Account**

1. Кликни **"Link a billing account"**
2. Выбери существующий Billing Account ИЛИ создай новый:
   - Name: My Billing Account
   - Country: Выбери страну
   - Add payment method: Добавь карту

**⚠️ ВАЖНО:** Google не спишет деньги за использование Sheets API (бесплатный лимит огромный), но карта **обязательна** для активации!

**Шаг 4: Подожди 2-3 минуты**

После привязки Billing Account подожди активации.

**Шаг 5: Перезапусти Railway**

Railway → Your App → **Restart**

---

## ✅ РЕШЕНИЕ 2: НАСТРОЙ IAM РОЛИ

### Service Account должен иметь права создавать файлы!

**Шаг 1: Открой IAM**

Замени `YOUR-PROJECT-ID`:

```
https://console.cloud.google.com/iam-admin/iam?project=YOUR-PROJECT-ID
```

**Шаг 2: Найди свой Service Account**

Ищи строку с email:
```
your-service-account@your-project.iam.gserviceaccount.com
```

**Шаг 3: Проверь роли**

Должна быть **хотя бы одна** из ролей:

**Вариант A (рекомендуется для прода):**
```
✅ Editor
```

**Вариант B (максимальные права):**
```
✅ Owner
```

**Вариант C (минимальные права):**
```
✅ Service Usage Consumer
✅ Storage Admin (для Drive)
```

**Если ролей НЕТ или есть только "Service Account User":**

**ЭТО ПРИЧИНА 403!**

**Шаг 4: Добавь роли**

1. Кликни на карандаш (Edit) возле Service Account
2. Кликни **"+ ADD ANOTHER ROLE"**
3. Выбери: **"Editor"**
4. Кликни **"Save"**

**Шаг 5: Подожди 1-2 минуты**

Права применяются не мгновенно.

**Шаг 6: Перезапусти Railway**

Railway → Your App → **Restart**

---

## ✅ РЕШЕНИЕ 3: ПРОВЕРЬ ЧТО APIs В ПРАВИЛЬНОМ ПРОЕКТЕ

### APIs должны быть включены В ТОМ ЖЕ проекте где Service Account!

**Шаг 1: Узнай Project ID из credentials**

```json
{
  "type": "service_account",
  "project_id": "quickstart-1591698112539",  <-- ЭТО ТВОЙ PROJECT ID
  ...
}
```

**Шаг 2: Открой Google Cloud Console**

```
https://console.cloud.google.com
```

**Шаг 3: ВЫБЕРИ ПРАВИЛЬНЫЙ ПРОЕКТ**

**Вверху справа** в dropdown должен быть выбран:
```
✅ quickstart-1591698112539
```

**Если выбран другой проект** → APIs включены не там!

**Шаг 4: Проверь APIs в ЭТОМ проекте**

```
https://console.cloud.google.com/apis/dashboard?project=quickstart-1591698112539
```

Должны быть:
```
✅ Google Sheets API - Enabled
✅ Google Drive API - Enabled
```

---

## 🔍 ПОРЯДОК ДЕЙСТВИЙ (ЧЕКЛИСТ)

### 1. Проверка Billing (САМОЕ ВАЖНОЕ!)

- [ ] Открыл: https://console.cloud.google.com/billing/linkedaccount?project=YOUR-PROJECT-ID
- [ ] Вижу: "Billing account linked" ✅
- [ ] Если нет → привязал Billing Account с картой
- [ ] Подождал 2-3 минуты

### 2. Проверка IAM ролей

- [ ] Открыл: https://console.cloud.google.com/iam-admin/iam?project=YOUR-PROJECT-ID
- [ ] Нашел мой Service Account email
- [ ] Проверил что есть роль "Editor" или "Owner"
- [ ] Если нет → добавил роль "Editor"
- [ ] Подождал 1-2 минуты

### 3. Проверка правильного проекта

- [ ] В Google Cloud Console выбран ПРАВИЛЬНЫЙ проект (вверху справа)
- [ ] Project ID = тот же что в JSON credentials
- [ ] APIs включены в ЭТОМ проекте

### 4. Перезапуск Railway

- [ ] Railway → Your App → Restart
- [ ] Проверил логи на наличие автопроверки API
- [ ] Попробовал создать Google Sheets снова

---

## 🧪 ТЕСТ ПОСЛЕ ИСПРАВЛЕНИЙ

```bash
# Локально
export GOOGLE_CREDENTIALS_JSON='...'
py diagnose_google_api.py
```

**Должно быть:**
```
✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!
🎉 Google Sheets API полностью настроен и работает!
```

**Если всё равно ошибка** → скинь полный вывод скрипта, разберемся!

---

## 📞 ДОПОЛНИТЕЛЬНАЯ ПОМОЩЬ

**Если после всех проверок всё равно 403:**

1. Скинь вывод `diagnose_google_api.py`
2. Скинь скриншот:
   - Billing page
   - IAM page (Service Account строка)
   - APIs Dashboard

**99% что проблема в Billing или IAM!**

