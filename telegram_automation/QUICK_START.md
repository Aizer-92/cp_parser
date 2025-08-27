# 🚀 Quick Start Guide - Telegram Automation

## Быстрый старт за 5 минут

### 1. Установка зависимостей
```bash
cd projects/telegram_automation
pip install -r requirements.txt
```

### 2. Настройка Telegram Bot (Рекомендуется)

#### Создание бота:
1. Откройте @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Сохраните токен бота

#### Настройка конфигурации:
```bash
# Отредактируйте config/bot_config.json
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "chat_id": "YOUR_CHAT_ID_HERE",
  "settings": {
    "auto_reply": true,
    "daily_notifications": true
  }
}
```

#### Запуск бота:
```bash
python scripts/bot_automation.py
```

### 3. Настройка пользовательского аккаунта (Осторожно!)

#### Получение API ключей:
1. Перейдите на https://my.telegram.org
2. Войдите в аккаунт
3. Создайте приложение
4. Сохраните API ID и API Hash

#### Настройка конфигурации:
```bash
# Отредактируйте config/user_config.json
{
  "api_id": "YOUR_API_ID_HERE",
  "api_hash": "YOUR_API_HASH_HERE",
  "phone": "YOUR_PHONE_NUMBER_HERE",
  "settings": {
    "monitoring_enabled": true,
    "max_actions_per_hour": 10
  }
}
```

#### Запуск автоматизации:
```bash
python scripts/user_automation.py
```

## 🔧 Основные команды

### Для бота:
- `/start` - Запуск бота
- `/help` - Справка
- `/status` - Статус бота
- `/schedule` - Расписание уведомлений

### Для пользовательского аккаунта:
- Мониторинг сообщений
- Автоответы
- Архивирование чатов
- Сохранение медиафайлов

## ⚠️ Важные предупреждения

1. **Безопасность**: Никогда не делитесь API ключами
2. **Лимиты**: Соблюдайте ограничения Telegram
3. **ToS**: Пользовательский аккаунт может нарушать условия использования
4. **Тестирование**: Используйте отдельный номер для тестов

## 📁 Структура проекта

```
telegram_automation/
├── config/           # Конфигурационные файлы
├── scripts/          # Основные скрипты
├── output/           # Логи и результаты
└── README.md         # Полная документация
```

## 🆘 Получение помощи

1. Запустите интерактивное руководство:
```bash
python scripts/setup_guide.py
```

2. Проверьте логи в `output/logs/`

3. Ознакомьтесь с полной документацией в `README.md`

## 🎯 Примеры использования

### Отправка уведомления через бота:
```python
import asyncio
from scripts.bot_automation import TelegramBotAutomation

async def send_notification():
    bot = TelegramBotAutomation()
    await bot.send_notification("Важное сообщение!")

asyncio.run(send_notification())
```

### Мониторинг сообщений:
```python
import asyncio
from scripts.user_automation import TelegramUserAutomation

async def monitor():
    automation = TelegramUserAutomation()
    if await automation.connect():
        await automation.start_monitoring()

asyncio.run(monitor())
```

## 🔄 Обновления

Регулярно проверяйте обновления библиотек:
```bash
pip install --upgrade python-telegram-bot telethon
```

---

**Готово!** Ваша автоматизация Telegram настроена и готова к использованию. 🎉
