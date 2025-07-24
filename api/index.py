import os
import asyncio
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# === НАСТРОЙКИ: Переменные окружения Vercel ===
# Эти данные вы должны добавить в настройки вашего проекта на Vercel
# (Settings -> Environment Variables)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# !!! ВАЖНО: Замените 123456789 на ваш настоящий Telegram User ID !!!
# Чтобы его узнать, напишите боту @userinfobot, он пришлет вам ваш ID.
ADMIN_ID = 8004572298

# === URL'ы для кнопок (остаются без изменений) ===
URL_KNOWLEDGE_BASE = "https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"
URL_ALMANAC = "https://baza-znaniy-app.vercel.app/"
URL_OTZIV = "https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"

# === ИНИЦИАЛИЗАЦИЯ ===
# Инициализируем бота
bot = Bot(token=BOT_TOKEN)
# Инициализируем Flask-приложение
app = Flask(__name__)
# Инициализируем клиент для подключения к базе данных Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ SUPABASE ---

async def save_user_async(user_id: int):
    """Асинхронно сохраняет chat_id пользователя в таблицу 'users' в Supabase."""
    try:
        # Используем upsert: он вставит новую запись, если chat_id не существует.
        # Если такой chat_id уже есть, ничего не произойдет. Идеально для нас.
        # supabase-py не является полностью асинхронной, поэтому оборачиваем вызов в to_thread.
        await asyncio.to_thread(
            supabase.table('users').upsert,
            {'chat_id': user_id},
            on_conflict='chat_id' # Указываем, что конфликт нужно проверять по полю chat_id
        )
        print(f"Сохранен или обновлен пользователь с ID: {user_id}")
    except Exception as e:
        print(f"Ошибка при сохранении пользователя {user_id} в Supabase: {e}")

async def get_all_user_ids_async() -> list[int]:
    """Асинхронно получает все chat_id из таблицы 'users'."""
    try:
        response = await asyncio.to_thread(
            supabase.table('users').select('chat_id').execute
        )
        user_ids = [item['chat_id'] for item in response.data]
        return user_ids
    except Exception as e:
        print(f"Ошибка при получении ID пользователей из Supabase: {e}")
        return []

async def remove_user_async(user_id: int):
    """Асинхронно удаляет пользователя по chat_id (например, если он заблокировал бота)."""
    try:
        await asyncio.to_thread(
            supabase.table('users').delete().eq('chat_id', user_id).execute
        )
        print(f"Пользователь {user_id} удален из базы, так как заблокировал бота.")
    except Exception as e:
        print(f"Ошибка при удалении пользователя {user_id}: {e}")
        
# --- ОСНОВНЫЕ ОБРАБОТЧИКИ КОМАНД БОТА ---

async def handle_start_async(update: Update):
    """Обрабатывает команду /start, сохраняет ID пользователя и отправляет приветствие."""
    user_id = update.message.chat_id
    # При каждом /start мы сохраняем ID пользователя в нашу базу
    await save_user_async(user_id)

    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url=URL_KNOWLEDGE_BASE))],
        [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url=URL_ALMANAC))],
        [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url=URL_OTZIV))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Привет! 😊\n\n"
        "Чтобы открыть главный дашборд, нажми на кнопку **Дашборд** слева от поля ввода.\n\n"
        "А с помощью кнопок ниже ты можешь открыть другие полезные разделы.",
        reply_markup=reply_markup,
        parse_mode='Markdown' # Добавляем parse_mode для жирного шрифта
    )

async def broadcast_message_async(message_text: str):
    """Отправляет рассылку всем пользователям из базы."""
    user_ids = await get_all_user_ids_async()
    print(f"Начинаю рассылку для {len(user_ids)} пользователей.")
    
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=message_text, parse_mode='Markdown')
            await asyncio.sleep(0.1) # Небольшая задержка, чтобы не попасть под лимиты Telegram
        except error.Forbidden:
            # Если пользователь заблокировал бота, Telegram выдаст ошибку "Forbidden".
            # Удаляем такого пользователя из нашей базы.
            await remove_user_async(user_id)
        except error.TelegramError as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def handle_admin_command_async(update: Update):
    """Обрабатывает команды, отправленные администратором."""
    if update.message.chat_id != ADMIN_ID:
        # Если команду пишет не админ, можно ничего не отвечать или написать об ошибке
        return

    text_parts = update.message.text.split(' ', 1)
    command = text_parts[0]
    
    if command == '/broadcast' and len(text_parts) > 1:
        message_to_send = text_parts[1]
        await update.message.reply_text("Начинаю рассылку...")
        await broadcast_message_async(message_to_send)
        await update.message.reply_text("Рассылка завершена.")
    elif command == '/stats':
        user_ids = await get_all_user_ids_async()
        await update.message.reply_text(f"Всего пользователей в базе: {len(user_ids)}")
    else:
        await update.message.reply_text(
            "Неизвестная команда или неверный формат.\n"
            "Доступные команды:\n"
            "`/broadcast <текст сообщения>`\n"
            "`/stats`",
            parse_mode='Markdown'
        )
        
# --- ГЛАВНЫЙ ВЕБХУК ДЛЯ VERCEL (основная точка входа) ---

@app.route('/', methods=['POST'])
def webhook():
    """Эта функция принимает все обновления от Telegram."""
    update_data = request.get_json()
    if update_data:
        update = Update.de_json(update_data, bot)
        if update.message and update.message.text:
            text = update.message.text
            
            # В зависимости от текста, запускаем нужную асинхронную функцию
            if text == '/start':
                asyncio.run(handle_start_async(update))
            elif text.startswith('/'): # Если сообщение начинается со слеша, считаем его командой
                 asyncio.run(handle_admin_command_async(update))
            
    return 'ok', 200
