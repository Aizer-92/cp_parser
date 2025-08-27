#!/usr/bin/env python3
"""
Plan/Fact Analyzer for Main mega ТОП
Анализатор планов и фактов для чата Main mega ТОП
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from loguru import logger
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
import os

class PlanFactAnalyzer:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        self.target_chat_name = "Main mega ТОП"
        self.target_chat_id = None
        
        # Настройка логирования
        os.makedirs("output/logs", exist_ok=True)
        logger.add("output/logs/plan_fact_analyzer.log", rotation="1 day", retention="7 days")
        
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
            print("📋 Доступные чаты:")
            for dialog in dialogs[:10]:
                print(f"  - {dialog.name} (ID: {dialog.id})")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска чата: {e}")
            return False
    
    def extract_plan_fact_data(self, message_text, message_date):
        """Извлечение данных планов и фактов из сообщения"""
        try:
            # Очищаем текст от лишних символов
            text = message_text.strip()
            
            # Различные паттерны для поиска планов и фактов
            patterns = [
                # Паттерн 1: План: X, Факт: Y
                r'план[:\s]*(\d+(?:\.\d+)?)[^\d]*факт[:\s]*(\d+(?:\.\d+)?)',
                # Паттерн 2: П/Ф: X/Y
                r'п/ф[:\s]*(\d+(?:\.\d+)?)[^\d]*(\d+(?:\.\d+)?)',
                # Паттерн 3: План X Факт Y
                r'план\s+(\d+(?:\.\d+)?)[^\d]*факт\s+(\d+(?:\.\d+)?)',
                # Паттерн 4: Просто числа через слеш или дефис
                r'(\d+(?:\.\d+)?)[/\-]\s*(\d+(?:\.\d+)?)',
                # Паттерн 5: П: X Ф: Y
                r'п[:\s]*(\d+(?:\.\d+)?)[^\d]*ф[:\s]*(\d+(?:\.\d+)?)',
            ]
            
            extracted_data = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, text.lower())
                for match in matches:
                    try:
                        plan_value = float(match.group(1))
                        fact_value = float(match.group(2))
                        
                        # Проверяем, что значения разумные (не слишком большие)
                        if 0 <= plan_value <= 1000000 and 0 <= fact_value <= 1000000:
                            extracted_data.append({
                                'date': message_date,
                                'plan': plan_value,
                                'fact': fact_value,
                                'difference': fact_value - plan_value,
                                'completion_percent': (fact_value / plan_value * 100) if plan_value > 0 else 0,
                                'pattern_used': pattern,
                                'original_text': text[:200]  # Первые 200 символов для отладки
                            })
                    except (ValueError, ZeroDivisionError):
                        continue
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения данных: {e}")
            return []
    
    async def get_weekly_messages(self, weeks_back=2):
        """Получение сообщений за последние недели"""
        try:
            print(f"📅 Получение сообщений за последние {weeks_back} недели...")
            
            # Вычисляем дату начала (вторник недели назад)
            today = datetime.now()
            days_since_tuesday = (today.weekday() - 1) % 7  # 1 = вторник
            start_date = today - timedelta(days=days_since_tuesday + (weeks_back * 7))
            
            # Получаем сообщения
            messages = await self.client.get_messages(
                self.target_chat_id,
                offset_date=start_date,
                limit=1000
            )
            
            print(f"✅ Получено {len(messages)} сообщений")
            
            # Фильтруем сообщения по вторникам
            tuesday_messages = []
            for msg in messages:
                if msg.text and msg.date.weekday() == 1:  # 1 = вторник
                    tuesday_messages.append({
                        'id': msg.id,
                        'date': msg.date,
                        'text': msg.text,
                        'sender': await self.get_sender_name(msg)
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
    
    def analyze_weekly_comparison(self, current_week_data, previous_week_data):
        """Сравнение данных текущей и прошлой недели"""
        try:
            comparison = {
                'current_week': {
                    'total_plan': sum(item['plan'] for item in current_week_data),
                    'total_fact': sum(item['fact'] for item in current_week_data),
                    'avg_completion': sum(item['completion_percent'] for item in current_week_data) / len(current_week_data) if current_week_data else 0,
                    'items_count': len(current_week_data)
                },
                'previous_week': {
                    'total_plan': sum(item['plan'] for item in previous_week_data),
                    'total_fact': sum(item['fact'] for item in previous_week_data),
                    'avg_completion': sum(item['completion_percent'] for item in previous_week_data) / len(previous_week_data) if previous_week_data else 0,
                    'items_count': len(previous_week_data)
                }
            }
            
            # Вычисляем разрывы
            comparison['gaps'] = {
                'plan_gap': comparison['current_week']['total_plan'] - comparison['previous_week']['total_plan'],
                'fact_gap': comparison['current_week']['total_fact'] - comparison['previous_week']['total_fact'],
                'completion_gap': comparison['current_week']['avg_completion'] - comparison['previous_week']['avg_completion']
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"❌ Ошибка сравнения недель: {e}")
            return {}
    
    def create_excel_report(self, all_data, weekly_comparison, filename=None):
        """Создание Excel отчета"""
        try:
            if not filename:
                filename = f"output/plan_fact_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Создаем директорию
            os.makedirs("output", exist_ok=True)
            
            # Создаем Excel файл
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                
                # Лист 1: Все данные
                if all_data:
                    df_all = pd.DataFrame(all_data)
                    # Убираем часовой пояс для Excel
                    df_all['date'] = pd.to_datetime(df_all['date']).dt.tz_localize(None)
                    df_all = df_all.sort_values('date', ascending=False)
                    
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
                
                # Лист 2: Сравнение недель
                if weekly_comparison:
                    comparison_data = []
                    for week, data in weekly_comparison.items():
                        if week != 'gaps':
                            comparison_data.append({
                                'Неделя': week,
                                'Общий план': data['total_plan'],
                                'Общий факт': data['total_fact'],
                                'Средний % выполнения': round(data['avg_completion'], 2),
                                'Количество позиций': data['items_count']
                            })
                    
                    df_comparison = pd.DataFrame(comparison_data)
                    df_comparison.to_excel(writer, sheet_name='Сравнение недель', index=False)
                    
                    # Добавляем разрывы
                    if 'gaps' in weekly_comparison:
                        gaps_data = [{
                            'Показатель': 'Разрыв планов',
                            'Значение': weekly_comparison['gaps']['plan_gap'],
                            'Тип': 'Увеличение' if weekly_comparison['gaps']['plan_gap'] > 0 else 'Снижение'
                        }, {
                            'Показатель': 'Разрыв фактов',
                            'Значение': weekly_comparison['gaps']['fact_gap'],
                            'Тип': 'Увеличение' if weekly_comparison['gaps']['fact_gap'] > 0 else 'Снижение'
                        }, {
                            'Показатель': 'Разрыв % выполнения',
                            'Значение': round(weekly_comparison['gaps']['completion_gap'], 2),
                            'Тип': 'Улучшение' if weekly_comparison['gaps']['completion_gap'] > 0 else 'Ухудшение'
                        }]
                        
                        df_gaps = pd.DataFrame(gaps_data)
                        df_gaps.to_excel(writer, sheet_name='Разрывы', index=False)
                
                # Лист 3: Статистика
                if all_data:
                    stats_data = {
                        'Показатель': [
                            'Всего записей',
                            'Средний план',
                            'Средний факт',
                            'Средний % выполнения',
                            'Максимальный % выполнения',
                            'Минимальный % выполнения',
                            'Количество перевыполнений (>100%)',
                            'Количество недовыполнений (<100%)'
                        ],
                        'Значение': [
                            len(all_data),
                            round(sum(item['plan'] for item in all_data) / len(all_data), 2),
                            round(sum(item['fact'] for item in all_data) / len(all_data), 2),
                            round(sum(item['completion_percent'] for item in all_data) / len(all_data), 2),
                            round(max(item['completion_percent'] for item in all_data), 2),
                            round(min(item['completion_percent'] for item in all_data), 2),
                            len([item for item in all_data if item['completion_percent'] > 100]),
                            len([item for item in all_data if item['completion_percent'] < 100])
                        ]
                    }
                    
                    df_stats = pd.DataFrame(stats_data)
                    df_stats.to_excel(writer, sheet_name='Статистика', index=False)
            
            print(f"✅ Отчет создан: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания отчета: {e}")
            return None
    
    async def run_analysis(self):
        """Запуск полного анализа"""
        try:
            print("🚀 ЗАПУСК АНАЛИЗА ПЛАНОВ И ФАКТОВ")
            print("=" * 50)
            
            # Подключение
            if not await self.connect():
                return
            
            # Поиск целевого чата
            if not await self.find_target_chat():
                return
            
            # Получение сообщений
            messages = await self.get_weekly_messages(weeks_back=4)  # 4 недели для анализа
            
            if not messages:
                print("❌ Не найдено сообщений для анализа")
                return
            
            # Извлечение данных
            all_extracted_data = []
            current_week_data = []
            previous_week_data = []
            
            current_week_start = datetime.now().replace(tzinfo=None) - timedelta(days=datetime.now().weekday())
            previous_week_start = current_week_start - timedelta(days=7)
            
            for msg in messages:
                extracted = self.extract_plan_fact_data(msg['text'], msg['date'])
                
                for item in extracted:
                    all_extracted_data.append(item)
                    
                    # Разделяем по неделям (убираем часовой пояс для сравнения)
                    msg_date_naive = msg['date'].replace(tzinfo=None)
                    if current_week_start <= msg_date_naive < current_week_start + timedelta(days=7):
                        current_week_data.append(item)
                    elif previous_week_start <= msg_date_naive < previous_week_start + timedelta(days=7):
                        previous_week_data.append(item)
            
            print(f"📊 Извлечено {len(all_extracted_data)} записей планов/фактов")
            print(f"📅 Текущая неделя: {len(current_week_data)} записей")
            print(f"📅 Прошлая неделя: {len(previous_week_data)} записей")
            
            # Сравнение недель
            weekly_comparison = self.analyze_weekly_comparison(current_week_data, previous_week_data)
            
            # Создание отчета
            report_file = self.create_excel_report(all_extracted_data, weekly_comparison)
            
            if report_file:
                print(f"\n🎉 Анализ завершен!")
                print(f"📁 Отчет сохранен: {report_file}")
                
                # Выводим краткую сводку
                if weekly_comparison:
                    print(f"\n📊 КРАТКАЯ СВОДКА:")
                    print(f"Текущая неделя: План {weekly_comparison['current_week']['total_plan']:.2f}, Факт {weekly_comparison['current_week']['total_fact']:.2f}")
                    print(f"Прошлая неделя: План {weekly_comparison['previous_week']['total_plan']:.2f}, Факт {weekly_comparison['previous_week']['total_fact']:.2f}")
                    
                    if 'gaps' in weekly_comparison:
                        print(f"Разрыв планов: {weekly_comparison['gaps']['plan_gap']:+.2f}")
                        print(f"Разрыв фактов: {weekly_comparison['gaps']['fact_gap']:+.2f}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            print(f"❌ Ошибка: {e}")

async def main():
    analyzer = PlanFactAnalyzer()
    await analyzer.run_analysis()

if __name__ == "__main__":
    asyncio.run(main())
