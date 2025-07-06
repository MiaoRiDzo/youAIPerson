#!/usr/bin/env python3
"""
Telegram Bot Memory - Main Entry Point
Центральный файл для запуска Telegram-бота
"""

import asyncio
import sys
import os

# Добавляем корневую папку в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.bot import main


if __name__ == "__main__":
    try:
        print("🚀 Запуск Telegram Bot Memory...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1) 