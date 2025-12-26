#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработчики команд и callback для Telegram бота
"""

import os
from config import KNOWLEDGE_BASE, SPECIAL_FILES, SEARCH_KEYWORDS, DEBUG_MODE
from telegram_api import (
    log_usage, get_file_path, send_message, send_document, 
    create_inline_keyboard, edit_message_text, answer_callback_query
)


class PDFManager:
    """Управление PDF файлами"""
    def __init__(self, base_folder):
        self.base_folder = base_folder
        self.files_count = 0
        self._scan_files()
    
    def _scan_files(self):
        """Подсчет количества PDF файлов"""
        try:
            total_files = 0
            for category_info in KNOWLEDGE_BASE.values():
                total_files += len(category_info["files"])
            total_files += len(SPECIAL_FILES)  # Добавляем специальные файлы
            self.files_count = total_files
        except:
            self.files_count = 11  # Fallback значение
    
    def get_files_count(self):
        """Получить количество файлов"""
        return self.files_count


# Глобальный менеджер PDF для статистики
pdf_manager = PDFManager("pdf_files")


def handle_start(chat_id, user_name):
    """Обработать команду /start"""
    log_usage(chat_id, "start")
    
    text = f"""🛠️ <b>База знаний Homeline Токмак</b>

Привет, {user_name}!

<b>🚀 СУПЕР ПОИСК ПО 190+ СЛОВАМ!</b>

<b>🎯 АВТОПОИСК:</b>
Напиши <i>любое</i> слово - я найду инструкции:
• <b>онт, ону, модем, коробочка</b> → оборудование  
• <b>вайфай, роутер, беспроводная</b> → WiFi настройки
• <b>затухание, сигнал, дбм, -20</b> → диагностика
• <b>сварка, аппарат, скалыватель</b> → инструменты
• <b>частный, мкд, офис</b> → подключения

<b>📋 КОМАНДЫ:</b>
📚 /all - все категории инструкций
⚡ /quick - быстрый справочник  
📞 /contacts - контакты

<b>💡 Попробуй написать:</b> модемчик, вифи, или любое слово!"""
    
    send_message(chat_id, text)


def handle_search(chat_id, text, is_command=True):
    """Обработать поиск (команда /search или автопоиск)"""
    if is_command:
        # Это команда /search
        parts = text.split()
        if len(parts) < 2:
            help_text = """🔍 <b>Поиск:</b> /search [слово] или просто напиши слово

<b>🚀 Работает 190+ ключевых слов!</b>
• <b>Модемы:</b> онт, ону, модем, коробочка, устройство
• <b>WiFi:</b> вайфай, роутер, беспроводная, пароль
• <b>Диагностика:</b> затухание, сигнал, дбм, -20, не работает
• <b>Инструменты:</b> сварка, аппарат, скалыватель, стриппер  
• <b>Подключения:</b> частный, дом, мкд, квартира, офис

<b>Примеры:</b>
/search модемчик
или просто: <b>вифи</b>"""
            send_message(chat_id, help_text)
            return
            
        keyword = " ".join(parts[1:]).lower()
    else:
        # Это автопоиск - весь текст как ключевое слово
        keyword = text.lower()
    
    log_usage(chat_id, f"search_{keyword}")
    
    if DEBUG_MODE:
        print(f"DEBUG: Поиск по ключевому слову: '{keyword}'")
    
    # Поиск файлов
    found_files = []
    for key, files in SEARCH_KEYWORDS.items():
        if key in keyword:
            if DEBUG_MODE:
                print(f"DEBUG: Найдено совпадение с ключом '{key}': {files}")
            found_files.extend(files)
    
    if DEBUG_MODE:
        print(f"DEBUG: Всего найдено файлов: {len(found_files)} - {found_files}")
    
    if not found_files:
        # При автопоиске показываем подсказку
        if not is_command:
            help_text = f"""🔍 <b>Ничего не найдено по запросу:</b> '{keyword}'

