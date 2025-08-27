#!/usr/bin/env python3
"""
Personal Telegram Account Setup
Настройка автоматизации для личного аккаунта
"""

import json
import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from loguru import logger

class PersonalAccountSetup:
    def __init__(self):
        self.config_file = "config/personal_config.json"
        self.session_name = "personal_account"
        
    def get_api_credentials(self):
        """Получение API ключей от пользователя"""
        print("🔑 НАСТРОЙКА API КЛЮЧЕЙ TELEGRAM")
        print("=" * 50)
        print()
        print("1. Перейдите на https://my.telegram.org")
        print("2. Войдите в свой аккаунт Telegram")
        print("3. Перейдите в 'API development tools'")
        print("4. Создайте новое приложение:")
        print("   - App title: Personal Automation")
        print("   - Short name: personal_auto")
        print("   - Platform: Desktop")
        print("   - Description: Personal automation script")
        print()
        
        api_id = input("Введите API ID: ").strip()
        api_hash = input("Введите API Hash: ").strip()
        phone = input("Введите номер телефона (с кодом страны, например +7): ").strip()
        
        return {
            "api_id": api_id,
            "api_hash": api_hash,
            "phone": phone
        }
    
    def create_personal_config(self, credentials):
        """Создание конфигурации для личного аккаунта"""
        config = {
            "api_id": credentials["api_id"],
            "api_hash": credentials["api_hash"],
            "phone": credentials["phone"],
            "session_name": self.session_name,
            "settings": {
                "auto_reply": False,  # Отключено по умолчанию для безопасности
                "monitoring_enabled": True,
                "max_actions_per_hour": 5,  # Консервативный лимит
                "delay_between_actions": 10
            },
            "monitoring": {
                "target_chats": [],  # Будет заполнено позже
                "keywords": [
                    "важно",
                    "срочно", 
                    "внимание",
                    "напоминание",
                    "задача"
                ],
                "auto_save_important": True
            },
            "automation": {
                "auto_archive_old": True,
                "save_media": True,
                "backup_messages": True,
                "daily_summary": True
            },
            "safety": {
                "max_messages_per_day": 20,  # Очень консервативный лимит
                "cooldown_minutes": 60,  # Большая задержка
                "emergency_stop": False,
                "working_hours": {
                    "start": "09:00",
                    "end": "21:00"
                }
            },
            "notifications": {
                "daily_reminder": "09:00",
                "weekly_summary": "monday 10:00",
                "important_alerts": True
            }
        }
        
        # Создаем директорию config если её нет
        os.makedirs("config", exist_ok=True)
        
        # Сохраняем конфигурацию
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Конфигурация сохранена в {self.config_file}")
        return config
    
    async def test_connection(self, config):
        """Тестирование подключения к Telegram"""
        print("\n🔗 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ")
        print("-" * 30)
        
        try:
            client = TelegramClient(
                self.session_name,
                config["api_id"],
                config["api_hash"]
            )
            
            print("Подключение к Telegram...")
            await client.start(phone=config["phone"])
            
            if await client.is_user_authorized():
                print("✅ Успешная авторизация!")
                
                # Получаем информацию о пользователе
                me = await client.get_me()
                print(f"👤 Пользователь: {me.first_name} {me.last_name or ''}")
                print(f"📱 Номер: {me.phone}")
                print(f"🆔 ID: {me.id}")
                
                # Получаем список диалогов
                print("\n📋 Получение списка чатов...")
                dialogs = await client.get_dialogs(limit=10)
                
                print("Последние 10 чатов:")
                for i, dialog in enumerate(dialogs, 1):
                    chat_name = dialog.name or f"Чат {dialog.id}"
                    print(f"  {i}. {chat_name} (ID: {dialog.id})")
                
                await client.disconnect()
                return True
                
            else:
                print("❌ Ошибка авторизации")
                return False
                
        except SessionPasswordNeededError:
            print("⚠️  Требуется пароль двухфакторной аутентификации")
            print("   Введите пароль в появившемся окне")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def setup_automation_features(self):
        """Настройка функций автоматизации"""
        print("\n⚙️  НАСТРОЙКА ФУНКЦИЙ АВТОМАТИЗАЦИИ")
        print("-" * 40)
        
        features = {
            "daily_reminders": "Ежедневные напоминания",
            "message_monitoring": "Мониторинг важных сообщений", 
            "auto_archive": "Автоматическое архивирование старых чатов",
            "media_backup": "Сохранение медиафайлов",
            "keyword_alerts": "Уведомления по ключевым словам",
            "weekly_summary": "Еженедельная сводка активности"
        }
        
        enabled_features = []
        
        for feature, description in features.items():
            response = input(f"Включить {description}? (y/n): ").strip().lower()
            if response in ['y', 'yes', 'да', 'д']:
                enabled_features.append(feature)
        
        return enabled_features
    
    def create_custom_automation_script(self, config, features):
        """Создание персонализированного скрипта автоматизации"""
        script_content = f'''#!/usr/bin/env python3
"""
Personal Telegram Automation
Автоматизация для личного аккаунта {config['phone']}
"""

import asyncio
import json
from datetime import datetime, time
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from loguru import logger
import os

class PersonalTelegramAutomation:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        self.daily_message_count = 0
        self.last_action_time = None
        
        # Настройка логирования
        logger.add("output/logs/personal_automation.log", rotation="1 day", retention="7 days")
        
    def load_config(self):
        with open("config/personal_config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def connect(self):
        try:
            self.client = TelegramClient(
                self.config['session_name'],
                self.config['api_id'],
                self.config['api_hash']
            )
            
            await self.client.start(phone=self.config['phone'])
            logger.info("Подключение к личному аккаунту установлено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения: {{e}}")
            return False
    
    def is_working_hours(self):
        """Проверка рабочих часов"""
        now = datetime.now().time()
        start_time = time.fromisoformat(self.config['safety']['working_hours']['start'])
        end_time = time.fromisoformat(self.config['safety']['working_hours']['end'])
        
        return start_time <= now <= end_time
    
    async def send_daily_reminder(self):
        """Отправка ежедневного напоминания"""
        if 'daily_reminders' in {self.config.get('enabled_features', [])}:
            message = f"🌅 Доброе утро! Время: {{datetime.now().strftime('%H:%M')}}\\n\\n"
            message += "📋 Задачи на сегодня:\\n"
            message += "• Проверить важные сообщения\\n"
            message += "• Обновить статус задач\\n"
            message += "• Планирование на завтра"
            
            # Отправляем себе
            await self.send_message_to_self(message)
    
    async def send_message_to_self(self, message):
        """Отправка сообщения самому себе"""
        try:
            me = await self.client.get_me()
            await self.client.send_message(me.id, message)
            logger.info("Сообщение отправлено самому себе")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {{e}}")
    
    async def monitor_important_messages(self):
        """Мониторинг важных сообщений"""
        if 'message_monitoring' not in {self.config.get('enabled_features', [])}:
            return
        
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                sender = await event.get_sender()
                message_text = event.message.text
                
                # Проверяем ключевые слова
                keywords = self.config['monitoring']['keywords']
                for keyword in keywords:
                    if keyword.lower() in message_text.lower():
                        alert = f"🚨 ВАЖНОЕ СООБЩЕНИЕ!\\n"
                        alert += f"От: {{sender.first_name if sender else 'Unknown'}}\\n"
                        alert += f"Текст: {{message_text[:100]}}..."
                        
                        await self.send_message_to_self(alert)
                        logger.info(f"Найдено ключевое слово: {{keyword}}")
                        break
                        
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения: {{e}}")
    
    async def start_automation(self):
        """Запуск автоматизации"""
        logger.info("Запуск персональной автоматизации Telegram")
        
        # Настройка мониторинга
        await self.monitor_important_messages()
        
        # Запуск клиента
        await self.client.run_until_disconnected()

async def main():
    automation = PersonalTelegramAutomation()
    
    if await automation.connect():
        await automation.start_automation()
    else:
        logger.error("Не удалось подключиться к Telegram")

if __name__ == "__main__":
    os.makedirs("output/logs", exist_ok=True)
    asyncio.run(main())
'''
        
        # Сохраняем скрипт
        script_path = "scripts/personal_automation.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ Персонализированный скрипт создан: {script_path}")
        return script_path
    
    def create_startup_script(self):
        """Создание скрипта для быстрого запуска"""
        startup_content = '''#!/usr/bin/env python3
"""
Quick Start Personal Automation
Быстрый запуск персональной автоматизации
"""

import subprocess
import sys
import os

def main():
    print("🚀 Запуск персональной автоматизации Telegram...")
    
    # Проверяем наличие конфигурации
    if not os.path.exists("config/personal_config.json"):
        print("❌ Конфигурация не найдена!")
        print("Запустите сначала: python scripts/personal_account_setup.py")
        return
    
    # Запускаем автоматизацию
    try:
        subprocess.run([sys.executable, "scripts/personal_automation.py"])
    except KeyboardInterrupt:
        print("\\n⏹️  Остановка автоматизации...")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    main()
'''
        
        with open("start_personal_automation.py", 'w', encoding='utf-8') as f:
            f.write(startup_content)
        
        print("✅ Скрипт быстрого запуска создан: start_personal_automation.py")

