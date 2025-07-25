#!/usr/bin/env python3
"""
Скрипт быстрого запуска AudioFlow
"""
import os
import sys
import subprocess

def main():
    """Основная функция запуска"""
    print("🎧 AudioFlow - Запуск приложения")
    print("=" * 40)
    
    # Проверка файла requirements.txt
    if not os.path.exists("requirements.txt"):
        print("❌ Файл requirements.txt не найден!")
        return
    
    # Проверка виртуального окружения
    if not os.path.exists("venv"):
        print("📦 Создание виртуального окружения...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        print("✅ Виртуальное окружение создано")
    
    # Определение команды активации
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:  # Linux/Mac
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Установка зависимостей
    print("📦 Установка зависимостей...")
    result = subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Ошибка установки зависимостей:")
        print(result.stderr)
        return
    
    print("✅ Зависимости установлены")
    
    # Проверка базы данных
    if not os.path.exists("audioflow.db"):
        print("🗄️ Инициализация базы данных...")
        result = subprocess.run([python_cmd, "scripts/init_db.py"])
        
        if result.returncode != 0:
            print("❌ Ошибка инициализации базы данных")
            return
    
    # Запуск сервера
    print("\n🚀 Запуск сервера AudioFlow...")
    print("📱 Приложение будет доступно по адресу: http://localhost:8000")
    print("⚙️ Админ панель: http://localhost:8000/admin/login")
    print("📚 API документация: http://localhost:8000/docs")
    print("\n🛑 Для остановки нажмите Ctrl+C")
    print("=" * 40)
    
    try:
        # Запуск uvicorn
        subprocess.run([
            python_cmd, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Сервер остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка запуска сервера: {e}")

if __name__ == "__main__":
    main() 