"""
SFTP Uploader для загрузки фотографий на Beget Cloud
"""
import os
import paramiko
from typing import List, Optional
from datetime import datetime
import io


class SFTPUploader:
    """Класс для загрузки файлов на SFTP сервер"""
    
    def __init__(self):
        self.host = os.getenv('SFTP_HOST', 'sftp.ru1.storage.beget.cloud')
        self.username = os.getenv('SFTP_USER', 'RECD00AQJIM4300MLJ0W')
        self.password = os.getenv('SFTP_PASSWORD', 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf')
        # Загружаем в корневую папку (нет прав на создание подпапок)
        self.base_path = ''
        
    def _get_connection(self):
        """Создать SFTP соединение"""
        transport = paramiko.Transport((self.host, 22))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        return sftp, transport
    
    def upload_photo(self, file_content: bytes, filename: str, position_id: int = None) -> str:
        """
        Загрузить фото на SFTP
        
        Args:
            file_content: содержимое файла в байтах
            filename: оригинальное имя файла
            position_id: ID позиции для организации папок (опционально)
            
        Returns:
            URL загруженного файла
        """
        sftp = None
        transport = None
        
        try:
            sftp, transport = self._get_connection()
            
            # Создаем уникальное имя файла с timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # микросекунды для уникальности
            
            # Извлекаем расширение (обрабатываем кириллицу)
            import re
            ext = os.path.splitext(filename)[1].lower()
            if not ext or len(ext) > 5:
                ext = '.jpg'  # По умолчанию если расширение странное
            
            # Создаем безопасное имя (только ASCII)
            if position_id:
                new_filename = f"pos_{position_id}_{timestamp}{ext}"
            else:
                new_filename = f"calc_{timestamp}{ext}"
            
            # Полный путь на сервере (просто имя файла)
            remote_path = new_filename
            
            # Загружаем файл в корневую папку
            print(f"📤 Загрузка файла: {remote_path}")
            with io.BytesIO(file_content) as file_obj:
                sftp.putfo(file_obj, remote_path)
            
            # Формируем публичный URL
            # Предполагаем что файлы доступны через HTTP
            public_url = f"https://ru1.storage.beget.cloud/{self.username}/{remote_path}"
            
            return public_url
            
        except Exception as e:
            print(f"❌ Ошибка загрузки на SFTP: {e}")
            raise
            
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()
    
    def upload_multiple_photos(
        self, 
        files: List[tuple], 
        position_id: int
    ) -> List[str]:
        """
        Загрузить несколько фотографий
        
        Args:
            files: список кортежей (file_content, filename)
            position_id: ID позиции
            
        Returns:
            список URL загруженных файлов
        """
        urls = []
        for file_content, filename in files:
            try:
                url = self.upload_photo(file_content, filename, position_id)
                urls.append(url)
            except Exception as e:
                print(f"⚠️ Не удалось загрузить {filename}: {e}")
                continue
        
        return urls
    
    def delete_photo(self, url: str) -> bool:
        """
        Удалить фото по URL
        
        Args:
            url: URL файла для удаления
            
        Returns:
            True если успешно удалено
        """
        sftp = None
        transport = None
        
        try:
            # Извлекаем путь из URL
            if '/calc/' not in url:
                return False
            
            path = url.split('/calc/')[1]
            remote_path = f"{self.base_path}{path}"
            
            sftp, transport = self._get_connection()
            sftp.remove(remote_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка удаления с SFTP: {e}")
            return False
            
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()


