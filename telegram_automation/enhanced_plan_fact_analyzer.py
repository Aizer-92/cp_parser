#!/usr/bin/env python3
"""
Enhanced Plan/Fact Analyzer for Main mega ТОП
Улучшенный анализатор планов и фактов
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from telethon import TelegramClient
from loguru import logger
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import os

class EnhancedPlanFactAnalyzer:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        self.target_chat_name = "Main mega ТОП"
        self.target_chat_id = None
        
        # Настройка логирования
        os.makedirs("output/logs", exist_ok=True)
        logger.add("output/logs/enhanced_plan_fact.log", rotation="1 day", retention="7 days")
        
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
    
    def extract_plan_fact_data(self, message_text, message_date, sender_name):
        """Улучшенное извлечение данных планов и фактов"""
        try:
            text = message_text.strip()
            extracted_data = []
            
            # Расширенные паттерны для поиска
            patterns = [
                # Паттерн 1: План: X, Факт: Y
                (r'план[:\s]*(\d+(?:\.\d+)?)[^\d]*факт[:\s]*(\d+(?:\.\d+)?)', 'План: X, Факт: Y'),
                # Паттерн 2: П/Ф: X/Y
                (r'п/ф[:\s]*(\d+(?:\.\d+)?)[^\d]*(\d+(?:\.\d+)?)', 'П/Ф: X/Y'),
                # Паттерн 3: План X Факт Y
                (r'план\s+(\d+(?:\.\d+)?)[^\d]*факт\s+(\d+(?:\.\d+)?)', 'План X Факт Y'),
                # Паттерн 4: Просто числа через слеш или дефис
                (r'(\d+(?:\.\d+)?)[/\-]\s*(\d+(?:\.\d+)?)', 'X/Y или X-Y'),
                # Паттерн 5: П: X Ф: Y
                (r'п[:\s]*(\d+(?:\.\d+)?)[^\d]*ф[:\s]*(\d+(?:\.\d+)?)', 'П: X Ф: Y'),
                # Паттерн 6: План - X, Факт - Y
                (r'план\s*[-\s]*(\d+(?:\.\d+)?)[^\d]*факт\s*[-\s]*(\d+(?:\.\d+)?)', 'План - X, Факт - Y'),
                # Паттерн 7: Числа в скобках
                (r'\((\d+(?:\.\d+)?)[^\d]*(\d+(?:\.\d+)?)\)', '(X Y)'),
                # Паттерн 8: План/Факт: X/Y
                (r'план/факт[:\s]*(\d+(?:\.\d+)?)[^\d]*(\d+(?:\.\d+)?)', 'План/Факт: X/Y'),
            ]
            
            for pattern, pattern_name in patterns:
                matches = re.finditer(pattern, text.lower())
                for match in matches:
                    try:
                        plan_value = float(match.group(1))
                        fact_value = float(match.group(2))
                        
                        # Проверяем разумность значений
                        if 0 <= plan_value <= 1000000 and 0 <= fact_value <= 1000000:
                            completion_percent = (fact_value / plan_value * 100) if plan_value > 0 else 0
                            
                            extracted_data.append({
                                'date': message_date,
                                'sender': sender_name,
                                'plan': plan_value,
                                'fact': fact_value,
                                'difference': fact_value - plan_value,
                                'completion_percent': completion_percent,
                                'pattern_used': pattern_name,
                                'original_text': text[:300],  # Первые 300 символов
                                'status': self.get_status(completion_percent)
                            })
                    except (ValueError, ZeroDivisionError):
                        continue
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения данных: {e}")
            return []
    
    def get_status(self, completion_percent):
        """Определение статуса выполнения"""
        if completion_percent >= 100:
            return "Перевыполнение"
        elif completion_percent >= 90:
            return "Хорошо"
        elif completion_percent >= 70:
            return "Удовлетворительно"
        else:
            return "Недовыполнение"
    
    async def get_weekly_messages(self, weeks_back=4):
        """Получение сообщений за последние недели"""
        try:
            print(f"📅 Получение сообщений за последние {weeks_back} недели...")
            
            # Вычисляем дату начала
            today = datetime.now()
            days_since_tuesday = (today.weekday() - 1) % 7
            start_date = today - timedelta(days=days_since_tuesday + (weeks_back * 7))
            
            # Получаем сообщения
            messages = await self.client.get_messages(
                self.target_chat_id,
                offset_date=start_date,
                limit=2000  # Увеличиваем лимит
            )
            
            print(f"✅ Получено {len(messages)} сообщений")
            
            # Фильтруем сообщения по вторникам
            tuesday_messages = []
            for msg in messages:
                if msg.text and msg.date.weekday() == 1:  # 1 = вторник
                    sender_name = await self.get_sender_name(msg)
                    tuesday_messages.append({
                        'id': msg.id,
                        'date': msg.date,
                        'text': msg.text,
                        'sender': sender_name
                    })
            
            print(f"📊 Найдено {len(tuesday_messages)} сообщений по вторникам")
            return tuesday_messages
            
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
    
    def analyze_data_by_weeks(self, all_data):
        """Анализ данных по неделям"""
        try:
            # Группируем данные по неделям
            weekly_data = {}
            
            for item in all_data:
                # Определяем неделю
                date = item['date'].replace(tzinfo=None)
                week_start = date - timedelta(days=date.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                
                if week_key not in weekly_data:
                    weekly_data[week_key] = []
                weekly_data[week_key].append(item)
            
            # Анализируем каждую неделю
            weekly_analysis = {}
            for week, data in weekly_data.items():
                if data:
                    weekly_analysis[week] = {
                        'total_plan': sum(item['plan'] for item in data),
                        'total_fact': sum(item['fact'] for item in data),
                        'avg_completion': sum(item['completion_percent'] for item in data) / len(data),
                        'items_count': len(data),
                        'senders': list(set(item['sender'] for item in data)),
                        'over_performance_count': len([item for item in data if item['completion_percent'] >= 100]),
                        'under_performance_count': len([item for item in data if item['completion_percent'] < 100])
                    }
            
            return weekly_analysis
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа по неделям: {e}")
            return {}
    
    def create_enhanced_excel_report(self, all_data, weekly_analysis, filename=None):
        """Создание улучшенного Excel отчета"""
        try:
            if not filename:
                filename = f"output/enhanced_plan_fact_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            os.makedirs("output", exist_ok=True)
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                
                # Лист 1: Все данные
                if all_data:
                    df_all = pd.DataFrame(all_data)
                    df_all['date'] = pd.to_datetime(df_all['date']).dt.tz_localize(None)
                    df_all = df_all.sort_values('date', ascending=False)
                    
                    # Переименовываем колонки для удобства
                    df_all = df_all.rename(columns={
                        'date': 'Дата',
                        'sender': 'Отправитель',
                        'plan': 'План',
                        'fact': 'Факт',
                        'difference': 'Разница',
                        'completion_percent': '% выполнения',
                        'pattern_used': 'Формат',
                        'original_text': 'Исходный текст',
                        'status': 'Статус'
                    })
                    
                    df_all.to_excel(writer, sheet_name='Все данные', index=False)
                    
                    # Форматирование
                    worksheet = writer.sheets['Все данные']
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Лист 2: Анализ по неделям
                if weekly_analysis:
                    weekly_data = []
                    for week, data in weekly_analysis.items():
                        weekly_data.append({
                            'Неделя': week,
                            'Общий план': round(data['total_plan'], 2),
                            'Общий факт': round(data['total_fact'], 2),
                            'Средний % выполнения': round(data['avg_completion'], 2),
                            'Количество позиций': data['items_count'],
                            'Перевыполнений': data['over_performance_count'],
                            'Недовыполнений': data['under_performance_count'],
                            'Участники': ', '.join(data['senders'])
                        })
                    
                    df_weekly = pd.DataFrame(weekly_data)
                    df_weekly.to_excel(writer, sheet_name='Анализ по неделям', index=False)
                
                # Лист 3: Статистика по отправителям
                if all_data:
                    sender_stats = {}
                    for item in all_data:
                        sender = item['sender']
                        if sender not in sender_stats:
                            sender_stats[sender] = {
                                'total_plan': 0,
                                'total_fact': 0,
                                'count': 0,
                                'over_performance': 0,
                                'under_performance': 0
                            }
                        
                        sender_stats[sender]['total_plan'] += item['plan']
                        sender_stats[sender]['total_fact'] += item['fact']
                        sender_stats[sender]['count'] += 1
                        
                        if item['completion_percent'] >= 100:
                            sender_stats[sender]['over_performance'] += 1
                        else:
                            sender_stats[sender]['under_performance'] += 1
                    
                    sender_data = []
                    for sender, stats in sender_stats.items():
                        avg_completion = (stats['total_fact'] / stats['total_plan'] * 100) if stats['total_plan'] > 0 else 0
                        sender_data.append({
                            'Отправитель': sender,
                            'Общий план': round(stats['total_plan'], 2),
                            'Общий факт': round(stats['total_fact'], 2),
                            'Средний % выполнения': round(avg_completion, 2),
                            'Количество записей': stats['count'],
                            'Перевыполнений': stats['over_performance'],
                            'Недовыполнений': stats['under_performance']
                        })
                    
                    df_senders = pd.DataFrame(sender_data)
                    df_senders = df_senders.sort_values('Средний % выполнения', ascending=False)
                    df_senders.to_excel(writer, sheet_name='Статистика по отправителям', index=False)
                
                # Лист 4: Общая статистика
                if all_data:
                    total_plan = sum(item['plan'] for item in all_data)
                    total_fact = sum(item['fact'] for item in all_data)
                    avg_completion = sum(item['completion_percent'] for item in all_data) / len(all_data)
                    
                    stats_data = {
                        'Показатель': [
                            'Всего записей',
                            'Общий план',
                            'Общий факт',
                            'Средний % выполнения',
                            'Максимальный % выполнения',
                            'Минимальный % выполнения',
                            'Количество перевыполнений (>100%)',
                            'Количество недовыполнений (<100%)',
                            'Количество отправителей',
                            'Самый активный отправитель'
                        ],
                        'Значение': [
                            len(all_data),
                            round(total_plan, 2),
                            round(total_fact, 2),
                            round(avg_completion, 2),
                            round(max(item['completion_percent'] for item in all_data), 2),
                            round(min(item['completion_percent'] for item in all_data), 2),
                            len([item for item in all_data if item['completion_percent'] > 100]),
                            len([item for item in all_data if item['completion_percent'] < 100]),
                            len(set(item['sender'] for item in all_data)),
                            max(set(item['sender'] for item in all_data), key=lambda x: len([item for item in all_data if item['sender'] == x]))
                        ]
                    }
                    
                    df_stats = pd.DataFrame(stats_data)
                    df_stats.to_excel(writer, sheet_name='Общая статистика', index=False)
            
            print(f"✅ Улучшенный отчет создан: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания отчета: {e}")
            return None
    
    async def run_enhanced_analysis(self):
        """Запуск улучшенного анализа"""
        try:
            print("🚀 ЗАПУСК УЛУЧШЕННОГО АНАЛИЗА ПЛАНОВ И ФАКТОВ")
            print("=" * 60)
            
            # Подключение
            if not await self.connect():
                return
            
            # Поиск целевого чата
            if not await self.find_target_chat():
                return
            
            # Получение сообщений
            messages = await self.get_weekly_messages(weeks_back=6)  # 6 недель для анализа
            
            if not messages:
                print("❌ Не найдено сообщений для анализа")
                return
            
            # Извлечение данных
            all_extracted_data = []
            
            for msg in messages:
                extracted = self.extract_plan_fact_data(msg['text'], msg['date'], msg['sender'])
                all_extracted_data.extend(extracted)
            
            print(f"📊 Извлечено {len(all_extracted_data)} записей планов/фактов")
            
            if not all_extracted_data:
                print("❌ Не удалось извлечь данные планов/фактов")
                return
            
            # Анализ по неделям
            weekly_analysis = self.analyze_data_by_weeks(all_extracted_data)
            
            # Создание отчета
            report_file = self.create_enhanced_excel_report(all_extracted_data, weekly_analysis)
            
            if report_file:
                print(f"\n🎉 Анализ завершен!")
                print(f"📁 Отчет сохранен: {report_file}")
                
                # Выводим краткую сводку
                print(f"\n📊 КРАТКАЯ СВОДКА:")
                print(f"Всего записей: {len(all_extracted_data)}")
                print(f"Период анализа: {len(weekly_analysis)} недель")
                print(f"Уникальных отправителей: {len(set(item['sender'] for item in all_extracted_data))}")
                
                # Показываем последние данные
                if all_extracted_data:
                    latest_data = sorted(all_extracted_data, key=lambda x: x['date'], reverse=True)[:5]
                    print(f"\n📅 Последние 5 записей:")
                    for item in latest_data:
                        date_str = item['date'].strftime('%Y-%m-%d')
                        print(f"  {date_str} | {item['sender']} | План: {item['plan']} | Факт: {item['fact']} | {item['completion_percent']:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            print(f"❌ Ошибка: {e}")

async def main():
    analyzer = EnhancedPlanFactAnalyzer()
    await analyzer.run_enhanced_analysis()

if __name__ == "__main__":
    asyncio.run(main())