<b>💡 Попробуй популярные слова:</b>
• <b>Модемы:</b> онт, ону, модем, коробочка, устройство
• <b>WiFi:</b> вайфай, роутер, беспроводная, пароль, сеть
• <b>Диагностика:</b> затухание, сигнал, дбм, -20, не работает
• <b>Сварка:</b> аппарат, скалыватель, стриппер, соединение
• <b>Подключения:</b> частный, дом, мкд, квартира, офис

<b>🔍 Всего работает 190+ слов!</b>
Или используй /all для просмотра всех категорий"""
            send_message(chat_id, help_text)
        else:
            send_message(chat_id, f"❌ Не найдено по запросу: {keyword}")
        return
    
    # Создать кнопки
    if DEBUG_MODE:
        print(f"DEBUG: Начинаем создание кнопок для {len(set(found_files))} файлов")
        
    buttons = []
    
    for i, filename in enumerate(set(found_files)):
        if DEBUG_MODE:
            print(f"DEBUG: Обрабатываем файл {i}: '{filename}'")
        
        # Найти категорию и описание файла
        category = None
        description = filename[:30] + "..."
        
        for cat_key, cat_info in KNOWLEDGE_BASE.items():
            if filename in cat_info["files"]:
                category = cat_key
                description = cat_info["files"][filename]
                if DEBUG_MODE:
                    print(f"DEBUG: Найдена категория '{category}' для файла '{filename}'")
                break
        
        # Если категория не найдена, ищем в специальных файлах
        if category is None:
            if DEBUG_MODE:
                print(f"DEBUG: Категория не найдена, ищем в специальных файлах")
            for special_key, special_filename in SPECIAL_FILES.items():
                if filename == special_filename:
                    category = "special"
                    if DEBUG_MODE:
                        print(f"DEBUG: Найден специальный файл: {special_key}")
                    break
        
        # Если категория так и не найдена - ставим default
        if category is None:
            if DEBUG_MODE:
                print(f"DEBUG: ВНИМАНИЕ! Категория не найдена для файла '{filename}', ставим 'unknown'")
            category = "unknown"
        
        # Создаем безопасный callback_data БЕЗ эмодзи, кириллицы и спецсимволов
        try:
            # Убираем ВСЕ небезопасные символы для Telegram callback_data
            import re
            # Оставляем только латиницу, цифры и подчеркивания
            safe_filename = re.sub(r'[^a-zA-Z0-9_]', '', 
                                 filename.replace('ДИАГНОСТИКА', 'DIAGNOSTIKA')
                                        .replace('ЗАТУХАНИЯ', 'ZATUHANIYA') 
                                        .replace('НАСТРОЙКА', 'NASTROYKA')
                                        .replace('РОУТЕРОВ', 'ROUTEROV')
                                        .replace('Базовая', 'Bazovaya')
                                        .replace('ГИБРИДЫ', 'GIBRIDY')
                                        .replace('ПОДКЛЮЧЕНИЕ', 'PODKLYUCHENIE')
                                        .replace('ЧАСТНОМ', 'CHASTNOM')
                                        .replace('СЕКТОРЕ', 'SEKTORE')
                                        .replace('КОММЕРЧЕСКИХ', 'KOMMERCHESKIH')
                                        .replace('ОБЪЕКТОВ', 'OBYEKTOV')
                                        .replace('ДЕМОНСТРАЦИЯ', 'DEMONSTRATSIYA')
                                        .replace('УСЛУГ', 'USLUG')
                                        .replace('КЛИЕНТУ', 'KLIENTU')
                                        .replace('ПРОСТЫЕ', 'PROSTYE')
                                        .replace('СВАРОЧНЫЕ', 'SVAROCHNYE')
                                        .replace('АППАРАТЫ', 'APPARATY')
                                        .replace('ИЗМЕРИТЕЛИ', 'IZMERITELI')
                                        .replace('ОПТИЧЕСКОЙ', 'OPTICHESKOY')
                                        .replace('МОЩНОСТИ', 'MOSHCHNOSTI')
                                        .replace('СКАЛЫВАТЕЛЯ', 'SKALYVATELEY')
                                        .replace('СТРИППЕРА', 'STRIPPERA')
                                        .replace(' ', '')
                                        .replace('.', '')
                                        .replace('(', '')
                                        .replace(')', '')
                                        .replace('-', '')
                                        .replace('№', 'N'))
            
            # Ограничиваем длину (Telegram лимит 64 символа)
            if len(safe_filename) > 50:
                safe_filename = safe_filename[:50]
                
            callback_data = f"search_{category}_{i}_{safe_filename}"
            
            if DEBUG_MODE:
                print(f"DEBUG: Создан безопасный callback_data: '{callback_data}'")
            
            buttons.append([{"text": description, "callback_data": callback_data}])
            if DEBUG_MODE:
                print(f"DEBUG: Кнопка добавлена: '{description}'")
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"DEBUG: ОШИБКА при создании кнопки для '{filename}': {e}")
            continue
    
    if DEBUG_MODE:
        print(f"DEBUG: Создано {len(buttons)} кнопок")
    
    if len(buttons) == 0:
        if DEBUG_MODE:
            print("DEBUG: ПРОБЛЕМА! Кнопки не созданы")
        send_message(chat_id, f"❌ Ошибка создания кнопок для найденных файлов")
        return
    
    if DEBUG_MODE:
        print(f"DEBUG: Создаем клавиатуру...")
        
    keyboard = create_inline_keyboard(buttons)
    
    # Разный текст для команды и автопоиска
    if is_command:
        result_text = f"🔍 <b>Найдено {len(set(found_files))} файлов:</b>"
    else:
        result_text = f"🎯 <b>Автопоиск по '{keyword}':</b>\nНайдено {len(set(found_files))} файлов:"
    
    if DEBUG_MODE:
        print(f"DEBUG: Отправляем сообщение с {len(buttons)} кнопками...")
        
    send_message(chat_id, result_text, keyboard)


def handle_all(chat_id):
    """Показать все инструкции"""
    log_usage(chat_id, "all")
    
    buttons = [
        [{"text": "1️⃣ КРИТИЧЕСКИЕ", "callback_data": "cat_critical"}],
        [{"text": "2️⃣ ПОДКЛЮЧЕНИЯ", "callback_data": "cat_connections"}], 
        [{"text": "3️⃣ ОБОРУДОВАНИЕ", "callback_data": "cat_equipment"}],
        [{"text": "⚡ Быстрый справочник", "callback_data": "special_quick"}]
    ]
    
    keyboard = create_inline_keyboard(buttons)
    text = """📚 <b>Все инструкции Homeline:</b>

