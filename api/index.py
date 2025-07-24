import os
import asyncio
import traceback # импортируем модуль для вывода детальных ошибок
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# --- ОТЛАДОЧНЫЙ ВЫВОД: Проверяем, что скрипт вообще запускается ---
print("--- Скрипт api/index.py запущен ---")

try:
    # === НАСТРОЙКИ: Переменные окружения Vercel ===
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    ADMIN_IDS_STR = os.environ.get('ADMIN_IDS', '')

    # --- ОТЛАДОЧНЫЙ ВЫВОД: Показываем, что мы получили из переменных ---
    print(f"BOT_TOKEN найден: {'Да' if BOT_TOKEN else 'Нет'}")
    print(f"SUPABASE_URL найден: {'Да' if SUPABASE_URL else 'Нет'}")
    print(f"SUPABASE_KEY найден: {'Да' if SUPABASE_KEY else 'Нет'}")
    print(f"Получена строка ADMIN_IDS: '{ADMIN_IDS_STR}'")

    # --- Превращаем строку в список ID с защитой от ошибок ---
    ADMIN_IDS = []
    if ADMIN_IDS_STR:
        try:
            # Превращаем строку в список целых чисел. Пропускаем пустые элементы.
            ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]
            print(f"Список ADMIN_IDS успешно создан: {ADMIN_IDS}")
        except ValueError as e:
            print(f"!!! КРИТИЧЕСКАЯ ОШИБКА: Не удалось преобразовать ADMIN_IDS в числа. Проверьте формат строки! Ошибка: {e}")
            ADMIN_IDS = [] # В случае ошибки оставляем список админов пустым

    # === ИНИЦИАЛИЗАЦИЯ ===
    bot = Bot(token=BOT_TOKEN)
    app = Flask(__name__)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("--- Клиенты Bot и Supabase успешно инициализированы ---")

except Exception as e:
    # Эта ловушка сработает, если ошибка произошла на самом верхнем уровне (например, нет ключей)
    print(f"!!! КРИТИЧЕСКАЯ ОШИБКА ПРИ ИНИЦИАЛИЗАЦИИ: {e}")
    traceback.print_exc()


# --- Функции для работы с базой (без изменений) ---
async def save_user_async(user_id: int):
    # ... (код функции без изменений)
    try:
        await asyncio.to_thread(
            supabase.table('users').upsert,
            {'chat_id': user_id},
            on_conflict='chat_id'
        )
        print(f"Сохранен или обновлен пользователь с ID: {user_id}")
    except Exception as e:
        print(f"Ошибка при сохранении пользователя {user_id} в Supabase: {e}")
# ... (остальные async функции без изменений)
async def get_all_user_ids_async() -> list[int]:
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
    user_id = update.message.chat_id
    await save_user_async(user_id)
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

async def broadcast_message_async(message_text: str):
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
    # --- ОТЛАДОЧНЫЙ ВЫВОД: Проверяем, что вебхук вызывается ---
    print("--- Входящий запрос в /webhook ---")
    try:
        update_data = request.get_json()
        if update_data:
            update = Update.de_json(update_data, bot)
            if update.message and update.message.text:
                text = update.message.text
                print(f"Получено сообщение: '{text}' от пользователя {update.message.chat_id}")
                if text == '/start':
                    asyncio.run(handle_start_async(update))
                elif text.startswith('/'):
                    asyncio.run(handle_admin_command_async(update))
    except Exception as e:
        # Эта ловушка поймает любую ошибку внутри вебхука
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА ВНУТРИ ВЕБХУКА: {e}")
        traceback.print_exc() # Печатаем полную трассировку ошибки
        
    return 'ok', 200
