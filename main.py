#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot для базы знаний Homeline Токмак
Модульная версия - исправлена проблема с отправкой ответов

Запуск: python main.py
"""

import os
import time
import signal
import sys

# Импортируем наши модули
from config import BASE_FOLDER, DEBUG_MODE
from telegram_api import get_updates, check_bot_connection
from handlers import process_message, process_callback


def signal_handler(sig, frame):
    """Обработчик сигнала прерывания (Ctrl+C)"""
    print("\n🛑 Получен сигнал остановки...")
    print("👋 Бот остановлен!")
    sys.exit(0)


def check_requirements():
    """Проверить все требования для запуска"""
    print("🔍 Проверка требований...")
    
    # Проверить папку с файлами
    if not os.path.exists(BASE_FOLDER):
        print(f"❌ Папка '{BASE_FOLDER}' не найдена!")
        print("🔧 Скачайте папку из Google Drive")
        return False
    print("✅ Папка с PDF файлами найдена")
    
    # Проверить библиотеку requests
    try:
        import requests
        print("✅ Библиотека requests доступна")
    except ImportError:
        print("❌ Установите: pip install requests")
        return False
    
    # Проверить подключение к боту
    if not check_bot_connection():
        return False
    
    return True


def main_loop():
    """Основной цикл бота"""
    update_offset = 0
    
    print("🤖 Бот запущен! Используется requests polling")
    print("📱 Найдите бота в Telegram и отправьте /start")
    print("🛑 Нажмите Ctrl+C для остановки")
    
    if DEBUG_MODE:
        print("🔍 Режим отладки включен - все действия будут логироваться")
    
    while True:
        try:
            updates = get_updates(update_offset)
            
            for update in updates:
                update_offset = update["update_id"] + 1
                
                if "message" in update:
                    if DEBUG_MODE:
                        user_text = update["message"].get("text", "")
                        user_id = update["message"]["from"].get("id", "unknown")
                        print(f"DEBUG: Получено сообщение от {user_id}: '{user_text}'")
                    process_message(update["message"])
                    
                elif "callback_query" in update:
                    if DEBUG_MODE:
                        callback_data = update["callback_query"].get("data", "")
                        user_id = update["callback_query"]["from"].get("id", "unknown")
                        print(f"DEBUG: Получен callback от {user_id}: '{callback_data}'")
                    process_callback(update["callback_query"])
                    
        except KeyboardInterrupt:
            print("\n🛑 Остановка бота...")
            break
        except Exception as e:
            if DEBUG_MODE:
                print(f"DEBUG: Ошибка в основном цикле: {e}")
                import traceback
                traceback.print_exc()
            time.sleep(5)  # Пауза при ошибке


def main():
    """Запуск бота"""
    # Установить обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Проверки перед запуском
        if not check_requirements():
            return
        
        # Запуск основного цикла
        main_loop()
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
    finally:
        print("👋 До свидания!")


if __name__ == '__main__':
    main()