<b>11 PDF файлов</b> в 3 категориях:

1️⃣ <b>КРИТИЧЕСКИЕ</b> - диагностика, настройки
2️⃣ <b>ПОДКЛЮЧЕНИЯ</b> - частный сектор, МКД  
3️⃣ <b>ОБОРУДОВАНИЕ</b> - ONT, гибриды, инструменты

Выбери категорию:"""
    
    send_message(chat_id, text, keyboard)


def handle_quick(chat_id):
    """Отправить быстрый справочник"""
    log_usage(chat_id, "quick")
    
    file_path = get_file_path(SPECIAL_FILES["quick"])
    caption = "⚡ <b>Быстрый справочник</b>"
    send_document(chat_id, file_path, SPECIAL_FILES["quick"], caption)


def handle_contacts(chat_id):
    """Показать контакты"""
    text = """📞 <b>КОНТАКТЫ HOMELINE ТОКМАК</b>

🔧 <b>Руководитель:</b> 0700111865
📞 <b>Офис:</b> 0700888211  
🆘 <b>Техподдержка:</b> 0554387803

⏰ <b>Режим работы:</b>
Пн-Пт: 8:00-17:00

💡 <i>Сначала проверь базу знаний!</i>"""
    
    send_message(chat_id, text)


def handle_callback(chat_id, callback_data, message_id):
    """Обработать нажатие кнопки"""
    try:
        if DEBUG_MODE:
            print(f"DEBUG: Получен callback: {callback_data}")
        
        if callback_data.startswith("search_"):
            # Обработка callback из автопоиска
            parts = callback_data.split("_")
            if len(parts) >= 4:
                category = parts[1]
                safe_filename = "_".join(parts[3:])  # Объединяем обратно если было несколько _
                
                if DEBUG_MODE:
                    print(f"DEBUG: Поиск файла по safe_filename: '{safe_filename}' в категории '{category}'")
                
                # ИСПРАВЛЕНИЕ: Ищем файл по безопасному имени напрямую
                found_filename = None
                
                # Проходим по всем файлам из поисковых ключевых слов
                for filename in [f for files in SEARCH_KEYWORDS.values() for f in files]:
                    # Создаем безопасное имя для сравнения (такое же как при создании кнопки)
                    import re
                    test_safe = re.sub(r'[^a-zA-Z0-9_]', '', 
                                     filename.replace('ДИАГНОСТИКА', 'DIAGNOSTIKA')
                                            .replace('ЗАТУХАНИЯ', 'ZATUHANIYA')
                                            .replace('НАСТРОЙКА', 'NASTROYKA')
                                            .replace('РОУТЕРОВ', 'ROUTEROV')
                                            .replace('Базовая', 'Bazovaya')
                                            .replace('ГИБРИДЫ', 'GIBRIDY')
                                            .replace('ПОДКЛЮЧЕНИЕ', 'PODKLYUCHENIE')
                                            .replace('ЧАСТНОМ', 'CHASTNOM')
                                            .replace('СЕКТОРЕ', 'SEKTORE')
                                            .replace('КОММЕРЧЕСКИХ', 'KOMMERCHESKIH')
                                            .replace('ОБЪЕКТОВ', 'OBYEKTOV')
                                            .replace('ДЕМОНСТРАЦИЯ', 'DEMONSTRATSIYA')
                                            .replace('УСЛУГ', 'USLUG')
                                            .replace('КЛИЕНТУ', 'KLIENTU')
                                            .replace('ПРОСТЫЕ', 'PROSTYE')
                                            .replace('СВАРОЧНЫЕ', 'SVAROCHNYE')
                                            .replace('АППАРАТЫ', 'APPARATY')
                                            .replace('ИЗМЕРИТЕЛИ', 'IZMERITELI')
                                            .replace('ОПТИЧЕСКОЙ', 'OPTICHESKOY')
                                            .replace('МОЩНОСТИ', 'MOSHCHNOSTI')
                                            .replace('СКАЛЫВАТЕЛЯ', 'SKALYVATELEY')
                                            .replace('СТРИППЕРА', 'STRIPPERA')
                                            .replace(' ', '')
                                            .replace('.', '')
                                            .replace('(', '')
                                            .replace(')', '')
                                            .replace('-', '')
                                            .replace('№', 'N'))
                    
                    # Ограничиваем длину также как при создании кнопки
                    if len(test_safe) > 50:
                        test_safe = test_safe[:50]
                    
                    if DEBUG_MODE:
                        print(f"DEBUG: Сравнение: '{test_safe}' == '{safe_filename}' ?")
                    
                    if test_safe == safe_filename:
                        found_filename = filename
                        if DEBUG_MODE:
                            print(f"DEBUG: НАЙДЕН файл по безопасному имени: '{found_filename}'")
                        break
                
                if found_filename:
                    # Найти правильную категорию для этого файла
                    correct_category = None
                    for cat_key, cat_info in KNOWLEDGE_BASE.items():
                        if found_filename in cat_info["files"]:
                            correct_category = cat_key
                            if DEBUG_MODE:
                                print(f"DEBUG: Файл '{found_filename}' принадлежит категории '{correct_category}'")
                            break
                    
                    # Если не найден в основных категориях, ищем в специальных
                    if correct_category is None:
                        for special_key, special_filename in SPECIAL_FILES.items():
                            if found_filename == special_filename:
                                correct_category = "special"
                                if DEBUG_MODE:
                                    print(f"DEBUG: Найден специальный файл: {special_key}")
                                break
                    
                    # Отправляем файл
                    if correct_category == "special":
                        file_path = get_file_path(found_filename)
                        caption = f"📄 <b>{found_filename}</b>"
                        send_document(chat_id, file_path, found_filename, caption)
                    else:
                        description = KNOWLEDGE_BASE[correct_category]["files"].get(found_filename, found_filename)
                        file_path = get_file_path(found_filename, correct_category)
                        caption = f"📄 <b>{description}</b>"
                        send_document(chat_id, file_path, found_filename, caption)
                    return
                else:
                    if DEBUG_MODE:
                        print(f"DEBUG: ОШИБКА - файл не найден по safe_filename: '{safe_filename}'")
                    send_message(chat_id, f"❌ Файл не найден. Обратитесь к администратору.")
                    return
                
        elif callback_data.startswith("cat_"):
            # Показать категорию
            category = callback_data.replace("cat_", "")
            if DEBUG_MODE:
                print(f"DEBUG: Открываем категорию: {category}")
            
            if category in KNOWLEDGE_BASE:
                cat_info = KNOWLEDGE_BASE[category]
                buttons = []
                
                for i, (filename, desc) in enumerate(cat_info["files"].items()):
                    # Создаем безопасный callback БЕЗ эмодзи и кириллицы
                    import re
                    safe_filename = re.sub(r'[^a-zA-Z0-9_]', '', 
                                         filename.replace('ДИАГНОСТИКА', 'DIAGNOSTIKA')
                                                .replace('ЗАТУХАНИЯ', 'ZATUHANIYA')
                                                .replace('НАСТРОЙКА', 'NASTROYKA')
                                                .replace('РОУТЕРОВ', 'ROUTEROV')
                                                .replace('Базовая', 'Bazovaya')
                                                .replace('ГИБРИДЫ', 'GIBRIDY')
                                                .replace('ПОДКЛЮЧЕНИЕ', 'PODKLYUCHENIE')
                                                .replace('ЧАСТНОМ', 'CHASTNOM')
                                                .replace('СЕКТОРЕ', 'SEKTORE')
                                                .replace('КОММЕРЧЕСКИХ', 'KOMMERCHESKIH')
                                                .replace('ОБЪЕКТОВ', 'OBYEKTOV')
                                                .replace('ДЕМОНСТРАЦИЯ', 'DEMONSTRATSIYA')
                                                .replace('УСЛУГ', 'USLUG')
                                                .replace('КЛИЕНТУ', 'KLIENTU')
                                                .replace('ПРОСТЫЕ', 'PROSTYE')
                                                .replace('СВАРОЧНЫЕ', 'SVAROCHNYE')
                                                .replace('АППАРАТЫ', 'APPARATY')
                                                .replace('ИЗМЕРИТЕЛИ', 'IZMERITELI')
                                                .replace('ОПТИЧЕСКОЙ', 'OPTICHESKOY')
                                                .replace('МОЩНОСТИ', 'MOSHCHNOSTI')
                                                .replace('СКАЛЫВАТЕЛЯ', 'SKALYVATELEY')
                                                .replace('СТРИППЕРА', 'STRIPPERA'))[:50]
                    
                    buttons.append([{"text": desc, "callback_data": f"file_{category}_{i}_{safe_filename}"}])
                
                buttons.append([{"text": "⬅️ Назад", "callback_data": "back"}])
                keyboard = create_inline_keyboard(buttons)
                
                # Обновить сообщение
                edit_text = f"<b>{cat_info['name']}</b>\n\nВыбери PDF:"
                edit_message_text(chat_id, message_id, edit_text, keyboard)
                
        elif callback_data.startswith("file_"):
            # Отправить файл из категории
            parts = callback_data.split("_")
            if len(parts) >= 4:
                category = parts[1] 
                safe_filename = "_".join(parts[3:])  # Объединяем обратно
                
                if DEBUG_MODE:
                    print(f"DEBUG: Ищем файл {safe_filename} в категории {category}")
                
                if category in KNOWLEDGE_BASE:
                    # Найти оригинальный filename по индексу (более надежно)
                    try:
                        file_index = int(parts[2])  # Индекс из callback_data
                        filenames = list(KNOWLEDGE_BASE[category]["files"].keys())
                        
                        if file_index < len(filenames):
                            filename = filenames[file_index]
                            description = KNOWLEDGE_BASE[category]["files"][filename]
                            file_path = get_file_path(filename, category)
                            caption = f"📄 <b>{description}</b>"
                            send_document(chat_id, file_path, filename, caption)
                            return
                    except (ValueError, IndexError) as e:
                        if DEBUG_MODE:
                            print(f"DEBUG: Ошибка получения файла по индексу: {e}")
                    
                    # Fallback - поиск по безопасному имени (для совместимости)
                    for filename in KNOWLEDGE_BASE[category]["files"]:
                        import re
                        test_safe = re.sub(r'[^a-zA-Z0-9_]', '', 
                                         filename.replace('ДИАГНОСТИКА', 'DIAGNOSTIKA')
                                                .replace('ЗАТУХАНИЯ', 'ZATUHANIYA')
                                                .replace('НАСТРОЙКА', 'NASTROYKA')
                                                .replace('РОУТЕРОВ', 'ROUTEROV')
                                                .replace('Базовая', 'Bazovaya')
                                                .replace('ГИБРИДЫ', 'GIBRIDY')
                                                .replace('ПОДКЛЮЧЕНИЕ', 'PODKLYUCHENIE')
                                                .replace('ЧАСТНОМ', 'CHASTNOM')
                                                .replace('СЕКТОРЕ', 'SEKTORE')
                                                .replace('КОММЕРЧЕСКИХ', 'KOMMERCHESKIH')
                                                .replace('ОБЪЕКТОВ', 'OBYEKTOV')
                                                .replace('ДЕМОНСТРАЦИЯ', 'DEMONSTRATSIYA')
                                                .replace('УСЛУГ', 'USLUG')
                                                .replace('КЛИЕНТУ', 'KLIENTU')
                                                .replace('ПРОСТЫЕ', 'PROSTYE')
                                                .replace('СВАРОЧНЫЕ', 'SVAROCHNYE')
                                                .replace('АППАРАТЫ', 'APPARATY')
                                                .replace('ИЗМЕРИТЕЛИ', 'IZMERITELI')
                                                .replace('ОПТИЧЕСКОЙ', 'OPTICHESKOY')
                                                .replace('МОЩНОСТИ', 'MOSHCHNOSTI')
                                                .replace('СКАЛЫВАТЕЛЯ', 'SKALYVATELEY')
                                                .replace('СТРИППЕРА', 'STRIPPERA'))[:50]
                                          
                        if test_safe == safe_filename:
                            description = KNOWLEDGE_BASE[category]["files"][filename]
                            file_path = get_file_path(filename, category)
                            caption = f"📄 <b>{description}</b>"
                            send_document(chat_id, file_path, filename, caption)
                            return
                            
        elif callback_data.startswith("special_"):
            # Специальные файлы
            file_type = callback_data.replace("special_", "")
            if DEBUG_MODE:
                print(f"DEBUG: Специальный файл: {file_type}")
            
            if file_type in SPECIAL_FILES:
                filename = SPECIAL_FILES[file_type]
                file_path = get_file_path(filename)
                caption = f"📄 <b>{file_type.upper()}</b>"
                send_document(chat_id, file_path, filename, caption)
                
        elif callback_data == "back":
            # Вернуться к главному меню - редактируем сообщение
            if DEBUG_MODE:
                print("DEBUG: Возврат в главное меню")
            
            buttons = [
                [{"text": "1️⃣ КРИТИЧЕСКИЕ", "callback_data": "cat_critical"}],
                [{"text": "2️⃣ ПОДКЛЮЧЕНИЯ", "callback_data": "cat_connections"}], 
                [{"text": "3️⃣ ОБОРУДОВАНИЕ", "callback_data": "cat_equipment"}],
                [{"text": "⚡ Быстрый справочник", "callback_data": "special_quick"}]
            ]
            
            keyboard = create_inline_keyboard(buttons)
            text = """📚 <b>Все инструкции Homeline:</b>

