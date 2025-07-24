import os
import asyncio
import traceback
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# === НАСТРОЙКИ: Переменные окружения Vercel ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
ADMIN_IDS_STR = os.environ.get('ADMIN_IDS', '')

# Превращаем строку с ID администраторов в список чисел
ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

# === URL'ы для кнопок ===
URL_KNOWLEDGE_BASE = "https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"
URL_ALMANAC = "https://baza-znaniy-app.vercel.app/"
URL_OTZIV = "https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"

# === ИНИЦИАЛИЗАЦИЯ ===
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- АСИНХРОННЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С БОТОМ И БАЗОЙ ---

async def save_user_async(user_id: int):
    """Асинхронно сохраняет chat_id пользователя в Supabase."""
    try:
        await asyncio.to_thread(
            supabase.table('users').upsert,
            {'chat_id': user_id},
            on_conflict='chat_id'
        )
        print(f"Сохранен или обновлен пользователь с ID: {user_id}")
    except Exception as e:
        print(f"Ошибка при сохранении пользователя {user_id} в Supabase: {e}")
        print(traceback.format_exc())

async def get_all_user_ids_async() -> list[int]:
    """Асинхронно получает все chat_id из Supabase."""
    # ... (код этой и других функций остается таким же, как в версии с "несколькими админами")
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
    try:
        await asyncio.to_thread(
            supabase.table('users').delete().eq('chat_id', user_id).execute
        )
        print(f"Пользователь {user_id} удален из базы, так как заблокировал бота.")
    except Exception as e:
        print(f"Ошибка при удалении пользователя {user_id}: {e}")

async def handle_start_async(update: Update):
    """Обрабатывает /start, сохраняет пользователя и отправляет приветствие."""
    user_id = update.message.chat_id
    await save_user_async(user_id) # Сохраняем ID

    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url=URL_KNOWLEDGE_BASE))],
        [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url=URL_ALMANAC))],
        [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url=URL_OTZIV))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # Здесь мы используем await, что правильно
    await update.message.reply_text(
        "Привет! 😊\n\n"
        "Чтобы открыть главный дашборд, нажми на кнопку **Дашборд** слева от поля ввода.\n\n"
        "А с помощью кнопок ниже ты можешь открыть другие полезные разделы.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def broadcast_message_async(message_text: str):
    """Отправляет рассылку всем пользователям."""
    user_ids = await get_all_user_ids_async()
    print(f"Начинаю рассылку для {len(user_ids)} пользователей.")
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=message_text, parse_mode='Markdown')
            await asyncio.sleep(0.1)
        except error.Forbidden:
            await remove_user_async(user_id)
        except error.TelegramError as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def handle_admin_command_async(update: Update):
    """Обрабатывает команды администратора."""
    if update.message.chat_id not in ADMIN_IDS:
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
        
# --- ГЛАВНЫЙ ВЕБХУК ДЛЯ VERCEL ---
@app.route('/', methods=['POST'])
def webhook():
    """Эта синхронная функция запускает нужные асинхронные обработчики."""
    try:
        update_data = request.get_json()
        if update_data:
            update = Update.de_json(update_data, bot)
            if update.message and update.message.text:
                text = update.message.text
                
                # Здесь мы используем asyncio.run, что правильно
                if text == '/start':
                    asyncio.run(handle_start_async(update))
                elif text.startswith('/'):
                     asyncio.run(handle_admin_command_async(update))
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ: {e}")
        print(traceback.format_exc())
            
    return 'ok', 200
