#!/usr/bin/env python3
"""
Chat History Analyzer
Анализатор истории чатов Telegram
"""

import asyncio
import json
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from loguru import logger
import os

class ChatHistoryAnalyzer:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        
        # Настройка логирования
        os.makedirs("output/logs", exist_ok=True)
        logger.add("output/logs/chat_history.log", rotation="1 day", retention="7 days")
        
    def load_config(self):
        with open("config/personal_config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def connect(self):
        """Подключение к Telegram"""
        try:
            self.client = TelegramClient(
                self.config['session_name'],
                self.config['api_id'],
                self.config['api_hash']
            )
            
            await self.client.start()
            
            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                print(f"👤 Подключен как: {me.first_name}")
                return True
            else:
                print("❌ Не удалось авторизоваться")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    async def get_chat_list(self):
        """Получение списка всех чатов"""
        try:
            dialogs = await self.client.get_dialogs()
            print(f"\n📋 Найдено {len(dialogs)} чатов:")
            print("-" * 50)
            
            for i, dialog in enumerate(dialogs, 1):
                chat_name = dialog.name or f"Чат {dialog.id}"
                chat_type = "Личный" if dialog.is_user else "Группа" if dialog.is_group else "Канал"
                print(f"{i:2d}. {chat_name} ({chat_type}) - ID: {dialog.id}")
            
            return dialogs
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка чатов: {e}")
            return []
    
    async def get_chat_history(self, chat_id, limit=100, offset_date=None):
        """Получение истории чата"""
        try:
            print(f"\n📖 Получение истории чата {chat_id}...")
            
            # Получаем сообщения
            messages = await self.client.get_messages(
                chat_id, 
                limit=limit,
                offset_date=offset_date
            )
            
            print(f"✅ Получено {len(messages)} сообщений")
            
            # Анализируем сообщения
            history_data = []
            for msg in messages:
                if msg.text:  # Только текстовые сообщения
                    sender = await msg.get_sender()
                    sender_name = sender.first_name if sender else "Unknown"
                    
                    history_data.append({
                        'id': msg.id,
                        'date': msg.date.isoformat(),
                        'sender': sender_name,
                        'text': msg.text,
                        'reply_to': msg.reply_to_msg_id if msg.reply_to_msg_id else None
                    })
            
            return history_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения истории: {e}")
            return []
    
    async def search_messages(self, chat_id, query, limit=50):
        """Поиск сообщений в чате"""
        try:
            print(f"\n🔍 Поиск сообщений с '{query}' в чате {chat_id}...")
            
            messages = await self.client.get_messages(
                chat_id,
                search=query,
                limit=limit
            )
            
            print(f"✅ Найдено {len(messages)} сообщений")
            
            search_results = []
            for msg in messages:
                if msg.text:
                    sender = await msg.get_sender()
                    sender_name = sender.first_name if sender else "Unknown"
                    
                    search_results.append({
                        'id': msg.id,
                        'date': msg.date.isoformat(),
                        'sender': sender_name,
                        'text': msg.text
                    })
            
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return []
    
    async def analyze_chat_activity(self, chat_id, days=7):
        """Анализ активности в чате"""
        try:
            print(f"\n📊 Анализ активности за последние {days} дней...")
            
            # Вычисляем дату начала
            start_date = datetime.now() - timedelta(days=days)
            
            # Получаем сообщения за период
            messages = await self.client.get_messages(
                chat_id,
                offset_date=start_date,
                limit=1000
            )
            
            # Анализируем активность
            activity_data = {}
            for msg in messages:
                if msg.text:
                    sender = await msg.get_sender()
                    sender_name = sender.first_name if sender else "Unknown"
                    
                    date_key = msg.date.strftime('%Y-%m-%d')
                    if date_key not in activity_data:
                        activity_data[date_key] = {'total': 0, 'users': {}}
                    
                    activity_data[date_key]['total'] += 1
                    if sender_name not in activity_data[date_key]['users']:
                        activity_data[date_key]['users'][sender_name] = 0
                    activity_data[date_key]['users'][sender_name] += 1
            
            return activity_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа активности: {e}")
            return {}
    
    async def export_chat_history(self, chat_id, filename=None):
        """Экспорт истории чата в файл"""
        try:
            if not filename:
                filename = f"output/chat_history_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Получаем историю
            history = await self.get_chat_history(chat_id, limit=500)
            
            if history:
                # Создаем директорию
                os.makedirs("output", exist_ok=True)
                
                # Сохраняем в файл
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, ensure_ascii=False)
                
                print(f"✅ История экспортирована в {filename}")
                return filename
            else:
                print("❌ Не удалось получить историю")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта: {e}")
            return None
    
    async def get_chat_info(self, chat_id):
        """Получение информации о чате"""
        try:
            entity = await self.client.get_entity(chat_id)
            
            info = {
                'id': entity.id,
                'title': getattr(entity, 'title', ''),
                'username': getattr(entity, 'username', ''),
                'participants_count': getattr(entity, 'participants_count', 0),
                'type': 'user' if hasattr(entity, 'first_name') else 'group' if hasattr(entity, 'title') else 'channel'
            }
            
            if hasattr(entity, 'first_name'):
                info['first_name'] = entity.first_name
                info['last_name'] = entity.last_name or ''
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о чате: {e}")
            return None

