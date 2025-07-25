import os
import asyncio
import traceback
import sys # <-- ВАЖНЫЙ ИМПОРТ для принудительной записи логов
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# === Глобальная область: только создание Flask-приложения ===
app = Flask(__name__)

# --- НОВАЯ СИНХРОННАЯ ФУНКЦИЯ СОХРАНЕНИЯ ---
def save_user_sync(supabase_client, user_id: int):
    """СИНХРОННО сохраняет ID пользователя в базу данных."""
    try:
        # Принудительно выводим лог ДО операции
        print(f"--- [DB-SYNC] Попытка upsert для пользователя {user_id}. ---")
        sys.stdout.flush() 

        # Прямой СИНХРОННЫЙ вызов. Основной поток будет ждать здесь.
        supabase_client.table('users').upsert({'chat_id': user_id}, on_conflict='chat_id').execute()
        
        # Этот лог появится, только если строка выше успешно выполнится
        print(f"--- [DB-SYNC] УСПЕХ: Пользователь {user_id} сохранен. ---")
        sys.stdout.flush()
    except Exception as e:
        # Этот лог появится, если строка execute() выдаст ошибку
        print(f"--- [DB-SYNC] !!! ОШИБКА при сохранении {user_id}: {e} !!! ---")
        print(traceback.format_exc())
        sys.stdout.flush()

# --- Асинхронный обработчик, который вызывает синхронную функцию ---
async def handle_start_async(bot, supabase_client, update: Update):
    """Обрабатывает /start: сначала синхронная база, потом асинхронный ответ."""
    user_id = update.message.chat_id
    
    # Сначала вызываем блокирующую функцию сохранения
    save_user_sync(supabase_client, user_id)
    
    # Только после завершения работы с базой отправляем ответ
    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url="https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"))],
        [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url="https://baza-znaniy-app.vercel.app/"))],
        [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url="https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! 😊 (sync_final_test)", # Новое уникальное сообщение
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ... (handle_admin_command_async можно пока оставить пустым)
async def handle_admin_command_async(bot, update: Update):
    pass

# === ГЛАВНЫЙ ВЕБХУК ===
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
                asyncio.run(handle_admin_command_async(bot, update))

    except Exception as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ !!! ---")
        print(traceback.format_exc())
        sys.stdout.flush()
            
    return 'ok', 200
