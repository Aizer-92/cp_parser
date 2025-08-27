#!/usr/bin/env python3
"""
Синхронизация с Google Drive
Требует установки: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import os
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

class GoogleDriveSync:
    def __init__(self, credentials_path='credentials.json', token_path='token.pickle'):
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        
    def authenticate(self):
        """Аутентификация в Google Drive API"""
        creds = None
        
        # Загружаем сохраненные токены
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
                
        # Если нет валидных токенов, запрашиваем новые
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print("❌ Файл credentials.json не найден!")
                    print("💡 Скачайте его из Google Cloud Console")
                    return False
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Сохраняем токены
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
                
        self.service = build('drive', 'v3', credentials=creds)
        return True
        
    def create_folder(self, folder_name, parent_id=None):
        """Создает папку в Google Drive"""
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
            
        try:
            folder = self.service.files().create(
                body=file_metadata, fields='id').execute()
            print(f"✅ Создана папка: {folder_name}")
            return folder.get('id')
        except Exception as e:
            print(f"❌ Ошибка создания папки: {e}")
            return None
            
    def find_folder(self, folder_name, parent_id=None):
        """Находит папку по имени"""
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_id:
            query += f" and '{parent_id}' in parents"
            
        try:
            results = self.service.files().list(
                q=query, spaces='drive', fields='files(id, name)').execute()
            files = results.get('files', [])
            return files[0]['id'] if files else None
        except Exception as e:
            print(f"❌ Ошибка поиска папки: {e}")
            return None
            
    def upload_file(self, file_path, folder_id=None):
        """Загружает файл в Google Drive"""
        if not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            return None
            
        file_metadata = {'name': os.path.basename(file_path)}
        if folder_id:
            file_metadata['parents'] = [folder_id]
            
        try:
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata, media_body=media, fields='id').execute()
            print(f"✅ Загружен файл: {os.path.basename(file_path)}")
            return file.get('id')
        except Exception as e:
            print(f"❌ Ошибка загрузки файла: {e}")
            return None
            
    def sync_folder(self, local_folder, drive_folder_name, exclude_patterns=None):
        """Синхронизирует локальную папку с Google Drive"""
        if not self.service:
            if not self.authenticate():
                return False
                
        # Находим или создаем папку в Drive
        folder_id = self.find_folder(drive_folder_name)
        if not folder_id:
            folder_id = self.create_folder(drive_folder_name)
            
        if not folder_id:
            return False
            
        # Обходим файлы в локальной папке
        for root, dirs, files in os.walk(local_folder):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Пропускаем исключенные файлы
                if exclude_patterns:
                    skip = False
                    for pattern in exclude_patterns:
                        if pattern in file_path:
                            skip = True
                            break
                    if skip:
                        continue
                        
                # Загружаем файл
                self.upload_file(file_path, folder_id)
                
        return True

def main():
    # Пример использования
    sync = GoogleDriveSync()
    
    # Синхронизируем папку Docs
    docs_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Docs')
    
    exclude_patterns = [
        '__pycache__',
        '.DS_Store',
        'venv',
        '.git',
        '*.log',
        'temp',
        'tmp'
    ]
    
    if sync.sync_folder(docs_folder, 'Reshad_Docs', exclude_patterns):
        print("✅ Синхронизация завершена!")
    else:
        print("❌ Ошибка синхронизации")

if __name__ == "__main__":
    main()
