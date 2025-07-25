import os
import asyncio
import traceback
import sys
import requests # Используем requests для надежной работы с Supabase
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client # Supabase клиент можно использовать для чтения, если понадобится

# === Глобальная область: только создание Flask-приложения ===
app = Flask(__name__)

# --- НОВАЯ СИНХРОННАЯ ФУНКЦИЯ СОХРАНЕНИЯ ЧЕРЕЗ REQUESTS ---
def save_user_sync_requests(supabase_url, supabase_key, user_id: int):
    """СИНХРОННО сохраняет ID пользователя через прямой HTTP-запрос."""
    try:
        url = f"{supabase_url}/rest/v1/users"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        data = { "chat_id": user_id }
        response = requests.post(url, headers=headers, json=data, timeout=5)
        
        if 200 <= response.status_code < 300:
            print(f"Пользователь {user_id} успешно сохранен/обновлен через HTTP.")
        else:
            print(f"!!! ОШИБКА HTTP: Статус {response.status_code}, Тело: {response.text}")

    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА при HTTP-запросе к Supabase: {e}")
        print(traceback.format_exc())

# --- Асинхронные функции-обработчики ---
async def handle_start_async(bot, supabase_url, supabase_key, update: Update):
    """Обрабатывает /start: сначала база, потом ответ."""
    user_id = update.message.chat_id
    save_user_sync_requests(supabase_url, supabase_key, user_id)
    
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

async def handle_admin_command_async(bot, supabase_url, supabase_key, update: Update):
    """Обрабатывает команды администратора (/stats, /broadcast)."""
    text_parts = update.message.text.split(' ', 1)
    command = text_parts[0]
    admin_id = update.message.chat_id
    
    # Для чтения данных можно использовать стандартный клиент, он обычно надежнее
    supabase_client: Client = create_client(supabase_url, supabase_key)

    if command == '/broadcast' and len(text_parts) > 1:
        message_to_send = text_parts[1]
        await update.message.reply_text("Начинаю рассылку...")
        
        user_ids = []
        try:
            response = supabase_client.table('users').select('chat_id').execute()
            user_ids = [item['chat_id'] for item in response.data]
        except Exception as e:
            await update.message.reply_text(f"Ошибка получения списка пользователей: {e}")
            return

        success_count = 0
        for user_id in user_ids:
            try:
                await bot.send_message(chat_id=user_id, text=message_to_send, parse_mode='Markdown')
                success_count += 1
                await asyncio.sleep(0.05)
            except error.Forbidden:
                # В реальном приложении здесь тоже нужно будет сделать DELETE-запрос
                print(f"Пользователь {user_id} заблокировал бота.")
            except error.TelegramError as e:
                print(f"Не удалось отправить сообщение {user_id}: {e}")
        
        await update.message.reply_text(f"Рассылка завершена. Отправлено: {success_count} из {len(user_ids)}.")

    elif command == '/stats':
        try:
            response = supabase_client.table('users').select('chat_id', count='exact').execute()
            await update.message.reply_text(f"Всего пользователей в базе: {response.count}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка получения статистики: {e}")
    else:
        await update.message.reply_text(
            "Неизвестная команда или неверный формат.\n"
            "Доступные команды:\n`/broadcast <текст>`\n`/stats`",
            parse_mode='Markdown'
        )

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
        
        update_data = request.get_json()
        update = Update.de_json(update_data, bot)
        
        if update.message and update.message.text:
            text = update.message.text
            user_id = update.message.chat_id
            
            if text == '/start':
                asyncio.run(handle_start_async(bot, SUPABASE_URL, SUPABASE_KEY, update))
            elif text.startswith('/') and user_id in ADMIN_IDS:
                asyncio.run(handle_admin_command_async(bot, SUPABASE_URL, SUPABASE_KEY, update))

    except Exception as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ !!! ---")
        print(traceback.format_exc())
            
    return 'ok', 200
