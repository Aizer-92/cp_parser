#!/usr/bin/env python3
"""
Простой запуск Planfix Dashboard 2025
"""

import os
import sys
import subprocess

def main():
    print("🚀 Запуск Planfix Dashboard 2025...")
    
    # Путь к проекту
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Активируем виртуальное окружение и запускаем
    if os.name == 'nt':  # Windows
        activate_script = os.path.join(project_dir, 'venv', 'Scripts', 'activate.bat')
        cmd = f'call "{activate_script}" && python final_dashboard.py'
        subprocess.run(cmd, shell=True)
    else:  # macOS/Linux
        activate_script = os.path.join(project_dir, 'venv', 'bin', 'activate')
        cmd = f'source "{activate_script}" && python3 final_dashboard.py'
        subprocess.run(cmd, shell=True, executable='/bin/bash')

if __name__ == "__main__":
    main()