async def main():
    analyzer = ChatHistoryAnalyzer()
    
    if not await analyzer.connect():
        print("❌ Не удалось подключиться")
        return
    
    print("🔍 АНАЛИЗАТОР ИСТОРИИ ЧАТОВ")
    print("=" * 40)
    
    while True:
        print("\n📋 Выберите действие:")
        print("1. Показать список чатов")
        print("2. Получить историю чата")
        print("3. Поиск сообщений")
        print("4. Анализ активности")
        print("5. Экспорт истории")
        print("6. Информация о чате")
        print("0. Выход")
        
        choice = input("\nВведите номер: ").strip()
        
        if choice == "1":
            await analyzer.get_chat_list()
            
        elif choice == "2":
            chat_id = input("Введите ID чата: ").strip()
            limit = input("Количество сообщений (по умолчанию 100): ").strip()
            limit = int(limit) if limit.isdigit() else 100
            
            history = await analyzer.get_chat_history(chat_id, limit)
            if history:
                print(f"\n📖 История чата (последние {len(history)} сообщений):")
                for msg in history[:10]:  # Показываем первые 10
                    print(f"[{msg['date']}] {msg['sender']}: {msg['text'][:100]}...")
                if len(history) > 10:
                    print(f"... и еще {len(history) - 10} сообщений")
            
        elif choice == "3":
            chat_id = input("Введите ID чата: ").strip()
            query = input("Введите поисковый запрос: ").strip()
            
            results = await analyzer.search_messages(chat_id, query)
            if results:
                print(f"\n🔍 Результаты поиска '{query}':")
                for msg in results:
                    print(f"[{msg['date']}] {msg['sender']}: {msg['text'][:100]}...")
            
        elif choice == "4":
            chat_id = input("Введите ID чата: ").strip()
            days = input("Количество дней (по умолчанию 7): ").strip()
            days = int(days) if days.isdigit() else 7
            
            activity = await analyzer.analyze_chat_activity(chat_id, days)
            if activity:
                print(f"\n📊 Активность за последние {days} дней:")
                for date, data in activity.items():
                    print(f"{date}: {data['total']} сообщений от {len(data['users'])} пользователей")
            
        elif choice == "5":
            chat_id = input("Введите ID чата: ").strip()
            await analyzer.export_chat_history(chat_id)
            
        elif choice == "6":
            chat_id = input("Введите ID чата: ").strip()
            info = await analyzer.get_chat_info(chat_id)
            if info:
                print(f"\n📋 Информация о чате:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            
        elif choice == "0":
            print("👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    asyncio.run(main())
