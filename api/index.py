import os
import asyncio
import traceback
import sys
from flask import Flask, request
from telegram import Update, Bot
from supabase import create_client, Client

# === Глобальная область: только создание Flask-приложения ===
app = Flask(__name__)


# === Асинхронные функции-обработчики ===
async def save_user_async(supabase_client, user_id: int):
    """Асинхронно сохраняет ID пользователя."""
    try:
        print(f"--- [DB] Попытка upsert для пользователя {user_id}. ---")
        sys.stdout.flush()
        await asyncio.to_thread(supabase_client.table('users').upsert, {'chat_id': user_id}, on_conflict='chat_id')
        print(f"--- [DB] УСПЕХ: Пользователь {user_id} сохранен. ---")
        sys.stdout.flush()
    except Exception as e:
        print(f"--- [DB] !!! ОШИБКА при сохранении {user_id}: {e} !!! ---")
        print(traceback.format_exc())
        sys.stdout.flush()

async def handle_start_async(bot, supabase_client, update: Update):
    """Обрабатывает /start: сначала база, потом ответ."""
    user_id = update.message.chat_id
    
    # --- ШАГ 1: СНАЧАЛА СОХРАНЯЕМ В БАЗУ ---
    await save_user_async(supabase_client, user_id)
    
    # --- ШАГ 2: ПОТОМ ОТПРАВЛЯЕМ ОТВЕТ ---
    await bot.send_message(
        chat_id=user_id,
        text="Тест Базы Данных: v_db_minimal" # Новое уникальное сообщение
    )
    print(f"--- УСПЕХ: Ответ 'v_db_minimal' для {user_id} отправлен. ---")


# === ГЛАВНЫЙ ВЕБХУК ===
@app.route('/', methods=['POST'])
def webhook():
    """Принимает запрос и выполняет минимальную логику."""
    try:
        BOT_TOKEN = os.environ['BOT_TOKEN']
        SUPABASE_URL = os.environ['SUPABASE_URL']
        SUPABASE_KEY = os.environ['SUPABASE_KEY']

        bot = Bot(token=BOT_TOKEN)
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        update_data = request.get_json()
        update = Update.de_json(update_data, bot)
        
        if update.message and update.message.text == '/start':
            asyncio.run(handle_start_async(bot, supabase, update))

    except Exception as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ !!! ---")
        print(traceback.format_exc())
            
    return 'ok', 200
