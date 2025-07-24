import os
import asyncio
import traceback
import json # Импортируем json для красивого вывода
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# === Глобальная инициализация, чтобы убедиться, что переменные читаются на старте ===
# Этот блок выполняется один раз при "прогреве" сервера Vercel
print("--- [СТАРТ] Загрузка модуля api/index.py ---")
try:
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    ADMIN_IDS_STR = os.environ.get('ADMIN_IDS', '')
    
    if not all([BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY, ADMIN_IDS_STR]):
        print("--- [СТАРТ] ВНИМАНИЕ: Одна или несколько переменных окружения отсутствуют при первоначальной загрузке! ---")

    ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

    bot = Bot(token=BOT_TOKEN)
    app = Flask(__name__)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("--- [СТАРТ] Глобальная инициализация прошла успешно. ---")

except Exception as e:
    print(f"--- [СТАРТ] !!! КРИТИЧЕСКАЯ ОШИБКА ПРИ ГЛОБАЛЬНОЙ ИНИЦИАЛИЗАЦИИ: {e} ---")
    print(traceback.format_exc())


# === Асинхронные функции-обработчики ===
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
        "Привет! 😊\n\nБот работает, и ваш ID сохранен для рассылок. (v_debug)",
        reply_markup=reply_markup
    )

async def handle_admin_command_async(update: Update):
    # Пока просто отвечаем, что команда получена
    await update.message.reply_text("Команда администратора распознана! (v_debug)")


# === ГЛАВНЫЙ ВЕБХУК С МАКСИМАЛЬНЫМ ЛОГИРОВАНИЕМ ===
@app.route('/', methods=['POST'])
def webhook():
    print("\n--- 1. ВЕБХУК ВЫЗВАН ---")
    try:
        # Получаем "сырые" байты тела запроса для надежности
        raw_data = request.get_data()
        print(f"--- 2. ПОЛУЧЕНЫ СЫРЫЕ ДАННЫЕ (raw_data), длина: {len(raw_data)} байт ---")
        
        if not raw_data:
            print("--- 3. ПРОВАЛ: Тело запроса пустое. Выход. ---")
            return "ok", 200

        # Декодируем байты в строку и парсим JSON
        update_data = json.loads(raw_data.decode('utf-8'))
        print(f"--- 3. УСПЕХ: Данные JSON: {json.dumps(update_data, indent=2)} ---")
        
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
            asyncio.run(handle_admin_command_async(update))
        else:
            print("--- 5. ПРОВАЛ: Сообщение не является известной командой. ---")

    except Exception as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА ВНУТРИ ВЕБХУКА !!! ---")
        # Эта функция выведет ПОЛНУЮ информацию об ошибке в логи
        print(traceback.format_exc())
            
    print("--- 6. ЗАВЕРШЕНИЕ РАБОТЫ ВЕБХУКА ---")
    return 'ok', 200