async def main():
    """Главная функция настройки"""
    print("🤖 НАСТРОЙКА ПЕРСОНАЛЬНОЙ АВТОМАТИЗАЦИИ TELEGRAM")
    print("=" * 60)
    print()
    
    setup = PersonalAccountSetup()
    
    # Получение API ключей
    credentials = setup.get_api_credentials()
    
    # Создание конфигурации
    config = setup.create_personal_config(credentials)
    
    # Тестирование подключения
    success = await setup.test_connection(config)
    
    if not success:
        print("❌ Не удалось подключиться к Telegram")
        print("Проверьте API ключи и попробуйте снова")
        return
    
    # Настройка функций
    features = setup.setup_automation_features()
    
    # Обновляем конфигурацию с включенными функциями
    config['enabled_features'] = features
    with open(setup.config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    # Создание скриптов
    setup.create_custom_automation_script(config, features)
    setup.create_startup_script()
    
    print("\n" + "=" * 60)
    print("✅ НАСТРОЙКА ЗАВЕРШЕНА!")
    print()
    print("🚀 Для запуска автоматизации используйте:")
    print("   python start_personal_automation.py")
    print()
    print("📁 Файлы созданы:")
    print("   • config/personal_config.json - конфигурация")
    print("   • scripts/personal_automation.py - основной скрипт")
    print("   • start_personal_automation.py - быстрый запуск")
    print()
    print("⚠️  ВАЖНО:")
    print("   • Используйте только для личных целей")
    print("   • Соблюдайте лимиты безопасности")
    print("   • Регулярно проверяйте логи")

if __name__ == "__main__":
    asyncio.run(main())
