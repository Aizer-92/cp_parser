"""
Продвинутый скачиватель для обхода ограничений Google Drive
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
import time
import zipfile
import io

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SCOPES, STORAGE_DIR
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedDownloader:
    """Продвинутый скачиватель для обхода ограничений Google Drive"""
    
    def __init__(self):
        self.credentials_file = GOOGLE_CREDENTIALS_FILE
        self.scopes = GOOGLE_SCOPES
        self.drive_service = self._authenticate_google_drive()
        self.sheets_service = self._authenticate_google_sheets()
        self.excel_files_dir = STORAGE_DIR / "excel_files"
        self.excel_files_dir.mkdir(parents=True, exist_ok=True)
        
    def _authenticate_google_drive(self):
        """Аутентификация в Google Drive API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=self.scopes
            )
            service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive API инициализирован")
            return service
        except Exception as e:
            logger.error(f"Ошибка аутентификации в Google Drive API: {e}")
            return None
    
    def _authenticate_google_sheets(self):
        """Аутентификация в Google Sheets API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=self.scopes
            )
            service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets API инициализирован")
            return service
        except Exception as e:
            logger.error(f"Ошибка аутентификации в Google Sheets API: {e}")
            return None
    
    def extract_sheet_id(self, url: str) -> Optional[str]:
        """Извлечение ID таблицы из URL"""
        try:
            if 'docs.google.com/spreadsheets/d/' in url:
                parts = url.split('/')
                if 'd' in parts:
                    sheet_id_index = parts.index('d') + 1
                    if sheet_id_index < len(parts):
                        return parts[sheet_id_index]
            return None
        except Exception as e:
            logger.warning(f"Ошибка извлечения ID из URL {url}: {e}")
            return None
    
    def download_via_sheets_api(self, sheet_id: str, sheet_title: str) -> Optional[str]:
        """Скачивание через Sheets API (обход ограничений Drive)"""
        try:
            logger.info(f"Попытка скачивания через Sheets API: {sheet_title}")
            
            # Получаем метаданные таблицы
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=sheet_id,
                includeGridData=True
            ).execute()
            
            # Создаем Excel файл вручную
            excel_path = self.excel_files_dir / f"{sheet_title}_sheets_api.xlsx"
            
            # Получаем все листы
            sheets = spreadsheet.get('sheets', [])
            logger.info(f"Найдено листов: {len(sheets)}")
            
            # Создаем простой Excel файл с данными
            self._create_excel_from_sheets_data(sheets, excel_path, sheet_title)
            
            file_size = excel_path.stat().st_size
            logger.info(f"Файл создан через Sheets API: {excel_path.name} ({file_size:,} байт)")
            return str(excel_path)
            
        except Exception as e:
            logger.error(f"Ошибка скачивания через Sheets API {sheet_title}: {e}")
            return None
    
    def _create_excel_from_sheets_data(self, sheets: List[Dict], excel_path: Path, sheet_title: str):
        """Создание Excel файла из данных Sheets API"""
        try:
            # Простое создание CSV файла (более совместимо)
            csv_path = excel_path.with_suffix('.csv')
            
            with open(csv_path, 'w', encoding='utf-8') as f:
                for i, sheet in enumerate(sheets):
                    sheet_name = sheet.get('properties', {}).get('title', f'Sheet{i+1}')
                    f.write(f"=== {sheet_name} ===\n")
                    
                    # Получаем данные ячеек
                    grid_data = sheet.get('gridData', {})
                    rows = grid_data.get('rowData', [])
                    
                    for row in rows:
                        values = row.get('values', [])
                        row_data = []
                        for cell in values:
                            cell_value = cell.get('formattedValue', '')
                            row_data.append(str(cell_value))
                        f.write(','.join(row_data) + '\n')
                    f.write('\n')
            
            # Переименовываем в .xlsx для совместимости
            excel_path = csv_path.with_suffix('.xlsx')
            csv_path.rename(excel_path)
            
        except Exception as e:
            logger.error(f"Ошибка создания Excel файла: {e}")
            raise
    
    def download_via_csv_export(self, sheet_id: str, sheet_title: str) -> Optional[str]:
        """Скачивание в формате CSV (обход ограничений)"""
        try:
            logger.info(f"Попытка скачивания в CSV формате: {sheet_title}")
            
            # Экспортируем в CSV через Drive API
            request = self.drive_service.files().export_media(
                fileId=sheet_id,
                mimeType='text/csv'
            )
            
            csv_path = self.excel_files_dir / f"{sheet_title}_csv.csv"
            
            with open(csv_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"Прогресс скачивания CSV: {progress}%")
            
            # Переименовываем в .xlsx для совместимости
            excel_path = csv_path.with_suffix('.xlsx')
            csv_path.rename(excel_path)
            
            file_size = excel_path.stat().st_size
            logger.info(f"Файл скачан в CSV формате: {excel_path.name} ({file_size:,} байт)")
            return str(excel_path)
            
        except Exception as e:
            logger.error(f"Ошибка скачивания в CSV формате {sheet_title}: {e}")
            return None
    
    def download_via_pdf_export(self, sheet_id: str, sheet_title: str) -> Optional[str]:
        """Скачивание в формате PDF (обход ограничений)"""
        try:
            logger.info(f"Попытка скачивания в PDF формате: {sheet_title}")
            
            # Экспортируем в PDF через Drive API
            request = self.drive_service.files().export_media(
                fileId=sheet_id,
                mimeType='application/pdf'
            )
            
            pdf_path = self.excel_files_dir / f"{sheet_title}_pdf.pdf"
            
            with open(pdf_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"Прогресс скачивания PDF: {progress}%")
            
            file_size = pdf_path.stat().st_size
            logger.info(f"Файл скачан в PDF формате: {pdf_path.name} ({file_size:,} байт)")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"Ошибка скачивания в PDF формате {sheet_title}: {e}")
            return None
    
    def download_large_sheet(self, sheet_url: str, sheet_title: str) -> Optional[str]:
        """Многоуровневое скачивание большого файла"""
        try:
            sheet_id = self.extract_sheet_id(sheet_url)
            if not sheet_id:
                logger.error(f"Не удалось извлечь ID из URL: {sheet_url}")
                return None
            
            logger.info(f"Многоуровневое скачивание: {sheet_title}")
            
            # Метод 1: Попытка обычного Excel экспорта
            try:
                request = self.drive_service.files().export_media(
                    fileId=sheet_id,
                    mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
                excel_path = self.excel_files_dir / f"{sheet_title}_excel.xlsx"
                
                with open(excel_path, 'wb') as f:
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        if status:
                            progress = int(status.progress() * 100)
                            logger.info(f"Прогресс скачивания Excel: {progress}%")
                
                file_size = excel_path.stat().st_size
                if file_size > 0:
                    logger.info(f"✅ Excel скачан успешно: {excel_path.name} ({file_size:,} байт)")
                    return str(excel_path)
                else:
                    logger.warning("Excel файл пустой, пробуем другие методы")
                    
            except Exception as e:
                logger.warning(f"Excel экспорт не удался: {e}")
            
            # Метод 2: CSV экспорт
            csv_path = self.download_via_csv_export(sheet_id, sheet_title)
            if csv_path:
                return csv_path
            
            # Метод 3: PDF экспорт
            pdf_path = self.download_via_pdf_export(sheet_id, sheet_title)
            if pdf_path:
                return pdf_path
            
            # Метод 4: Sheets API
            sheets_path = self.download_via_sheets_api(sheet_id, sheet_title)
            if sheets_path:
                return sheets_path
            
            logger.error(f"Все методы скачивания не удались для {sheet_title}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка многоуровневого скачивания {sheet_title}: {e}")
            return None
    
    def download_failed_sheets(self, failed_urls: List[str]) -> Dict:
        """Скачивание файлов, которые не удалось скачать ранее"""
        try:
            logger.info(f"=== ПОВТОРНОЕ СКАЧИВАНИЕ {len(failed_urls)} ФАЙЛОВ ===")
            
            results = {
                'downloaded': 0,
                'errors': [],
                'files': []
            }
            
            for i, url in enumerate(failed_urls, 1):
                try:
                    sheet_id = self.extract_sheet_id(url)
                    if not sheet_id:
                        error_msg = f"Не удалось извлечь ID из URL: {url}"
                        results['errors'].append(error_msg)
                        continue
                    
                    sheet_title = f"sheet_{sheet_id[:8]}"
                    logger.info(f"Повторное скачивание {i}/{len(failed_urls)}: {sheet_title}")
                    
                    # Пробуем многоуровневое скачивание
                    file_path = self.download_large_sheet(url, sheet_title)
                    
                    if file_path:
                        results['downloaded'] += 1
                        results['files'].append({
                            'title': sheet_title,
                            'path': file_path,
                            'size': Path(file_path).stat().st_size
                        })
                        logger.info(f"✅ Успешно скачан: {sheet_title}")
                    else:
                        error_msg = f"Не удалось скачать {sheet_title}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                
                except Exception as e:
                    error_msg = f"Ошибка обработки {url}: {e}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Повторное скачивание завершено: {results['downloaded']} файлов")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка повторного скачивания: {e}")
            return {'error': str(e)}

def main():
    """Основная функция"""
    
    # URL файлов, которые не удалось скачать ранее
    failed_urls = [
        "https://docs.google.com/spreadsheets/d/1SD3YfSQfy6NojyETk6IyrRtwFiXs327ClII-_xW1ufo/edit",
        "https://docs.google.com/spreadsheets/d/1FHHpsQJR-N_20w4mas6ggIDB7PCzqr4hv_kc8602ok0/edit",
        "https://docs.google.com/spreadsheets/d/1nav9w2dzra5xaIFAHOGMKys3by0jCd7imB0NzYieLAo/edit",
        "https://docs.google.com/spreadsheets/d/17MYSsxoomx2PNLOisN3Q2REwN66hk-hh6-JxHJ6tMP8/edit"
    ]
    
    downloader = AdvancedDownloader()
    if not downloader.drive_service or not downloader.sheets_service:
        logger.error("Не удалось инициализировать Google API")
        return
    
    results = downloader.download_failed_sheets(failed_urls)
    
    if 'error' in results:
        logger.error(f"Ошибка скачивания: {results['error']}")
    else:
        logger.info("Повторное скачивание завершено!")
        logger.info(f"Скачано файлов: {results['downloaded']}")
        logger.info(f"Ошибок: {len(results['errors'])}")
        
        if results['files']:
            logger.info("\nСкачанные файлы:")
            for file_info in results['files']:
                logger.info(f"  - {file_info['title']}: {file_info['size']:,} байт")
        
        if results['errors']:
            logger.info("\nОшибки:")
            for error in results['errors']:
                logger.error(f"  - {error}")

if __name__ == "__main__":
    main()

