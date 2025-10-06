#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для загрузки всех изображений через FTP в хранилище Beget
"""

import os
import sys
from pathlib import Path
import ftplib
from ftplib import FTP_TLS
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from tqdm import tqdm

# Настройки FTP
FTP_HOST = 'ftp.ru1.storage.beget.cloud'
FTP_USERNAME = 'RECD00AQJIM4300MLJ0W'
FTP_PASSWORD = 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
FTP_REMOTE_DIR = '/73d16f7545b3-promogoods/images'  # Папка на сервере

# Локальные настройки
LOCAL_IMAGES_DIR = Path('storage/images')
MAX_WORKERS = 2  # Количество одновременных загрузок (FTP ограничен)
BATCH_SIZE = 50  # Размер батча для отчета
UPLOAD_DELAY = 0.1  # Задержка между загрузками в секундах

class FTPImageUploader:
    def __init__(self):
        self.uploaded_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def upload_single_file(self, local_path, remote_path, max_retries=3):
        """Загружает один файл через FTP с повторными попытками"""
        for attempt in range(max_retries):
            try:
                # Создаем FTPS соединение
                ftp = FTP_TLS()
                ftp.connect(FTP_HOST, 21, timeout=30)
                ftp.login(FTP_USERNAME, FTP_PASSWORD)
                ftp.prot_p()  # Включаем защищенный режим передачи данных
                
                # Переходим в папку images
                try:
                    ftp.cwd(FTP_REMOTE_DIR)
                except ftplib.error_perm:
                    # Создаем папку если её нет
                    ftp.mkd(FTP_REMOTE_DIR)
                    ftp.cwd(FTP_REMOTE_DIR)
                
                # Создаем подпапки если нужно
                remote_dir = os.path.dirname(remote_path)
                if remote_dir and remote_dir != '.':
                    try:
                        ftp.cwd(remote_dir)
                    except ftplib.error_perm:
                        # Создаем подпапки
                        parts = remote_dir.split('/')
                        current_path = ''
                        for part in parts:
                            if part:
                                current_path += '/' + part
                                try:
                                    ftp.cwd(current_path)
                                except ftplib.error_perm:
                                    ftp.mkd(current_path)
                                    ftp.cwd(current_path)
                
                # Загружаем файл
                with open(local_path, 'rb') as f:
                    ftp.storbinary(f'STOR {os.path.basename(remote_path)}', f)
                
                # Закрываем соединение
                ftp.quit()
                
                # Добавляем задержку для соблюдения rate limit
                time.sleep(UPLOAD_DELAY)
                
                with self.lock:
                    self.uploaded_count += 1
                    if self.uploaded_count % BATCH_SIZE == 0:
                        elapsed = time.time() - self.start_time
                        rate = self.uploaded_count / elapsed
                        print(f"✅ Загружено: {self.uploaded_count} файлов, скорость: {rate:.1f} файл/сек")
                
                return True, None
                
            except ftplib.error_temp as e:
                if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                    # Rate limit - ждем дольше и повторяем
                    wait_time = (attempt + 1) * 2  # Увеличиваем время ожидания
                    print(f"⚠️  Rate limit для {local_path.name}, жду {wait_time} сек...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  Ошибка для {local_path.name}, повторяю через 1 сек...")
                    time.sleep(1)
                    continue
                else:
                    raise e
        
        # Если все попытки исчерпаны
        with self.lock:
            self.failed_count += 1
        return False, f"Не удалось загрузить после {max_retries} попыток"
    
    def test_connection(self):
        """Тестирует FTP соединение"""
        try:
            print("🔌 Тестирую FTPS соединение...")
            ftp = FTP_TLS()
            ftp.connect(FTP_HOST, 21, timeout=30)
            ftp.login(FTP_USERNAME, FTP_PASSWORD)
            ftp.prot_p()  # Включаем защищенный режим передачи данных
            
            print("✅ FTP соединение установлено!")
            
            # Проверяем текущую директорию
            current_dir = ftp.pwd()
            print(f"📁 Текущая директория: {current_dir}")
            
            # Пробуем создать папку для изображений
            try:
                ftp.mkd(FTP_REMOTE_DIR)
                print(f"✅ Папка {FTP_REMOTE_DIR} создана")
            except ftplib.error_perm as e:
                if "exists" in str(e).lower():
                    print(f"✅ Папка {FTP_REMOTE_DIR} уже существует")
                else:
                    print(f"⚠️  Не удалось создать папку: {e}")
            
            ftp.quit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка FTP соединения: {e}")
            return False
    
    def upload_images(self):
        """Загружает все изображения"""
        print("🚀 Начинаю загрузку изображений через FTP...")
        print(f"📁 Локальная папка: {LOCAL_IMAGES_DIR}")
        print(f"🌐 FTP сервер: {FTP_HOST}")
        print(f"📊 Максимум потоков: {MAX_WORKERS}")
        print()
        
        # Тестируем соединение
        if not self.test_connection():
            return
        
        # Получаем список всех файлов
        image_files = list(LOCAL_IMAGES_DIR.rglob('*'))
        image_files = [f for f in image_files if f.is_file()]
        
        print(f"📋 Найдено {len(image_files)} файлов для загрузки")
        print()
        
        if not image_files:
            print("❌ Файлы не найдены!")
            return
        
        # Создаем задачи для загрузки
        upload_tasks = []
        for local_path in image_files:
            # Создаем относительный путь
            relative_path = local_path.relative_to(LOCAL_IMAGES_DIR)
            remote_path = f"{FTP_REMOTE_DIR}/{relative_path}"
            
            upload_tasks.append((local_path, remote_path))
        
        # Загружаем файлы параллельно
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Отправляем все задачи
            future_to_task = {
                executor.submit(self.upload_single_file, local_path, remote_path): (local_path, remote_path)
                for local_path, remote_path in upload_tasks
            }
            
            # Обрабатываем результаты с прогресс-баром
            with tqdm(total=len(upload_tasks), desc="Загрузка изображений") as pbar:
                for future in as_completed(future_to_task):
                    local_path, remote_path = future_to_task[future]
                    try:
                        success, error = future.result()
                        if not success:
                            print(f"❌ Ошибка загрузки {local_path.name}: {error}")
                    except Exception as e:
                        print(f"❌ Критическая ошибка для {local_path.name}: {e}")
                    
                    pbar.update(1)
        
        # Финальная статистика
        total_time = time.time() - self.start_time
        print()
        print("=" * 60)
        print("📊 ФИНАЛЬНАЯ СТАТИСТИКА")
        print("=" * 60)
        print(f"✅ Успешно загружено: {self.uploaded_count} файлов")
        print(f"❌ Ошибок: {self.failed_count} файлов")
        print(f"⏱️  Общее время: {total_time:.1f} секунд")
        print(f"🚀 Средняя скорость: {self.uploaded_count/total_time:.1f} файл/сек")
        print(f"📈 Успешность: {self.uploaded_count/(self.uploaded_count+self.failed_count)*100:.1f}%")
        print()
        
        if self.uploaded_count > 0:
            print("🎉 Загрузка завершена!")
            print(f"🌐 Изображения доступны по адресу: https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/")
            print()
            print("📝 Для обновления веб-интерфейса:")
            print("1. Обновите URL изображений в базе данных")
            print("2. Измените serve_image функцию в app.py")
        else:
            print("❌ Загрузка не удалась!")

def main():
    """Основная функция"""
    print("🖼️  Загрузчик изображений через FTP в хранилище Beget")
    print("=" * 60)
    
    # Проверяем наличие папки с изображениями
    if not LOCAL_IMAGES_DIR.exists():
        print(f"❌ Папка с изображениями не найдена: {LOCAL_IMAGES_DIR}")
        return
    
    # Создаем загрузчик и запускаем
    uploader = FTPImageUploader()
    uploader.upload_images()

if __name__ == "__main__":
    main()
