import os
import asyncio
import traceback
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# === Инициализация Flask ===
# Мы создаем приложение Flask сразу, чтобы убедиться, что оно работает.
app = Flask(__name__)

# === Тестовый маршрут для проверки "здоровья" приложения ===
@app.route('/hello', methods=['GET'])
def hello():
    """Простая функция, чтобы проверить, что сервер вообще жив."""
    print("--- Запрос к /hello получен! ---")
    return "Hello, Vercel server is running!", 200


# === Основной вебхук для Telegram ===
@app.route('/', methods=['POST'])
def webhook():
    """Эта функция будет обрабатывать все запросы от Telegram."""
    print("--- Входящий POST-запрос в / ---")
    
    # Мы помещаем ВСЮ логику инициализации и обработки ВНУТРЬ try...except
    # Это наша лучшая попытка поймать ошибку, где бы она ни была.
    try:
        # --- Шаг 1: Инициализация клиентов внутри запроса ---
        print("Шаг 1: Загрузка переменных окружения.")
        BOT_TOKEN = os.environ.get('BOT_TOKEN')
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
        ADMIN_IDS_STR = os.environ.get('ADMIN_IDS', '')

        if not all([BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY, ADMIN_IDS_STR]):
            print("!!! КРИТИЧЕСКАЯ ОШИБКА: Одна или несколько переменных окружения не найдены!")
            return "Configuration error", 500

        print("Шаг 2: Создание клиентов Bot и Supabase.")
        bot = Bot(token=BOT_TOKEN)
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print(f"Шаг 3: Обработка строки ADMIN_IDS: '{ADMIN_IDS_STR}'")
        ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]
        print(f"Список админов: {ADMIN_IDS}")

        # --- Шаг 2: Обработка запроса от Telegram ---
        print("Шаг 4: Обработка данных от Telegram.")
        update_data = request.get_json()
        if not update_data:
            print("Ошибка: Тело запроса пустое.")
            return "ok", 200

        update = Update.de_json(update_data, bot)
        if not (update.message and update.message.text):
            print("Обновление не содержит текстового сообщения.")
            return "ok", 200

        # --- Шаг 3: Выполнение логики бота ---
        text = update.message.text
        user_id = update.message.chat_id
        print(f"Получено сообщение '{text}' от пользователя {user_id}")

        # Всю логику (сохранение, рассылка) нужно было бы перенести сюда,
        # но для начала давайте просто убедимся, что этот блок работает.

        # --- Сохранение пользователя ---
        print(f"Попытка сохранить пользователя {user_id} в Supabase.")
        supabase.table('users').upsert({'chat_id': user_id}, on_conflict='chat_id').execute()
        print(f"Пользователь {user_id} успешно сохранен/обновлен.")
        
        # --- Ответ пользователю ---
        if text == '/start':
            # Для простоты пока отправим простой ответ
            bot.send_message(chat_id=user_id, text="Бот работает! Ваш ID сохранен.")
        
        elif text.startswith('/') and user_id in ADMIN_IDS:
             bot.send_message(chat_id=user_id, text="Команда администратора получена.")

    except Exception as e:
        # Если что-то сломается на любом из шагов, мы увидим детальную ошибку
        print("--- !!! ПРОИЗОШЛА КРИТИЧЕСКАЯ ОШИБКА !!! ---")
        # Эта функция выведет ПОЛНУЮ информацию об ошибке в логи
        print(traceback.format_exc())
        
    return "ok", 200
