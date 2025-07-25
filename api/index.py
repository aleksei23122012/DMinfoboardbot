import os
import asyncio
import traceback
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# === Глобальная область: только создание Flask-приложения ===
app = Flask(__name__)


# === Асинхронные функции-обработчики ===

# --- ИЗМЕНЕНИЕ ЗДЕСЬ: Функция теперь принимает `username` ---
async def save_user_async(supabase_client, user_id: int, username: str):
    """Асинхронно сохраняет ID и логин пользователя в базу данных Supabase."""
    try:
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ: Вставляем объект с двумя полями ---
        user_data = {'chat_id': user_id, 'username': username}
        await asyncio.to_thread(supabase_client.table('users').upsert, user_data, on_conflict='chat_id')
        print(f"Пользователь {user_id} ({username}) успешно сохранен/обновлен в Supabase.")
    except Exception as e:
        print(f"!!! ОШИКА при сохранении пользователя {user_id}: {e}")

async def remove_user_async(supabase_client, user_id: int):
    """Асинхронно удаляет пользователя, который заблокировал бота."""
    try:
        await asyncio.to_thread(supabase_client.table('users').delete().eq('chat_id', user_id).execute)
        print(f"Пользователь {user_id} удален из базы (заблокировал бота).")
    except Exception as e:
        print(f"!!! ОШИБКА при удалении пользователя {user_id}: {e}")

# --- ИЗМЕНЕНИЕ ЗДЕСЬ: Получаем `username` из `update` ---
async def handle_start_async(bot, supabase_client, update: Update):
    """Обрабатывает команду /start."""
    user = update.message.from_user
    user_id = user.id
    # Получаем username. Если его нет, используем пустую строку.
    username = user.username if user.username else ""
    
    # --- ИЗМЕНЕНИЕ ЗДЕСЬ: Передаем `username` в функцию сохранения ---
    await save_user_async(supabase_client, user_id, username)
    
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

async def broadcast_message_async(bot, supabase_client, admin_chat_id, message_text: str):
    # ... (эта функция остается без изменений)
    user_ids = []
    try:
        response = await asyncio.to_thread(supabase_client.table('users').select('chat_id').execute)
        user_ids = [item['chat_id'] for item in response.data]
    except Exception as e:
        print(f"!!! ОШИБКА при получении списка пользователей для рассылки: {e}")
        await bot.send_message(chat_id=admin_chat_id, text=f"Ошибка получения списка пользователей: {e}")
        return
        
    print(f"Начинаю рассылку для {len(user_ids)} пользователей.")
    success_count = 0
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=message_text, parse_mode='Markdown')
            success_count += 1
            await asyncio.sleep(0.05)
        except error.Forbidden:
            await remove_user_async(supabase_client, user_id)
        except error.TelegramError as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
    
    await bot.send_message(chat_id=admin_chat_id, text=f"Рассылка завершена. Отправлено сообщений: {success_count} из {len(user_ids)}.")


async def handle_admin_command_async(bot, supabase_client, update: Update):
    # ... (эта функция остается без изменений)
    text_parts = update.message.text.split(' ', 1)
    command = text_parts[0]
    admin_id = update.message.chat_id
    
    if command == '/broadcast' and len(text_parts) > 1:
        message_to_send = text_parts[1]
        await update.message.reply_text("Начинаю рассылку...")
        await broadcast_message_async(bot, supabase_client, admin_id, message_to_send)
    elif command == '/stats':
        try:
            response = await asyncio.to_thread(supabase_client.table('users').select('chat_id', count='exact').execute)
            await update.message.reply_text(f"Всего пользователей в базе: {response.count}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка получения статистики: {e}")
    else:
        await update.message.reply_text(
            "Неизвестная команда или неверный формат.\n"
            "Доступные команды:\n`/broadcast <текст>`\n`/stats`",
            parse_mode='Markdown'
        )

# === ГЛАВНЫЙ ВЕБХУК: ТОЧКА ВХОДА ДЛЯ TELEGRAM ===
@app.route('/', methods=['POST'])
def webhook():
    # ... (эта функция остается без изменений)
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
                asyncio.run(handle_admin_command_async(bot, supabase, update))

    except Exception as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ !!! ---")
        print(traceback.format_exc())
            
    return 'ok', 200
