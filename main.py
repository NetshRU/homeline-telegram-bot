#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram бот базы знаний Homeline с веб-сервером для Render.com
"""

import logging
import time
import os
from threading import Thread
from flask import Flask

# Импорт модулей бота
from config import TOKEN, BASE_FOLDER, DEBUG_MODE, IS_PRODUCTION
from handlers import MessageHandler

# Попытка импортировать правильный класс из telegram_api
try:
    from telegram_api import TelegramAPI
    API_CLASS = TelegramAPI
    logger_msg = "Импортирован TelegramAPI"
except ImportError:
    try:
        from telegram_api import TelegramBot
        API_CLASS = TelegramBot
        logger_msg = "Импортирован TelegramBot"
    except ImportError:
        try:
            from telegram_api import Bot
            API_CLASS = Bot
            logger_msg = "Импортирован Bot"
        except ImportError:
            try:
                from telegram_api import TelegramClient
                API_CLASS = TelegramClient
                logger_msg = "Импортирован TelegramClient"
            except ImportError as e:
                raise ImportError(f"Не удалось импортировать класс из telegram_api: {e}")

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask веб-сервер для health check
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Homeline Telegram Bot работает!"

@app.route('/health')
def health():
    return {"status": "ok", "bot": "running"}

@app.route('/stats')
def stats():
    try:
        # Получаем статистику от бота
        stats_data = {
            "status": "running",
            "base_folder": BASE_FOLDER,
            "debug_mode": DEBUG_MODE,
            "is_production": IS_PRODUCTION,
            "files_loaded": handler.pdf_manager.get_files_count() if 'handler' in globals() else 0,
            "api_class": API_CLASS.__name__
        }
        return stats_data
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_flask():
    """Запуск Flask сервера в отдельном потоке"""
    port = int(os.environ.get('PORT', 10000))  # Render использует переменную PORT
    app.run(host='0.0.0.0', port=port, debug=False)

def run_telegram_bot():
    """Запуск Telegram бота"""
    global handler
    
    try:
        logger.info("Запуск Telegram бота...")
        logger.info(f"📥 {logger_msg}")
        
        # Инициализация API с правильным классом
        api = API_CLASS(TOKEN)
        
        # Инициализация обработчика сообщений
        handler = MessageHandler(api, BASE_FOLDER)
        
        # Проверка подключения к Telegram
        bot_info = api.get_me()
        if not bot_info:
            raise Exception("Не удалось получить информацию о боте")
        
        logger.info(f"✅ Бот запущен: @{bot_info.get('username', 'unknown')}")
        logger.info(f"📂 Базовая папка: {BASE_FOLDER}")
        logger.info(f"🔍 Файлов загружено: {handler.pdf_manager.get_files_count()}")
        logger.info(f"🚀 Супер поиск активирован!")
        
        # Основной цикл получения обновлений
        offset = 0
        timeout = 30
        
        logger.info("🔄 Начинаю получение сообщений...")
        
        while True:
            try:
                updates = api.get_updates(offset=offset, timeout=timeout)
                
                if updates:
                    for update in updates:
                        # Обработка обновления
                        handler.handle_update(update)
                        
                        # Обновляем offset для следующего запроса
                        offset = max(offset, update.get('update_id', 0) + 1)
                
                # Небольшая пауза между запросами
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки...")
                break
                
            except Exception as e:
                logger.error(f"Ошибка в главном цикле: {e}")
                # При ошибке ждем 5 секунд и продолжаем
                time.sleep(5)
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

def main():
    """Главная функция - запуск веб-сервера и Telegram бота"""
    logger.info("🚀 Запуск Homeline Telegram Bot...")
    
    try:
        # Запуск Flask сервера в отдельном потоке
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info(f"🌐 Веб-сервер запущен на порту {os.environ.get('PORT', 10000)}")
        
        # Даем время серверу запуститься
        time.sleep(2)
        
        # Запуск Telegram бота в главном потоке
        run_telegram_bot()
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при запуске: {e}")
        raise

if __name__ == "__main__":
    main()
