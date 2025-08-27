"""
Утилиты для интеграции Google Sheets с финансовыми данными
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connector import GoogleSheetsConnector

class FinanceSheetsSync:
    """Класс для работы с финансовыми данными в Google Sheets"""
    
    def __init__(self, connector: Optional[GoogleSheetsConnector] = None):
        """
        Инициализация финансовой интеграции
        
        Args:
            connector: Готовый коннектор или None для создания нового
        """
        self.connector = connector or GoogleSheetsConnector()
        self.finance_data_path = "../../Docs/Finance/"
        
    def authenticate(self, service_account_file: str = "credentials/quickstart-1591698112539-676a9e339335.json") -> bool:
        """
        Аутентификация в Google Sheets
        
        Args:
            service_account_file: Путь к файлу Service Account
            
        Returns:
            bool: True если успешно
        """
        return self.connector.authenticate_service_account(service_account_file)
    
    def create_budget_template(self, spreadsheet_id: str, sheet_name: str = "Budget 2024") -> bool:
        """
        Создает шаблон бюджета
        
        Args:
            spreadsheet_id: ID таблицы
            sheet_name: Название листа
            
        Returns:
            bool: True если успешно
        """
        try:
            # Создаем лист
            try:
                self.connector.create_sheet(spreadsheet_id, sheet_name)
            except:
                pass  # Лист уже существует
            
            # Структура бюджета
            budget_data = [
                ["ПЕРСОНАЛЬНЫЙ БЮДЖЕТ", "", "", ""],
                ["", "", "", ""],
                ["ДОХОДЫ", "План", "Факт", "Разница"],
                ["Зарплата", "100000", "", "=C4-B4"],
                ["Подработка", "20000", "", "=C5-B5"],
                ["Инвестиции", "5000", "", "=C6-B6"],
                ["Прочие доходы", "0", "", "=C7-B7"],
                ["ИТОГО ДОХОДЫ", "=SUM(B4:B7)", "=SUM(C4:C7)", "=C8-B8"],
                ["", "", "", ""],
                ["РАСХОДЫ", "План", "Факт", "Разница"],
                ["Жилье", "40000", "", "=C11-B11"],
                ["Питание", "25000", "", "=C12-B12"],
                ["Транспорт", "10000", "", "=C13-B13"],
                ["Здоровье", "5000", "", "=C14-B14"],
                ["Образование", "3000", "", "=C15-B15"],
                ["Развлечения", "8000", "", "=C16-B16"],
                ["Одежда", "5000", "", "=C17-B17"],
                ["Накопления", "15000", "", "=C18-B18"],
                ["Прочие расходы", "5000", "", "=C19-B19"],
                ["ИТОГО РАСХОДЫ", "=SUM(B11:B19)", "=SUM(C11:C19)", "=C20-B20"],
                ["", "", "", ""],
                ["БАЛАНС", "=B8-B20", "=C8-C20", "=C22-B22"],
                ["", "", "", ""],
                ["ФИНАНСОВЫЕ ЦЕЛИ", "", "", ""],
                ["Цель", "Сумма", "Накоплено", "Осталось"],
                ["Резервный фонд", "200000", "50000", "=B26-C26"],
                ["Отпуск", "100000", "20000", "=B27-C27"],
                ["Новая техника", "50000", "0", "=B28-C28"]
            ]
            
            # Записываем шаблон
            success = self.connector.write_range(
                spreadsheet_id,
                f"{sheet_name}!A1",
                budget_data
            )
            
            if success:
                print(f"✅ Создан шаблон бюджета '{sheet_name}'")
                return True
            else:
                print("❌ Ошибка создания шаблона бюджета")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка создания бюджета: {e}")
            return False
    
    def create_expense_tracker(self, spreadsheet_id: str, sheet_name: str = "Expenses") -> bool:
        """
        Создает трекер расходов
        
        Args:
            spreadsheet_id: ID таблицы
            sheet_name: Название листа
            
        Returns:
            bool: True если успешно
        """
        try:
            # Создаем лист
            try:
                self.connector.create_sheet(spreadsheet_id, sheet_name)
            except:
                pass
            
            # Заголовки трекера расходов
            expense_headers = [
                ["ТРЕКЕР РАСХОДОВ", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["Дата", "Категория", "Описание", "Сумма", "Способ оплаты", "Место", "Теги"],
                [datetime.now().strftime("%Y-%m-%d"), "Питание", "Обед", "500", "Карта", "Кафе", "еда"],
                [datetime.now().strftime("%Y-%m-%d"), "Транспорт", "Метро", "60", "Карта", "Метро", "транспорт"],
                ["", "", "", "", "", "", ""],
                ["СТАТИСТИКА", "", "", "", "", "", ""],
                ["Категория", "Сумма", "", "", "", "", ""],
                ["Питание", "=SUMIF(B:B,\"Питание\",D:D)", "", "", "", "", ""],
                ["Транспорт", "=SUMIF(B:B,\"Транспорт\",D:D)", "", "", "", "", ""],
                ["Жилье", "=SUMIF(B:B,\"Жилье\",D:D)", "", "", "", "", ""],
                ["Здоровье", "=SUMIF(B:B,\"Здоровье\",D:D)", "", "", "", "", ""],
                ["Развлечения", "=SUMIF(B:B,\"Развлечения\",D:D)", "", "", "", "", ""],
                ["Прочее", "=SUMIF(B:B,\"Прочее\",D:D)", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["ИТОГО ЗА МЕСЯЦ", "=SUM(D4:D1000)", "", "", "", "", ""]
            ]
            
            # Записываем трекер
            success = self.connector.write_range(
                spreadsheet_id,
                f"{sheet_name}!A1",
                expense_headers
            )
            
            if success:
                print(f"✅ Создан трекер расходов '{sheet_name}'")
                return True
            else:
                print("❌ Ошибка создания трекера расходов")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка создания трекера: {e}")
            return False
    
    def create_investment_tracker(self, spreadsheet_id: str, sheet_name: str = "Investments") -> bool:
        """
        Создает трекер инвестиций
        
        Args:
            spreadsheet_id: ID таблицы
            sheet_name: Название листа
            
        Returns:
            bool: True если успешно
        """
        try:
            # Создаем лист
            try:
                self.connector.create_sheet(spreadsheet_id, sheet_name)
            except:
                pass
            
            # Структура инвестиционного портфеля
            investment_data = [
                ["ИНВЕСТИЦИОННЫЙ ПОРТФЕЛЬ", "", "", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["Актив", "Тип", "Количество", "Цена покупки", "Текущая цена", "Сумма", "Доходность %"],
                ["SBER", "Акции", "100", "250", "280", "=C4*E4", "=(E4-D4)/D4*100"],
                ["GAZP", "Акции", "50", "180", "170", "=C5*E5", "=(E5-D5)/D5*100"],
                ["Облигации ОФЗ", "Облигации", "10", "1000", "1020", "=C6*E6", "=(E6-D6)/D6*100"],
                ["", "", "", "", "", "", ""],
                ["ИТОГО ПОРТФЕЛЬ", "", "", "", "", "=SUM(F4:F6)", ""],
                ["Вложено", "", "", "", "", "=SUMPRODUCT(C4:C6,D4:D6)", ""],
                ["Текущая стоимость", "", "", "", "", "=F8", ""],
                ["Прибыль/Убыток", "", "", "", "", "=F10-F9", ""],
                ["Доходность %", "", "", "", "", "=F11/F9*100", ""],
                ["", "", "", "", "", "", ""],
                ["ПОПОЛНЕНИЯ СЧЕТА", "", "", "", "", "", ""],
                ["Дата", "Сумма", "Брокер", "", "", "", ""],
                [datetime.now().strftime("%Y-%m-%d"), "10000", "Тинькофф", "", "", "", ""],
                ["", "", "", "", "", "", ""],
                ["ДИВИДЕНДЫ", "", "", "", "", "", ""],
                ["Дата", "Актив", "Сумма", "", "", "", ""],
                ["", "", "", "", "", "", ""]
            ]
            
            # Записываем трекер инвестиций
            success = self.connector.write_range(
                spreadsheet_id,
                f"{sheet_name}!A1",
                investment_data
            )
            
            if success:
                print(f"✅ Создан трекер инвестиций '{sheet_name}'")
                return True
            else:
                print("❌ Ошибка создания трекера инвестиций")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка создания инвестиций: {e}")
            return False
    
    def add_expense(self, spreadsheet_id: str, date: str, category: str, 
                   description: str, amount: float, payment_method: str = "Карта",
                   place: str = "", tags: str = "", sheet_name: str = "Expenses") -> bool:
        """
        Добавляет новый расход
        
        Args:
            spreadsheet_id: ID таблицы
            date: Дата в формате YYYY-MM-DD
            category: Категория расхода
            description: Описание
            amount: Сумма
            payment_method: Способ оплаты
            place: Место покупки
            tags: Теги
            sheet_name: Название листа
            
        Returns:
            bool: True если успешно
        """
        try:
            new_expense = [
                [date, category, description, str(amount), payment_method, place, tags]
            ]
            
            # Добавляем расход в конец таблицы (после заголовков)
            success = self.connector.append_rows(
                spreadsheet_id,
                f"{sheet_name}!A4:G4",
                new_expense
            )
            
            if success:
                print(f"✅ Добавлен расход: {description} - {amount} руб.")
                return True
            else:
                print("❌ Ошибка добавления расхода")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка добавления расхода: {e}")
            return False
    
    def get_monthly_expenses(self, spreadsheet_id: str, month: int, year: int,
                           sheet_name: str = "Expenses") -> pd.DataFrame:
        """
        Получает расходы за месяц
        
        Args:
            spreadsheet_id: ID таблицы
            month: Месяц (1-12)
            year: Год
            sheet_name: Название листа
            
        Returns:
            pd.DataFrame: Расходы за месяц
        """
        try:
            # Читаем все данные с листа расходов
            data = self.connector.read_range(spreadsheet_id, f"{sheet_name}!A4:G1000")
            
            if not data:
                return pd.DataFrame()
            
            # Создаем DataFrame
            df = pd.DataFrame(data[1:], columns=data[0] if data else [])
            
            if df.empty:
                return df
            
            # Фильтруем по месяцу и году
            df['Дата'] = pd.to_datetime(df['Дата'], errors='coerce')
            df = df.dropna(subset=['Дата'])
            
            # Фильтр по месяцу и году
            mask = (df['Дата'].dt.month == month) & (df['Дата'].dt.year == year)
            monthly_expenses = df[mask]
            
            return monthly_expenses
            
        except Exception as e:
            print(f"❌ Ошибка получения расходов: {e}")
            return pd.DataFrame()
    
    def generate_monthly_report(self, spreadsheet_id: str, month: int, year: int,
                              sheet_name: str = "Monthly Report") -> bool:
        """
        Генерирует месячный отчет
        
        Args:
            spreadsheet_id: ID таблицы
            month: Месяц
            year: Год
            sheet_name: Название листа отчета
            
        Returns:
            bool: True если успешно
        """
        try:
            # Получаем данные за месяц
            monthly_data = self.get_monthly_expenses(spreadsheet_id, month, year)
            
            if monthly_data.empty:
                print("❌ Нет данных за указанный период")
                return False
            
            # Создаем лист отчета
            report_sheet = f"{sheet_name} {year}-{month:02d}"
            try:
                self.connector.create_sheet(spreadsheet_id, report_sheet)
            except:
                pass
            
            # Группировка по категориям
            category_totals = monthly_data.groupby('Категория')['Сумма'].sum().sort_values(ascending=False)
            
            # Формируем отчет
            report_data = [
                [f"ОТЧЕТ ЗА {month:02d}.{year}", "", ""],
                ["", "", ""],
                ["РАСХОДЫ ПО КАТЕГОРИЯМ", "", ""],
                ["Категория", "Сумма", "% от общего"]
            ]
            
            total_amount = category_totals.sum()
            
            for category, amount in category_totals.items():
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                report_data.append([category, str(amount), f"{percentage:.1f}%"])
            
            report_data.extend([
                ["", "", ""],
                ["ИТОГО", str(total_amount), "100%"],
                ["", "", ""],
                ["СТАТИСТИКА", "", ""],
                [f"Всего транзакций", str(len(monthly_data)), ""],
                [f"Средний чек", str(round(total_amount / len(monthly_data), 2)) if len(monthly_data) > 0 else "0", ""],
                [f"Самая большая покупка", str(monthly_data['Сумма'].max()) if not monthly_data.empty else "0", ""],
                [f"Самая частая категория", category_totals.index[0] if not category_totals.empty else "Нет", ""]
            ])
            
            # Записываем отчет
            success = self.connector.write_range(
                spreadsheet_id,
                f"{report_sheet}!A1",
                report_data
            )
            
            if success:
                print(f"✅ Создан отчет за {month:02d}.{year}")
                return True
            else:
                print("❌ Ошибка создания отчета")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка генерации отчета: {e}")
            return False
    
    def setup_finance_spreadsheet(self, spreadsheet_id: Optional[str] = None) -> bool:
        """
        Полная настройка финансовой таблицы
        
        Args:
            spreadsheet_id: ID таблицы или None для использования из config
            
        Returns:
            bool: True если успешно
        """
        if not self.connector.is_connected():
            print("❌ Не подключен к Google Sheets")
            return False
        
        # Получаем ID таблицы
        if spreadsheet_id is None:
            spreadsheet_id = self.connector.get_config_spreadsheet('finance_tracking')
        
        if not spreadsheet_id:
            print("❌ ID таблицы для финансов не настроен")
            return False
        
        try:
            print(f"🔄 Настройка финансовой таблицы {spreadsheet_id}")
            
            # Создаем все необходимые листы
            budget_success = self.create_budget_template(spreadsheet_id)
            expense_success = self.create_expense_tracker(spreadsheet_id)
            investment_success = self.create_investment_tracker(spreadsheet_id)
            
            if budget_success and expense_success and investment_success:
                print("✅ Финансовая таблица настроена успешно")
                print(f"📊 Откройте таблицу: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
                return True
            else:
                print("⚠️ Настройка завершена с ошибками")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка настройки: {e}")
            return False

def main():
    """Пример использования финансовой интеграции"""
    print("💰 Google Sheets - Финансовая интеграция")
    print("=" * 50)
    
    # Создаем интеграцию
    finance_sync = FinanceSheetsSync()
    
    # Аутентификация
    if not finance_sync.authenticate():
        print("❌ Ошибка аутентификации")
        return
    
    # Получаем ID таблицы из конфигурации
    spreadsheet_id = finance_sync.connector.get_config_spreadsheet('finance_tracking')
    
    if not spreadsheet_id:
        print("❌ ID таблицы для финансов не настроен в config.json")
        print("Добавьте 'finance_tracking': 'your_spreadsheet_id' в config.json")
        return
    
    try:
        # Настройка финансовой таблицы
        print("🔄 Настройка финансовой таблицы...")
        success = finance_sync.setup_finance_spreadsheet(spreadsheet_id)
        
        if success:
            # Добавляем примерные расходы
            today = datetime.now().strftime("%Y-%m-%d")
            
            sample_expenses = [
                (today, "Питание", "Обед в кафе", 800, "Карта", "Кафе у офиса", "еда,обед"),
                (today, "Транспорт", "Такси", 300, "Карта", "Яндекс.Такси", "транспорт"),
                (today, "Здоровье", "Витамины", 1200, "Карта", "Аптека", "здоровье,витамины")
            ]
            
            print("\n💳 Добавление примерных расходов...")
            for expense in sample_expenses:
                finance_sync.add_expense(spreadsheet_id, *expense)
            
            # Генерируем отчет за текущий месяц
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            print(f"\n📊 Генерация отчета за {current_month:02d}.{current_year}...")
            finance_sync.generate_monthly_report(spreadsheet_id, current_month, current_year)
            
            print("\n🎉 Финансовая интеграция настроена!")
            print(f"📊 Откройте таблицу: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        else:
            print("\n❌ Настройка не удалась")
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
