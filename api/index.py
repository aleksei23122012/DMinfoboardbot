import os
import asyncio
import traceback
import psycopg2 # Новая библиотека для Postgres
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error

# === Глобальная область: только создание Flask-приложения ===
app = Flask(__name__)

# --- НОВАЯ СИНХРОННАЯ ФУНКЦИЯ СОХРАНЕНИЯ В VERCEL POSTGRES ---
def save_user_sync_postgres(postgres_url, user_id: int, username: str):
    """СИНХРОННО сохраняет пользователя в Vercel Postgres."""
    try:
        # ON CONFLICT (chat_id) DO UPDATE... - это команда "upsert" для Postgres
        sql = """
        INSERT INTO users (chat_id, username)
        VALUES (%s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET
        username = EXCLUDED.username;
        """
        conn = psycopg2.connect(postgres_url)
        cur = conn.cursor()
        cur.execute(sql, (user_id, username))
        conn.commit()
        cur.close()
        conn.close()
        print(f"Пользователь {user_id} ({username}) успешно сохранен в Vercel Postgres.")
    except Exception as e:
        print(f"--- !!! ОШИБКА при сохранении в Postgres: {e} !!! ---")
        print(traceback.format_exc())

# --- Асинхронные обработчики ---
async def handle_start_async(bot, postgres_url, update: Update):
    user = update.message.from_user
    user_id = user.id
    username = user.username if user.username else ""
    
    save_user_sync_postgres(postgres_url, user_id, username)
    
    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url="https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"))],
        [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url="https://baza-znaniy-app.vercel.app/"))],
        [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url="https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! 😊\n\n"
        "Чтобы открыть главный дашборд, нажми на кнопку **Дашборд** слева от поля ввода.\n\n"
        "А с помощью кнопок ниже ты можешь открыть другие полезные разделы.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ... (здесь будет код для админских команд, пока можно оставить так)
async def handle_admin_command_async(bot, postgres_url, update: Update):
    # Добавим сюда полную логику админских команд
    text_parts = update.message.text.split(' ', 1)
    command = text_parts[0]
    admin_id = update.message.chat_id

    if command == '/stats':
        try:
            conn = psycopg2.connect(postgres_url)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users;")
            count = cur.fetchone()[0]
            cur.close()
            conn.close()
            await update.message.reply_text(f"Всего пользователей в базе: {count}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка получения статистики: {e}")
    else:
        await update.message.reply_text("Админская команда получена.")


# === ГЛАВНЫЙ ВЕБХУК ===
@app.route('/', methods=['POST'])
def webhook():
    try:
        BOT_TOKEN = os.environ['BOT_TOKEN']
        POSTGRES_URL = os.environ['POSTGRES_URL'] # Используем новую переменную
        ADMIN_IDS_STR = os.environ.get('ADMIN_IDS', '')
        ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

        bot = Bot(token=BOT_TOKEN)
        update_data = request.get_json()
        update = Update.de_json(update_data, bot)
        
        if update.message and update.message.text:
            text = update.message.text
            user_id = update.message.chat_id

            if text == '/start':
                asyncio.run(handle_start_async(bot, POSTGRES_URL, update))
            elif text.startswith('/') and user_id in ADMIN_IDS:
                asyncio.run(handle_admin_command_async(bot, POSTGRES_URL, update))

    except Exception as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ !!! ---")
        print(traceback.format_exc())
            
    return 'ok', 200
