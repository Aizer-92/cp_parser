#!/usr/bin/env python3
"""
Complete Telegram Authorization
Завершение процесса авторизации в Telegram
"""

import asyncio
import json
import getpass
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

class AuthCompleter:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        
    def load_config(self):
        with open("config/personal_config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def complete_auth(self):
        """Завершение авторизации"""
        try:
            print("🔐 ЗАВЕРШЕНИЕ АВТОРИЗАЦИИ TELEGRAM")
            print("=" * 50)
            print()
            
            self.client = TelegramClient(
                self.config['session_name'],
                self.config['api_id'],
                self.config['api_hash']
            )
            
            print("🔗 Подключение к Telegram...")
            print(f"📱 Номер: {self.config['phone']}")
            print()
            
            # Запускаем процесс авторизации
            await self.client.connect()
            
            # Проверяем, авторизован ли уже пользователь
            if await self.client.is_user_authorized():
                print("✅ Пользователь уже авторизован!")
                me = await self.client.get_me()
                print(f"👤 Пользователь: {me.first_name} {me.last_name or ''}")
                print(f"📱 Номер: {me.phone}")
                return True
            
            # Если не авторизован, начинаем процесс
            print("📱 Начинаем процесс авторизации...")
            print("💡 Вам придет код подтверждения")
            
            # Отправляем код
            await self.client.send_code_request(self.config['phone'])
            print("✅ Код подтверждения отправлен!")
            
            # Запрашиваем код у пользователя
            print("\n📱 Введите код подтверждения:")
            code = input("Код: ").strip()
            
            try:
                # Пытаемся войти с кодом
                await self.client.sign_in(self.config['phone'], code)
                print("✅ Код принят!")
                
                # Проверяем, нужен ли пароль двухфакторной аутентификации
                if await self.client.is_user_authorized():
                    me = await self.client.get_me()
                    print(f"👤 Авторизация завершена!")
                    print(f"👤 Пользователь: {me.first_name} {me.last_name or ''}")
                    print(f"📱 Номер: {me.phone}")
                    return True
                    
            except SessionPasswordNeededError:
                print("\n🔐 Требуется пароль двухфакторной аутентификации")
                print("💡 Пароль не будет отображаться при вводе")
                
                while True:
                    password = getpass.getpass("Пароль: ")
                    try:
                        await self.client.sign_in(password=password)
                        print("✅ Пароль принят!")
                        
                        me = await self.client.get_me()
                        print(f"👤 Авторизация завершена!")
                        print(f"👤 Пользователь: {me.first_name} {me.last_name or ''}")
                        print(f"📱 Номер: {me.phone}")
                        return True
                        
                    except Exception as e:
                        print(f"❌ Неверный пароль: {e}")
                        retry = input("Попробовать еще раз? (y/n): ").strip().lower()
                        if retry not in ['y', 'yes', 'да', 'д']:
                            break
                            
            except PhoneCodeInvalidError:
                print("❌ Неверный код подтверждения")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            return False
        finally:
            if self.client:
                await self.client.disconnect()
    
    async def test_connection(self):
        """Тестирование подключения после авторизации"""
        try:
            print("\n🧪 Тестирование подключения...")
            
            self.client = TelegramClient(
                self.config['session_name'],
                self.config['api_id'],
                self.config['api_hash']
            )
            
            await self.client.start()
            
            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                print(f"✅ Подключение работает!")
                print(f"👤 Пользователь: {me.first_name}")
                
                # Тестируем отправку сообщения
                test_message = "🤖 Тест авторизации\n✅ Подключение работает!"
                await self.client.send_message(me.id, test_message)
                print("✅ Тестовое сообщение отправлено!")
                
                return True
            else:
                print("❌ Пользователь не авторизован")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False
        finally:
            if self.client:
                await self.client.disconnect()

async def main():
    auth = AuthCompleter()
    
    # Завершаем авторизацию
    success = await auth.complete_auth()
    
    if success:
        print("\n🎉 Авторизация завершена успешно!")
        
        # Тестируем подключение
        test_success = await auth.test_connection()
        
        if test_success:
            print("\n🚀 Теперь можете запустить автоматизацию:")
            print("   python3 easy_automation.py")
        else:
            print("\n❌ Тестирование не прошло")
    else:
        print("\n❌ Авторизация не завершена")
        print("💡 Попробуйте еще раз")

if __name__ == "__main__":
    asyncio.run(main())
