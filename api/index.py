import os
import asyncio
import traceback
import json # Импортируем json для красивого вывода
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# === ИНИЦИАЛИЗАЦИЯ (вынесена наружу для стабильности) ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
ADMIN_IDS_STR = os.environ.get('ADMIN_IDS', '')
ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Асинхронные функции остаются без изменений
async def save_user_async(user_id: int):
    try:
        await asyncio.to_thread(supabase.table('users').upsert, {'chat_id': user_id}, on_conflict='chat_id')
        print(f"--- УСПЕХ: Пользователь {user_id} сохранен в Supabase. ---")
    except Exception as e:
        print(f"--- ОШИБКА в save_user_async: {e} ---")

async def handle_start_async(update: Update):
    user_id = update.message.chat_id
    await save_user_async(user_id)
    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url="https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"))],
        [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url="https://baza-znaniy-app.vercel.app/"))],
        [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url="https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! 😊\n\nБот работает, и ваш ID сохранен для рассылок.",
        reply_markup=reply_markup
    )

async def handle_admin_command_async(update: Update):
    # ... (эта функция остается без изменений)
    if update.message.chat_id not in ADMIN_IDS: return
    text_parts = update.message.text.split(' ', 1)
    command = text_parts[0]
    # ... и так далее


# === ГЛАВНЫЙ ВЕБХУК С МАКСИМАЛЬНЫМ ЛОГИРОВАНИЕМ ===
@app.route('/', methods=['POST'])
def webhook():
    print("--- 1. ВЕБХУК ВЫЗВАН ---")
    try:
        update_data = request.get_json(silent=True) # silent=True предотвращает сбой, если тело не JSON
        print(f"--- 2. ПОЛУЧЕНЫ ДАННЫЕ: {json.dumps(update_data, indent=2)} ---")

        if not update_data:
            print("--- 3. ПРОВАЛ: Данные пустые (update_data is None). Выход. ---")
            return "ok", 200

        print("--- 3. УСПЕХ: Данные есть. Десериализуем... ---")
        update = Update.de_json(update_data, bot)
        
        if not (update.message and update.message.text):
            print("--- 4. ПРОВАЛ: В обновлении нет текстового сообщения. Выход. ---")
            return "ok", 200

        print(f"--- 4. УСПЕХ: Есть сообщение '{update.message.text}' от {update.message.chat_id}. ---")
        
        text = update.message.text
        if text == '/start':
            print("--- 5. ВЫЗЫВАЕМ ОБРАБОТЧИК /start ---")
            asyncio.run(handle_start_async(update))
        elif text.startswith('/') and update.message.chat_id in ADMIN_IDS:
            print("--- 5. ВЫЗЫВАЕМ ОБРАБОТЧИК АДМИНА ---")
            # asyncio.run(handle_admin_command_async(update)) # Пока отключим для теста
            asyncio.run(update.message.reply_text("Команда админа распознана!"))


    except Exception as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА ВНУТРИ ВЕБХУКА !!! ---")
        print(traceback.format_exc())
            
    print("--- 6. ЗАВЕРШЕНИЕ РАБОТЫ ВЕБХУКА ---")
    return 'ok', 200
