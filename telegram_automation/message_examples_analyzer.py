#!/usr/bin/env python3
"""
Message Examples Analyzer for Main mega ТОП
Анализатор примеров сообщений по понедельникам-вторникам
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from telethon import TelegramClient
from loguru import logger
import pandas as pd
import os

class MessageExamplesAnalyzer:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        self.target_chat_name = "Main mega ТОП"
        self.target_chat_id = None
        
        # Настройка логирования
        os.makedirs("output/logs", exist_ok=True)
        logger.add("output/logs/message_examples.log", rotation="1 day", retention="7 days")
        
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
    
    async def find_target_chat(self):
        """Поиск целевого чата"""
        try:
            print(f"🔍 Поиск чата '{self.target_chat_name}'...")
            
            dialogs = await self.client.get_dialogs()
            
            for dialog in dialogs:
                if self.target_chat_name.lower() in dialog.name.lower():
                    self.target_chat_id = dialog.id
                    print(f"✅ Найден чат: {dialog.name} (ID: {dialog.id})")
                    return True
            
            print(f"❌ Чат '{self.target_chat_name}' не найден")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска чата: {e}")
            return False
    
    async def get_monday_tuesday_messages(self, weeks_back=12):
        """Получение сообщений по понедельникам и вторникам"""
        try:
            print(f"📥 Загрузка сообщений по понедельникам-вторникам за последние {weeks_back} недель...")
            
            today = datetime.now()
            start_date = today - timedelta(weeks=weeks_back)
            
            messages = await self.client.get_messages(
                self.target_chat_id,
                offset_date=start_date,
                limit=5000
            )
            
            print(f"✅ Получено {len(messages)} сообщений")
            
            # Фильтруем сообщения по понедельникам и вторникам
            monday_tuesday_messages = []
            
            for msg in messages:
                if msg.text and len(msg.text.strip()) > 20:  # Минимум 20 символов
                    # Проверяем день недели (понедельник = 0, вторник = 1)
                    if msg.date.weekday() in [0, 1]:  # Понедельник или вторник
                        sender_name = await self.get_sender_name(msg)
                        monday_tuesday_messages.append({
                            'id': msg.id,
                            'date': msg.date,
                            'text': msg.text.strip(),
                            'sender': sender_name,
                            'length': len(msg.text.strip()),
                            'weekday': msg.date.weekday(),
                            'weekday_name': 'Понедельник' if msg.date.weekday() == 0 else 'Вторник'
                        })
            
            print(f"📊 Найдено {len(monday_tuesday_messages)} сообщений по понедельникам-вторникам")
            return monday_tuesday_messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения сообщений: {e}")
            return []
    
    async def get_sender_name(self, message):
        """Получение имени отправителя"""
        try:
            sender = await message.get_sender()
            if sender:
                return f"{sender.first_name} {sender.last_name or ''}".strip()
            return "Unknown"
        except:
            return "Unknown"
    
    def analyze_message_content(self, messages):
        """Анализ содержимого сообщений"""
        try:
            print("🔍 Анализ содержимого сообщений...")
            
            analysis = {
                'total_messages': len(messages),
                'senders': {},
                'keywords_found': {},
                'message_examples': []
            }
            
            for msg in messages:
                text = msg['text'].lower()
                sender = msg['sender']
                
                # Подсчитываем отправителей
                if sender not in analysis['senders']:
                    analysis['senders'][sender] = 0
                analysis['senders'][sender] += 1
                
                # Ищем ключевые слова
                keywords = [
                    'план', 'факт', 'выполнено', 'сделано', 'готово', 'завершено',
                    'задача', 'проект', 'работа', 'отчет', 'итоги', 'результаты'
                ]
                
                found_keywords = []
                for keyword in keywords:
                    if keyword in text:
                        found_keywords.append(keyword)
                        if keyword not in analysis['keywords_found']:
                            analysis['keywords_found'][keyword] = 0
                        analysis['keywords_found'][keyword] += 1
                
                # Сохраняем примеры сообщений
                if len(analysis['message_examples']) < 20:  # Первые 20 сообщений
                    analysis['message_examples'].append({
                        'sender': sender,
                        'date': msg['date'].strftime('%Y-%m-%d'),
                        'weekday': msg['weekday_name'],
                        'text': msg['text'][:500] + '...' if len(msg['text']) > 500 else msg['text'],
                        'length': msg['length'],
                        'keywords': found_keywords
                    })
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа содержимого: {e}")
            return {}
    
    def create_examples_report(self, messages, analysis, filename=None):
        """Создание отчета с примерами сообщений"""
        try:
            if not filename:
                filename = f"output/message_examples_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            os.makedirs("output", exist_ok=True)
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                
                # Лист 1: Примеры сообщений
                if analysis.get('message_examples'):
                    df_examples = pd.DataFrame(analysis['message_examples'])
                    df_examples.to_excel(writer, sheet_name='Примеры сообщений', index=False)
                
                # Лист 2: Статистика по отправителям
                if analysis.get('senders'):
                    sender_data = []
                    for sender, count in analysis['senders'].items():
                        sender_data.append({
                            'Отправитель': sender,
                            'Количество сообщений': count
                        })
                    
                    df_senders = pd.DataFrame(sender_data)
                    df_senders = df_senders.sort_values('Количество сообщений', ascending=False)
                    df_senders.to_excel(writer, sheet_name='Статистика по отправителям', index=False)
                
                # Лист 3: Найденные ключевые слова
                if analysis.get('keywords_found'):
                    keyword_data = []
                    for keyword, count in analysis['keywords_found'].items():
                        keyword_data.append({
                            'Ключевое слово': keyword,
                            'Количество вхождений': count
                        })
                    
                    df_keywords = pd.DataFrame(keyword_data)
                    df_keywords = df_keywords.sort_values('Количество вхождений', ascending=False)
                    df_keywords.to_excel(writer, sheet_name='Ключевые слова', index=False)
                
                # Лист 4: Все сообщения
                if messages:
                    messages_data = []
                    for msg in messages:
                        messages_data.append({
                            'ID': msg['id'],
                            'Дата': msg['date'].strftime('%Y-%m-%d %H:%M'),
                            'День недели': msg['weekday_name'],
                            'Отправитель': msg['sender'],
                            'Текст': msg['text'],
                            'Длина': msg['length']
                        })
                    
                    df_messages = pd.DataFrame(messages_data)
                    df_messages = df_messages.sort_values(['Отправитель', 'Дата'], ascending=[True, False])
                    df_messages.to_excel(writer, sheet_name='Все сообщения', index=False)
            
            print(f"✅ Отчет с примерами создан: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания отчета: {e}")
            return None
    
    async def run_examples_analysis(self):
        """Запуск анализа примеров сообщений"""
        try:
            print("🚀 ЗАПУСК АНАЛИЗА ПРИМЕРОВ СООБЩЕНИЙ")
            print("=" * 50)
            
            # Подключение
            if not await self.connect():
                return
            
            # Поиск целевого чата
            if not await self.find_target_chat():
                return
            
            # Получение сообщений по понедельникам-вторникам
            messages = await self.get_monday_tuesday_messages(weeks_back=12)
            
            if not messages:
                print("❌ Не найдено сообщений по понедельникам-вторникам")
                return
            
            # Анализ содержимого
            analysis = self.analyze_message_content(messages)
            
            # Создание отчета
            report_file = self.create_examples_report(messages, analysis)
            
            if report_file:
                print(f"\n🎉 Анализ примеров завершен!")
                print(f"📁 Отчет сохранен: {report_file}")
                
                # Выводим краткую сводку
                print(f"\n📊 КРАТКАЯ СВОДКА:")
                print(f"Всего сообщений: {analysis.get('total_messages', 0)}")
                print(f"Уникальных отправителей: {len(analysis.get('senders', {}))}")
                
                # Показываем топ отправителей
                if analysis.get('senders'):
                    print(f"\n👥 ТОП ОТПРАВИТЕЛЕЙ:")
                    top_senders = sorted(analysis['senders'].items(), key=lambda x: x[1], reverse=True)[:5]
                    for sender, count in top_senders:
                        print(f"  {sender}: {count} сообщений")
                
                # Показываем популярные ключевые слова
                if analysis.get('keywords_found'):
                    print(f"\n🔍 ПОПУЛЯРНЫЕ КЛЮЧЕВЫЕ СЛОВА:")
                    top_keywords = sorted(analysis['keywords_found'].items(), key=lambda x: x[1], reverse=True)[:5]
                    for keyword, count in top_keywords:
                        print(f"  {keyword}: {count} раз")
                
                # Показываем примеры сообщений
                if analysis.get('message_examples'):
                    print(f"\n📝 ПРИМЕРЫ СООБЩЕНИЙ:")
                    for i, example in enumerate(analysis['message_examples'][:5]):
                        print(f"\n  {i+1}. {example['sender']} ({example['date']}, {example['weekday']})")
                        print(f"     Ключевые слова: {', '.join(example['keywords'])}")
                        print(f"     Текст: {example['text'][:200]}...")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            print(f"❌ Ошибка: {e}")

async def main():
    analyzer = MessageExamplesAnalyzer()
    await analyzer.run_examples_analysis()

if __name__ == "__main__":
    asyncio.run(main())
