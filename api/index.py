import os
import asyncio
import traceback
import sys
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# === Глобальная область: только создание Flask-приложения ===
app = Flask(__name__)

# === Асинхронные функции-обработчики ===

async def save_user_async(supabase_client, user_id: int):
    """Сохраняет ID пользователя в базу данных (упрощенная версия для теста)."""
    try:
        print(f"--- [DB] Попытка INSERT для пользователя {user_id}. ---")
        sys.stdout.flush() # Принудительная запись лога

        # Используем простой INSERT. Если пользователь уже есть, будет ошибка, которую мы поймаем.
        await asyncio.to_thread(supabase_client.table('users').insert, {'chat_id': user_id})
        
        print(f"--- [DB] УСПЕХ: Пользователь {user_id} вставлен в базу. ---")
        sys.stdout.flush()
    except Exception as e:
        # Проверяем, не является ли ошибка ошибкой дубликата (это нормально)
        if 'duplicate key value violates unique constraint' in str(e):
            print(f"--- [DB] ИНФО: Пользователь {user_id} уже существует в базе. ---")
        else:
            # Логируем любую другую, настоящую ошибку
            print(f"--- [DB] !!! ОШИБКА при INSERT для пользователя {user_id}: {e} !!! ---")
            print(traceback.format_exc())
        sys.stdout.flush()

async def handle_start_async(bot, supabase_client, update: Update):
    """Обрабатывает команду /start с измененным порядком операций."""
    user_id = update.message.chat_id
    print(f"--- [HANDLER] Начало обработки /start для {user_id}. ---")
    sys.stdout.flush()

    # --- ШАГ 1: СНАЧАЛА СОХРАНЯЕМ В БАЗУ ---
    # Мы не пойдем дальше, пока эта строка не завершится.
    await save_user_async(supabase_client, user_id)
    
    print(f"--- [HANDLER] Сохранение в базу для {user_id} завершено. Отправляем ответ... ---")
    sys.stdout.flush()

    # --- ШАГ 2: ПОТОМ ОТПРАВЛЯЕМ ОТВЕТ ---
    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url="https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"))],
        [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url="https://baza-znaniy-app.vercel.app/"))],
        [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url="https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Привет! 😊 (db_first_test)",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    print(f"--- [HANDLER] Ответ для {user_id} отправлен. ---")
    sys.stdout.flush()

# ... (остальной код, включая handle_admin_command_async и webhook, остается прежним)
async def handle_admin_command_async(bot, supabase_client, update: Update):
    # ...
    pass

@app.route('/', methods=['POST'])
def webhook():
    try:
        BOT_TOKEN = os.environ['BOT_TOKEN']
        SUPABASE_URL = os.environ['SUPABASE_URL']
        SUPABASE_KEY = os.environ['SUPABASE_KEY']
        ADMIN_IDS_STR = os.environ.get('ADMIN_IDS', '')
        ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

        bot = Bot(token=BOT_TOKEN)
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        update_data = request.get_json()
        update = Update.de_json(update_data, bot)
        
        if update.message and update.message.text:
            text = update.message.text
            user_id = update.message.chat_id
            
            if text == '/start':
                asyncio.run(handle_start_async(bot, supabase, update))
            elif text.startswith('/') and user_id in ADMIN_IDS:
                # Временно отключим для чистоты теста
                pass

    except Exception as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ !!! ---")
        print(traceback.format_exc())
            
    return 'ok', 200
