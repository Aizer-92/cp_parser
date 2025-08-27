#!/usr/bin/env python3
"""
Easy Personal Telegram Automation
Упрощенная автоматизация с лучшей обработкой авторизации
"""

import asyncio
import json
import getpass
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from loguru import logger
import os

class EasyTelegramAutomation:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        
        # Настройка логирования
        os.makedirs("output/logs", exist_ok=True)
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
            
            print("🔗 Подключение к Telegram...")
            
            # Настраиваем обработчики для кодов и паролей
            await self.client.start(
                phone=self.config['phone'],
                code_callback=self.code_callback,
                password_callback=self.password_callback
            )
            
            # Проверяем авторизацию
            if await self.client.is_user_authorized():
                logger.info("✅ Успешная авторизация")
                
                # Получаем информацию о пользователе
                me = await self.client.get_me()
                print(f"👤 Подключен как: {me.first_name} {me.last_name or ''}")
                print(f"📱 Номер: {me.phone}")
                print(f"🆔 ID: {me.id}")
                
                return True
            else:
                print("❌ Не удалось авторизоваться")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            print(f"❌ Ошибка: {e}")
            return False
    
    def code_callback(self):
        """Обработчик для кода подтверждения"""
        print("\n📱 Введите код подтверждения из Telegram:")
        print("💡 Код придет в виде SMS или в приложение Telegram")
        code = input("Код: ").strip()
        return code
    
    def password_callback(self):
        """Обработчик для пароля двухфакторной аутентификации"""
        print("\n🔐 Введите пароль двухфакторной аутентификации:")
        print("💡 Пароль не будет отображаться при вводе (это нормально)")
        password = getpass.getpass("Пароль: ")
        return password
    
    async def send_message_to_self(self, message):
        """Отправка сообщения самому себе"""
        try:
            me = await self.client.get_me()
            await self.client.send_message(me.id, message)
            logger.info("✅ Сообщение отправлено самому себе")
            print("✅ Сообщение отправлено!")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки: {e}")
            print(f"❌ Ошибка отправки: {e}")
    
    async def test_connection(self):
        """Тестирование подключения"""
        try:
            # Отправляем тестовое сообщение
            test_message = "🤖 Тест автоматизации Telegram\n✅ Подключение работает!"
            await self.send_message_to_self(test_message)
            return True
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False
    
    async def monitor_messages(self):
        """Мониторинг важных сообщений"""
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                sender = await event.get_sender()
                message_text = event.message.text
                
                # Логируем все сообщения
                sender_name = sender.first_name if sender else "Unknown"
                logger.info(f"📨 Новое сообщение от {sender_name}: {message_text[:50]}...")
                
                # Проверяем ключевые слова
                keywords = self.config['monitoring']['keywords']
                for keyword in keywords:
                    if keyword.lower() in message_text.lower():
                        alert = f"🚨 ВАЖНОЕ СООБЩЕНИЕ!\n"
                        alert += f"От: {sender_name}\n"
                        alert += f"Текст: {message_text[:100]}..."
                        
                        await self.send_message_to_self(alert)
                        logger.info(f"🔍 Найдено ключевое слово: {keyword}")
                        print(f"🔍 Найдено ключевое слово: {keyword}")
                        break
                        
            except Exception as e:
                logger.error(f"❌ Ошибка обработки сообщения: {e}")
    
    async def start_automation(self):
        """Запуск автоматизации"""
        logger.info("🚀 Запуск персональной автоматизации")
        print("🚀 Автоматизация запущена!")
        print("📋 Функции:")
        print("   • Мониторинг важных сообщений")
        print("   • Уведомления по ключевым словам")
        print("   • Отправка сообщений самому себе")
        print()
        print("💡 Для остановки нажмите Ctrl+C")
        print("-" * 50)
        
        # Тестируем подключение
        if await self.test_connection():
            print("✅ Тест подключения прошел успешно")
        else:
            print("❌ Тест подключения не прошел")
        
        # Настройка мониторинга
        await self.monitor_messages()
        
        # Запуск клиента
        await self.client.run_until_disconnected()

async def main():
    automation = EasyTelegramAutomation()
    
    if await automation.connect():
        await automation.start_automation()
    else:
        print("❌ Не удалось подключиться к Telegram")
        print("\n💡 Попробуйте:")
        print("   1. Проверить API ключи")
        print("   2. Убедиться, что номер телефона правильный")
        print("   3. Проверить интернет-соединение")

if __name__ == "__main__":
    asyncio.run(main())
