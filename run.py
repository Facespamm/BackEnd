#!/usr/bin/env python3
"""
Запуск приложения Judo Tournament Management System
"""

import os
import sys
from app import create_app

# Добавляем корневую директорию в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = create_app()

if __name__ == '__main__':
    print("🥋 Judo Tournament Management System")
    print("🚀 Запуск сервера...")
    # print("📊 Админка: http://localhost:5000/admin")
    # print("🎯 Судьи: http://localhost:5000/referee")
    # print("📺 Табло: http://localhost:5000/scoreboard")
    # print("🌐 Публичная: http://localhost:5000/public")
    # print("⏹️  Остановка: Ctrl+C")

    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")