import os
import asyncio
import traceback
import json
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# === ГЛОБАЛЬНАЯ ОБЛАСТЬ: ТОЛЬКО САМОЕ ЛЕГКОЕ ===
# Здесь мы только создаем Flask-приложение. Больше ничего.
app = Flask(__name__)

# === Асинхронные функции-обработчики (без изменений) ===
# Они будут вызываться из вебхука
async def save_user_async(supabase_client, user_id: int):
    try:
        await asyncio.to_thread(supabase_client.table('users').upsert, {'chat_id': user_id}, on_conflict='chat_id')
        print(f"--- УСПЕХ: Пользователь {user_id} сохранен в Supabase. ---")
    except Exception as e:
        print(f"--- ОШИБКА в save_user_async: {e} ---")

async def handle_start_async(bot, supabase_client, update: Update):
    user_id = update.message.chat_id
    await save_user_async(supabase_client, user_id)
    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url="https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"))],
        [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url="https://baza-znaniy-app.vercel.app/"))],
        [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url="https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! 😊\n\nВаш аккаунт зарегистрирован для получения новостей.",
        reply_markup=reply_markup
    )

async def handle_admin_command_async(bot, update: Update):
    await update.message.reply_text("Команда администратора распознана и будет обработана.")
    # Здесь будет полная логика /stats и /broadcast


# === ГЛАВНЫЙ ВЕБХУК: ВСЯ РАБОТА ПРОИСХОДИТ ЗДЕСЬ ===
@app.route('/', methods=['POST'])
def webhook():
    print("\n--- 1. ВЕБХУК ВЫЗВАН ---")
    try:
        # === ШАГ А: ИНИЦИАЛИЗАЦИЯ ВНУТРИ ЗАПРОСА ===
        # Это происходит КАЖДЫЙ раз и решает проблему "холодного старта"
        BOT_TOKEN = os.environ['BOT_TOKEN']
        SUPABASE_URL = os.environ['SUPABASE_URL']
        SUPABASE_KEY = os.environ['SUPABASE_KEY']
        ADMIN_IDS_STR = os.environ.get('ADMIN_IDS', '')
        ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

        bot = Bot(token=BOT_TOKEN)
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("--- 2. КЛИЕНТЫ Bot и Supabase успешно созданы. ---")

        # === ШАГ Б: ОБРАБОТКА ЗАПРОСА ===
        update_data = request.get_json()
        print(f"--- 3. ПОЛУЧЕНЫ ДАННЫЕ: {json.dumps(update_data, indent=2)} ---")
        
        update = Update.de_json(update_data, bot)
        
        if not (update.message and update.message.text):
            print("--- 4. В обновлении нет текстового сообщения. Выход. ---")
            return "ok", 200

        print(f"--- 4. УСПЕХ: Есть сообщение '{update.message.text}' от {update.message.chat_id}. ---")
        
        # === ШАГ В: ВЫЗОВ ОБРАБОТЧИКА ===
        text = update.message.text
        if text == '/start':
            print("--- 5. ВЫЗЫВАЕМ ОБРАБОТЧИК /start ---")
            asyncio.run(handle_start_async(bot, supabase, update))
        elif text.startswith('/') and update.message.chat_id in ADMIN_IDS:
            print("--- 5. ВЫЗЫВАЕМ ОБРАБОТЧИК АДМИНА ---")
            # Позже здесь будет полная логика, сейчас просто ответ
            asyncio.run(handle_admin_command_async(bot, update))

    except KeyError as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА: Отсутствует переменная окружения: {e} !!! ---")
    except Exception as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА ВНУТРИ ВЕБХУКА !!! ---")
        print(traceback.format_exc())
            
    print("--- 6. ЗАВЕРШЕНИЕ РАБОТЫ ВЕБХУКА ---")
    return 'ok', 200