<b>11 PDF файлов</b> в 3 категориях:

1️⃣ <b>КРИТИЧЕСКИЕ</b> - диагностика, настройки
2️⃣ <b>ПОДКЛЮЧЕНИЯ</b> - частный сектор, МКД  
3️⃣ <b>ОБОРУДОВАНИЕ</b> - ONT, гибриды, инструменты

Выбери категорию:"""
            
            edit_message_text(chat_id, message_id, text, keyboard)
            
    except Exception as e:
        if DEBUG_MODE:
            print(f"Ошибка callback: {e}")
            import traceback
            traceback.print_exc()


def process_message(message):
    """Обработать входящее сообщение"""
    try:
        chat_id = message["chat"]["id"]
        user_name = message["from"].get("first_name", "Пользователь")
        
        if "text" in message:
            text = message["text"].strip()
            
            # Обработка команд (начинаются с /)
            if text.startswith("/"):
                if text == "/start":
                    handle_start(chat_id, user_name)
                elif text.startswith("/search"):
                    handle_search(chat_id, text, is_command=True)
                elif text == "/all":
                    handle_all(chat_id)
                elif text == "/quick":
                    handle_quick(chat_id)
                elif text == "/contacts":
                    handle_contacts(chat_id)
                else:
                    # Неизвестная команда
                    help_text = """❓ <b>Неизвестная команда</b>

