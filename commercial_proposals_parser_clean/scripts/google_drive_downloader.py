"""
Скачивание Google Sheets таблиц в формате Excel
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
import time
from urllib.parse import urlparse, parse_qs

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SCOPES, STORAGE_DIR
from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDriveDownloader:
    """Скачивание Google Sheets таблиц в формате Excel"""
    
    def __init__(self):
        self.credentials_file = GOOGLE_CREDENTIALS_FILE
        self.scopes = GOOGLE_SCOPES
        self.drive_service = self._authenticate_google_drive()
        self.db_manager = DatabaseManager
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
    
    def extract_sheet_id(self, url: str) -> Optional[str]:
        """Извлечение ID таблицы из URL"""
        try:
            if 'docs.google.com/spreadsheets/d/' in url:
                # Формат: https://docs.google.com/spreadsheets/d/SHEET_ID/edit
                parts = url.split('/')
                if 'd' in parts:
                    sheet_id_index = parts.index('d') + 1
                    if sheet_id_index < len(parts):
                        return parts[sheet_id_index]
            elif 'drive.google.com/file/d/' in url:
                # Формат: https://drive.google.com/file/d/FILE_ID/view
                parts = url.split('/')
                if 'd' in parts:
                    file_id_index = parts.index('d') + 1
                    if file_id_index < len(parts):
                        return parts[file_id_index]
            return None
        except Exception as e:
            logger.warning(f"Ошибка извлечения ID из URL {url}: {e}")
            return None
    
    def download_sheet_as_excel(self, sheet_url: str, sheet_title: str = None) -> Optional[str]:
        """Скачивание Google Sheets таблицы в формате Excel"""
        try:
            logger.info(f"Скачивание таблицы: {sheet_title or 'Unknown'}")
            
            # Извлекаем ID таблицы
            sheet_id = self.extract_sheet_id(sheet_url)
            if not sheet_id:
                logger.error(f"Не удалось извлечь ID из URL: {sheet_url}")
                return None
            
            logger.info(f"ID таблицы: {sheet_id}")
            
            # Скачиваем файл в формате Excel
            request = self.drive_service.files().export_media(
                fileId=sheet_id,
                mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            # Генерируем имя файла
            if not sheet_title:
                sheet_title = f"sheet_{sheet_id[:8]}"
            
            # Очищаем имя файла от недопустимых символов
            clean_title = self._clean_filename(sheet_title)
            timestamp = int(time.time())
            filename = f"{clean_title}_{timestamp}.xlsx"
            excel_path = self.excel_files_dir / filename
            
            # Скачиваем файл
            with open(excel_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"Прогресс скачивания: {progress}%")
            
            file_size = excel_path.stat().st_size
            logger.info(f"Файл скачан: {excel_path.name} ({file_size:,} байт)")
            return str(excel_path)
            
        except Exception as e:
            logger.error(f"Ошибка скачивания {sheet_title}: {e}")
            return None
    
    def _clean_filename(self, filename: str) -> str:
        """Очистка имени файла от недопустимых символов"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:100]  # Ограничиваем длину
    
    def download_sheets_from_db(self, limit: int = 10) -> Dict:
        """Скачивание таблиц из базы данных"""
        try:
            logger.info(f"=== СКАЧИВАНИЕ GOOGLE SHEETS (лимит: {limit}) ===")
            
            session = self.db_manager.get_session()
            
            try:
                # Получаем листы со статусом 'pending'
                sheets = session.query(SheetMetadata).filter(
                    SheetMetadata.status == 'pending'
                ).limit(limit).all()
                
                if not sheets:
                    logger.info("Нет листов для скачивания")
                    return {'downloaded': 0, 'errors': []}
                
                logger.info(f"Найдено {len(sheets)} листов для скачивания")
                
                results = {
                    'downloaded': 0,
                    'skipped': 0,
                    'errors': [],
                    'files': []
                }
                
                for i, sheet in enumerate(sheets, 1):
                    try:
                        logger.info(f"Скачивание {i}/{len(sheets)}: {sheet.sheet_title}")
                        
                        # Проверяем, не скачан ли уже файл
                        if sheet.local_file_path and Path(sheet.local_file_path).exists():
                            logger.info(f"Файл уже существует: {sheet.local_file_path}")
                            results['skipped'] += 1
                            continue
                        
                        # Скачиваем файл
                        excel_path = self.download_sheet_as_excel(
                            sheet.sheet_url, 
                            sheet.sheet_title
                        )
                        
                        if excel_path:
                            # Обновляем запись в БД
                            sheet.local_file_path = excel_path
                            sheet.status = 'downloaded'
                            sheet.updated_at = time.time()
                            
                            results['downloaded'] += 1
                            results['files'].append({
                                'title': sheet.sheet_title,
                                'path': excel_path,
                                'size': Path(excel_path).stat().st_size
                            })
                            
                            logger.info(f"✅ Скачан: {sheet.sheet_title}")
                        else:
                            sheet.status = 'error'
                            error_msg = f"Ошибка скачивания {sheet.sheet_title}"
                            results['errors'].append(error_msg)
                            logger.error(error_msg)
                    
                    except Exception as e:
                        error_msg = f"Ошибка обработки {sheet.sheet_title}: {e}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                
                session.commit()
                logger.info(f"Скачивание завершено: {results['downloaded']} файлов")
                
                return results
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Ошибка скачивания листов: {e}")
            return {'error': str(e)}
    
    def download_specific_sheets(self, sheet_urls: List[str]) -> Dict:
        """Скачивание конкретных таблиц по URL"""
        try:
            logger.info(f"=== СКАЧИВАНИЕ КОНКРЕТНЫХ ТАБЛИЦ ===")
            
            results = {
                'downloaded': 0,
                'errors': [],
                'files': []
            }
            
            for i, url in enumerate(sheet_urls, 1):
                try:
                    logger.info(f"Скачивание {i}/{len(sheet_urls)}: {url}")
                    
                    # Извлекаем название из URL или используем номер
                    sheet_title = f"sheet_{i}"
                    sheet_id = self.extract_sheet_id(url)
                    if sheet_id:
                        sheet_title = f"sheet_{sheet_id[:8]}"
                    
                    # Скачиваем файл
                    excel_path = self.download_sheet_as_excel(url, sheet_title)
                    
                    if excel_path:
                        results['downloaded'] += 1
                        results['files'].append({
                            'title': sheet_title,
                            'path': excel_path,
                            'size': Path(excel_path).stat().st_size
                        })
                        logger.info(f"✅ Скачан: {sheet_title}")
                    else:
                        error_msg = f"Ошибка скачивания {url}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                
                except Exception as e:
                    error_msg = f"Ошибка скачивания {url}: {e}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Скачивание завершено: {results['downloaded']} файлов")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка скачивания таблиц: {e}")
            return {'error': str(e)}

def main():
    """Основная функция"""
    downloader = GoogleDriveDownloader()
    if not downloader.drive_service:
        logger.error("Не удалось инициализировать Google Drive API")
        return
    
    # Скачиваем листы из базы данных
    results = downloader.download_sheets_from_db(limit=10)
    
    if 'error' in results:
        logger.error(f"Ошибка скачивания: {results['error']}")
    else:
        logger.info("Скачивание завершено!")
        logger.info(f"Скачано файлов: {results['downloaded']}")
        logger.info(f"Пропущено файлов: {results.get('skipped', 0)}")
        if results['errors']:
            logger.info(f"Ошибок: {len(results['errors'])}")

if __name__ == "__main__":
    main()