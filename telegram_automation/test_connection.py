#!/usr/bin/env python3
"""
Test Telegram Connection
Простой тест подключения к Telegram
"""

import asyncio
import json
import getpass
from telethon import TelegramClient
from loguru import logger

class TelegramConnectionTest:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        
    def load_config(self):
        with open("config/personal_config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    
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
    
    async def test_connection(self):
        """Тестирование подключения"""
        try:
            print("🔗 Тестирование подключения к Telegram...")
            print(f"📱 Номер: {self.config['phone']}")
            print(f"🆔 API ID: {self.config['api_id']}")
            print()
            
            self.client = TelegramClient(
                self.config['session_name'],
                self.config['api_id'],
                self.config['api_hash']
            )
            
            # Подключение с обработчиками
            await self.client.start(
                phone=self.config['phone'],
                code_callback=self.code_callback,
                password_callback=self.password_callback
            )
            
            # Проверяем авторизацию
            if await self.client.is_user_authorized():
                print("✅ Успешная авторизация!")
                
                # Получаем информацию о пользователе
                me = await self.client.get_me()
                print(f"👤 Пользователь: {me.first_name} {me.last_name or ''}")
                print(f"📱 Номер: {me.phone}")
                print(f"🆔 ID: {me.id}")
                print(f"👤 Username: @{me.username or 'нет'}")
                
                # Тестируем отправку сообщения
                print("\n📤 Тестирование отправки сообщения...")
                test_message = "🤖 Тест подключения\n✅ Автоматизация работает!"
                await self.client.send_message(me.id, test_message)
                print("✅ Тестовое сообщение отправлено!")
                
                # Получаем список чатов
                print("\n📋 Получение списка чатов...")
                dialogs = await self.client.get_dialogs(limit=5)
                print("Последние 5 чатов:")
                for i, dialog in enumerate(dialogs, 1):
                    chat_name = dialog.name or f"Чат {dialog.id}"
                    print(f"  {i}. {chat_name} (ID: {dialog.id})")
                
                print("\n🎉 Тест подключения прошел успешно!")
                print("✅ Ваш аккаунт готов к автоматизации")
                
                return True
                
            else:
                print("❌ Не удалось авторизоваться")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
        finally:
            if self.client:
                await self.client.disconnect()

async def main():
    print("🤖 ТЕСТ ПОДКЛЮЧЕНИЯ TELEGRAM")
    print("=" * 40)
    print()
    
    test = TelegramConnectionTest()
    success = await test.test_connection()
    
    if success:
        print("\n🚀 Теперь можете запустить автоматизацию:")
        print("   python3 easy_automation.py")
    else:
        print("\n❌ Подключение не удалось")
        print("💡 Проверьте:")
        print("   • API ключи в config/personal_config.json")
        print("   • Номер телефона")
        print("   • Интернет-соединение")

if __name__ == "__main__":
    asyncio.run(main())
