#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с Telegram Bot API
"""

import json
import os
import requests
from datetime import datetime
from config import BASE_URL, BASE_FOLDER, TIMEOUT_SECONDS, LOG_FILE, DEBUG_MODE


def log_usage(user_id, action):
    """Логирование использования"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} - {user_id} - {action}\n")
    except:
        pass


def get_file_path(filename, category=None):
    """Получить путь к файлу"""
    from config import KNOWLEDGE_BASE
    
    if category and category in KNOWLEDGE_BASE:
        folder = KNOWLEDGE_BASE[category]["folder"]
        return os.path.join(BASE_FOLDER, folder, filename)
    return os.path.join(BASE_FOLDER, filename)


def send_message(chat_id, text, reply_markup=None):
    """Отправить текстовое сообщение"""
    try:
        if DEBUG_MODE:
            print(f"DEBUG: send_message вызван для chat_id={chat_id}")
            print(f"DEBUG: Текст сообщения: '{text[:100]}...'")
            print(f"DEBUG: Клавиатура: {'Есть' if reply_markup else 'Нет'}")
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
            if DEBUG_MODE:
                print(f"DEBUG: Добавлена клавиатура в payload")
            
        if DEBUG_MODE:
            print(f"DEBUG: Отправляем HTTP запрос к {BASE_URL}/sendMessage")
            
        response = requests.post(f"{BASE_URL}/sendMessage", data=payload, timeout=TIMEOUT_SECONDS)
        
        if DEBUG_MODE:
            print(f"DEBUG: HTTP ответ: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            if DEBUG_MODE:
                print(f"DEBUG: Telegram ответ: ok={response_data.get('ok')}")
                if not response_data.get('ok'):
                    print(f"DEBUG: ОШИБКА от Telegram: {response_data}")
            return response_data
        else:
            if DEBUG_MODE:
                print(f"DEBUG: HTTP ОШИБКА {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        if DEBUG_MODE:
            print(f"DEBUG: ИСКЛЮЧЕНИЕ в send_message: {e}")
            import traceback
            traceback.print_exc()
        return None


def send_document(chat_id, file_path, filename, caption=""):
    """Отправить PDF файл"""
    try:
        if DEBUG_MODE:
            print(f"DEBUG: send_document вызван для файла: {filename}")
            print(f"DEBUG: Путь к файлу: {file_path}")
            print(f"DEBUG: Существует ли файл: {os.path.exists(file_path)}")
            
        if not os.path.exists(file_path):
            if DEBUG_MODE:
                print(f"DEBUG: Файл не найден: {file_path}")
            send_message(chat_id, f"❌ Файл не найден: {filename}")
            return None
            
        with open(file_path, 'rb') as file:
            files = {'document': (filename, file, 'application/pdf')}
            data = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'HTML'  # Добавляем для поддержки HTML тегов в caption
            }
            
            if DEBUG_MODE:
                print(f"DEBUG: Отправляем файл размером {os.path.getsize(file_path)} байт")
                
            response = requests.post(f"{BASE_URL}/sendDocument", files=files, data=data, timeout=TIMEOUT_SECONDS)
            
            if DEBUG_MODE:
                print(f"DEBUG: Файл отправлен, статус: {response.status_code}")
                
            return response.json()
            
    except Exception as e:
        if DEBUG_MODE:
            print(f"DEBUG: Ошибка отправки файла: {e}")
        send_message(chat_id, f"❌ Ошибка отправки файла: {filename}")
        return None


def create_inline_keyboard(buttons):
    """Создать инлайн клавиатуру"""
    try:
        if DEBUG_MODE:
            print(f"DEBUG: create_inline_keyboard получил {len(buttons)} кнопок")
        
        keyboard = []
        for i, row in enumerate(buttons):
            keyboard_row = []
            for j, button in enumerate(row):
                if DEBUG_MODE:
                    print(f"DEBUG: Обрабатываем кнопку [{i}][{j}]: text='{button['text'][:30]}...', callback='{button['callback_data']}'")
                keyboard_row.append({
                    "text": button["text"],
                    "callback_data": button["callback_data"]
                })
            keyboard.append(keyboard_row)
        
        result = {"inline_keyboard": keyboard}
        if DEBUG_MODE:
            print(f"DEBUG: Создана клавиатура с {len(keyboard)} рядами")
        return result
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"DEBUG: ОШИБКА в create_inline_keyboard: {e}")
            import traceback
            traceback.print_exc()
        return {"inline_keyboard": []}


def get_updates(update_offset):
    """Получить обновления от Telegram"""
    try:
        payload = {
            "offset": update_offset,
            "timeout": 30,
            "allowed_updates": ["message", "callback_query"]
        }
        
        response = requests.post(f"{BASE_URL}/getUpdates", data=payload, timeout=35)
        
        if response.status_code == 200:
            data = response.json()
            if data["ok"]:
                return data["result"]
        
        return []
        
    except requests.exceptions.Timeout:
        # Таймаут - это нормально при long polling
        return []
    except Exception as e:
        if DEBUG_MODE:
            print(f"DEBUG: Ошибка получения обновлений: {e}")
        return []


def answer_callback_query(callback_id):
    """Ответить на callback query (убрать часики)"""
    try:
        response = requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": callback_id})
        if DEBUG_MODE:
            print(f"DEBUG: Answer callback response: {response.status_code}")
        return response
    except Exception as e:
        if DEBUG_MODE:
            print(f"DEBUG: Ошибка answerCallbackQuery: {e}")
        return None


def edit_message_text(chat_id, message_id, text, reply_markup=None):
    """Редактировать существующее сообщение"""
    try:
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
            
        response = requests.post(f"{BASE_URL}/editMessageText", data=payload)
        
        if DEBUG_MODE:
            print(f"DEBUG: Edit message response: {response.status_code}")
            
        return response
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"DEBUG: Ошибка editMessageText: {e}")
        return None


def check_bot_connection():
    """Проверить подключение к боту"""
    try:
        response = requests.get(f"{BASE_URL}/getMe", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["ok"]:
                bot_name = data["result"]["username"]
                print(f"✅ Бот @{bot_name} подключен успешно")
                return True
            else:
                print("❌ Неверный токен бота")
                return False
        else:
            print("❌ Не удается подключиться к Telegram API")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False