<b>Доступные команды:</b>
🔍 /search [слово] - поиск PDF
📚 /all - все инструкции  
⚡ /quick - быстрый справочник
📞 /contacts - контакты

<b>💡 Можно просто писать слова без команд:</b>
затухание, wifi, ont, сварка, мкд"""
                    send_message(chat_id, help_text)
            
            # АВТОПОИСК - обычный текст (не команда)
            else:
                # Игнорируем слишком короткие сообщения (менее 3 символов)
                if len(text) < 3:
                    help_text = """💡 <b>Автопоиск активен!</b>

Просто напиши слово для поиска инструкций:
• <b>затухание</b> - диагностика GPON
• <b>wifi</b> - настройка роутеров  
• <b>ont</b> - оборудование
• <b>сварка</b> - качество соединений

Или используй команды: /all /quick /contacts"""
                    send_message(chat_id, help_text)
                    return
                
                # Автопоиск по тексту
                if DEBUG_MODE:
                    print(f"DEBUG: Автопоиск активирован для: '{text}'")
                log_usage(chat_id, f"autosearch_{text}")
                handle_search(chat_id, text, is_command=False)
                
    except Exception as e:
        if DEBUG_MODE:
            print(f"Ошибка обработки сообщения: {e}")
            import traceback
            traceback.print_exc()


def process_callback(callback_query):
    """Обработать callback от кнопки"""
    try:
        chat_id = callback_query["message"]["chat"]["id"]
        message_id = callback_query["message"]["message_id"]
        callback_data = callback_query["data"]
        
        if DEBUG_MODE:
            print(f"DEBUG: Получен callback_query: {callback_data}")
        
        # Ответить на callback (убрать "часики")
        callback_id = callback_query["id"]
        answer_callback_query(callback_id)
        
        handle_callback(chat_id, callback_data, message_id)
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"Ошибка callback: {e}")
            import traceback
            traceback.print_exc()
