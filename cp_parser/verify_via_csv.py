#!/usr/bin/env python3
"""
Проверка тиражей через CSV экспорт (быстрее чем Excel)
Работает в отдельной папке verification_csv/
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import json
import gspread
from google.oauth2.service_account import Credentials
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import os
import csv
from datetime import datetime
import time

# Railway DB
os.environ['USE_RAILWAY_DB'] = 'true'

def download_csv(sheet_id, output_path):
    """Скачивает Google Sheet как CSV (первый лист)"""
    try:
        scope = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
        
        # CSV экспорт (gid=0 = первый лист)
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        
        import requests
        response = requests.get(export_url, headers={'Authorization': f'Bearer {creds.token}'})
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"  ❌ {str(e)[:40]}")
        return False

def extract_quantity_from_csv(csv_path, row_number):
    """Извлекает тираж из колонки E (индекс 4) указанной строки"""
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # row_number это номер строки в Excel (1-based)
            # В Python списке индекс на 1 меньше
            if row_number <= len(rows):
                row_data = rows[row_number - 1]
                
                # Колонка E = индекс 4
                if len(row_data) > 4:
                    cell_value = row_data[4]
                    
                    if not cell_value:
                        return None
                    
                    try:
                        return int(float(str(cell_value).replace(',', '').replace(' ', '')))
                    except:
                        return str(cell_value)
        
        return None
            
    except Exception as e:
        return None

def verify_project(project_data, db, csv_dir):
    """Проверяет проект через CSV"""
    project_id = project_data['id']
    sheet_id = project_data['sheet_id']
    
    print(f"\n{'='*70}")
    print(f"🔍 ID {project_id}: {project_data['name'][:55]}")
    
    csv_path = csv_dir / f"project_{project_id}.csv"
    print(f"📥 CSV...", end=' ', flush=True)
    
    if not download_csv(sheet_id, csv_path):
        return None
    
    size_kb = csv_path.stat().st_size / 1024
    print(f"✅ {size_kb:.0f} KB")
    
    with db.get_session() as session:
        products = session.execute(text("""
            SELECT 
                p.id, p.name, p.row_number,
                po.quantity, po.route
            FROM products p
            INNER JOIN price_offers po ON p.id = po.product_id
            WHERE p.project_id = :pid
            AND po.quantity >= 300
            AND po.quantity % 10 = 0
            ORDER BY p.row_number
        """), {'pid': project_id}).fetchall()
        
        if not products:
            print(f"⚠️  Нет подозрительных товаров")
            return None
        
        print(f"📊 Проверяю {len(products)} записей...", end=' ', flush=True)
        
        results = []
        checked_rows = {}
        
        for prod in products:
            row_num = prod.row_number
            
            if row_num not in checked_rows:
                checked_rows[row_num] = extract_quantity_from_csv(csv_path, row_num)
            
            excel_qty = checked_rows[row_num]
            db_qty = int(prod.quantity)
            
            is_x10 = False
            if excel_qty and isinstance(excel_qty, int) and excel_qty * 10 == db_qty:
                is_x10 = True
            
            results.append({
                'product_id': prod.id,
                'product_name': prod.name,
                'row': row_num,
                'excel': excel_qty,
                'db': db_qty,
                'route': prod.route,
                'is_x10': is_x10
            })
        
        x10_count = sum(1 for r in results if r['is_x10'])
        ok_count = sum(1 for r in results if r['excel'] == r['db'])
        
        print(f"Done!")
        print(f"  ❌ x10: {x10_count}/{len(results)} ({x10_count/len(results)*100:.0f}%)", end='')
        print(f"  ✅ OK: {ok_count}/{len(results)} ({ok_count/len(results)*100:.0f}%)")
        
        if x10_count > 0:
            print(f"  📋 Примеры:")
            shown = 0
            for r in results:
                if r['is_x10'] and shown < 2:
                    print(f"    Р{r['row']}: {r['excel']} → {r['db']}")
                    shown += 1
        
        return {
            'id': project_id,
            'name': project_data['name'],
            'url': project_data['url'],
            'total': len(results),
            'x10': x10_count,
            'ok': ok_count,
            'results': results
        }

def main():
    print("="*70)
    print("🔍 ПРОВЕРКА ТИРАЖЕЙ ЧЕРЕЗ CSV")
    print("="*70)
    
    with open('projects_to_verify.json', 'r', encoding='utf-8') as f:
        projects = json.load(f)
    
    print(f"\n📋 Проверяю все {len(projects)} проектов")
    print(f"📁 CSV файлы в: verification_csv/\n")
    
    # Отдельная папка для CSV
    csv_dir = Path('verification_csv')
    csv_dir.mkdir(exist_ok=True)
    
    db = PostgreSQLManager()
    all_results = []
    
    start_time = time.time()
    
    for i, proj in enumerate(projects, 1):
        print(f"\n{'#'*70}")
        print(f"# {i}/{len(projects)}")
        
        result = verify_project(proj, db, csv_dir)
        if result:
            all_results.append(result)
        
        # Показываем промежуточный прогресс каждые 10 проектов
        if i % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(projects) - i) * avg_time
            print(f"\n⏱️  Прогресс: {i}/{len(projects)} | Осталось: ~{remaining/60:.1f} мин")
        
        time.sleep(0.3)  # Небольшая пауза между запросами
    
    # Итог
    print("\n\n" + "="*70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*70)
    
    if not all_results:
        print("\n⚠️  Не удалось проверить ни одного проекта")
        return
    
    total_x10 = sum(r['x10'] for r in all_results)
    total_rec = sum(r['total'] for r in all_results)
    projects_with_errors = len([r for r in all_results if r['x10'] > 0])
    
    print(f"\n✅ Проверено: {len(all_results)} проектов")
    print(f"📊 Всего записей: {total_rec:,}")
    print(f"❌ Ошибок x10: {total_x10:,} ({total_x10/total_rec*100:.1f}%)")
    print(f"⚠️  Проектов с ошибками: {projects_with_errors}/{len(all_results)}")
    
    # Топ проектов с ошибками
    error_projects = sorted([r for r in all_results if r['x10'] > 0], 
                          key=lambda x: x['x10'], reverse=True)
    
    if error_projects:
        print(f"\n📋 ТОП-20 ПРОЕКТОВ С ОШИБКАМИ:")
        for r in error_projects[:20]:
            pct = r['x10']/r['total']*100 if r['total'] > 0 else 0
            print(f"  ❌ ID {r['id']}: {r['x10']}/{r['total']} ({pct:.0f}%) - {r['name'][:50]}")
    
    # CSV отчет
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    csv_report = Path(f"ПРОВЕРКА_ТИРАЖЕЙ_50_ПРОЕКТОВ_{timestamp}.csv")
    
    with open(csv_report, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID_Проекта', 'Название_проекта', 'ID_Товара', 'Название_товара',
            'Строка', 'Тираж_Google', 'Тираж_БД', 'Маршрут', 'Ошибка_x10', 'URL'
        ])
        
        for proj in all_results:
            for r in proj['results']:
                writer.writerow([
                    proj['id'], proj['name'],
                    r['product_id'], r['product_name'],
                    r['row'], r['excel'], r['db'],
                    r['route'], 'ДА' if r['is_x10'] else 'НЕТ',
                    proj['url']
                ])
    
    print(f"\n💾 Детальный отчет: {csv_report}")
    print(f"📁 CSV файлы сохранены: verification_csv/")
    
    # Вывод рекомендации
    if total_x10 > 0:
        error_pct = total_x10 / total_rec * 100
        print(f"\n💡 РЕКОМЕНДАЦИЯ:")
        if error_pct > 10:
            print(f"   🚨 КРИТИЧНО: {error_pct:.1f}% ошибок!")
            print(f"   Рекомендуется массовое исправление для {projects_with_errors} проектов")
        elif error_pct > 5:
            print(f"   ⚠️  Средний уровень ошибок ({error_pct:.1f}%)")
            print(f"   Проверить проекты с ошибками >10%")
        else:
            print(f"   ✅ Низкий уровень ошибок ({error_pct:.1f}%)")
            print(f"   Выборочная проверка проектов с ошибками")
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Время выполнения: {elapsed/60:.1f} минут")
    print("="*70)

if __name__ == '__main__':
    main()




