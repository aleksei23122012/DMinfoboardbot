import os
import asyncio
import traceback
import sys
import requests # <-- НОВЫЙ ВАЖНЫЙ ИМПОРТ
from flask import Flask, request
from telegram import Update, Bot
from supabase import create_client, Client # <-- Supabase теперь нужен только для чтения

# === Глобальная область: только создание Flask-приложения ===
app = Flask(__name__)

# --- НОВАЯ СИНХРОННАЯ ФУНКЦИЯ СОХРАНЕНИЯ ЧЕРЕЗ REQUESTS ---
def save_user_sync_requests(supabase_url, supabase_key, user_id: int):
    """СИНХРОННО сохраняет ID пользователя через прямой HTTP-запрос."""
    try:
        print(f"--- [HTTP] Попытка POST-запроса для {user_id}. ---")
        sys.stdout.flush()

        # Формируем URL и заголовки для прямого запроса к API Supabase
        url = f"{supabase_url}/rest/v1/users"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates" # Команда "upsert": вставить или обновить, если есть
        }
        data = { "chat_id": user_id }

        # Выполняем POST-запрос с таймаутом 5 секунд
        response = requests.post(url, headers=headers, json=data, timeout=5)
        
        # Этот лог появится, только если мы получим ответ от сервера
        print(f"--- [HTTP] ПОЛУЧЕН ОТВЕТ: Статус {response.status_code}, Тело: {response.text} ---")
        sys.stdout.flush()

        if 200 <= response.status_code < 300:
            print(f"--- [HTTP] УСПЕХ: Пользователь {user_id} сохранен через HTTP. ---")
        else:
            print(f"--- [HTTP] !!! ОШИБКА: Неуспешный статус ответа. ---")

    except requests.exceptions.Timeout:
        print(f"--- [HTTP] !!! КРИТИЧЕСКАЯ ОШИБКА: Запрос к Supabase отвалился по таймауту! ---")
    except Exception as e:
        print(f"--- [HTTP] !!! КРИТИЧЕСКАЯ ОШИБКА при HTTP-запросе: {e} !!!")
        print(traceback.format_exc())
    sys.stdout.flush()


# --- Асинхронный обработчик, который вызывает синхронную функцию ---
async def handle_start_async(bot, supabase_url, supabase_key, update: Update):
    """Обрабатывает /start: сначала база, потом ответ."""
    user_id = update.message.chat_id
    
    # Сначала вызываем блокирующую функцию сохранения
    save_user_sync_requests(supabase_url, supabase_key, user_id)
    
    # Только после завершения работы с базой отправляем ответ
    await bot.send_message(
        chat_id=user_id,
        text="ФИНАЛЬНЫЙ ТЕСТ: v_requests_final" # Новое уникальное сообщение
    )


# === ГЛАВНЫЙ ВЕБХУК ===
@app.route('/', methods=['POST'])
def webhook():
    try:
        BOT_TOKEN = os.environ['BOT_TOKEN']
        SUPABASE_URL = os.environ['SUPABASE_URL']
        SUPABASE_KEY = os.environ['SUPABASE_KEY']

        bot = Bot(token=BOT_TOKEN)
        
        update_data = request.get_json()
        update = Update.de_json(update_data, bot)
        
        if update.message and update.message.text == '/start':
            # Передаем URL и ключ напрямую в обработчик
            asyncio.run(handle_start_async(bot, SUPABASE_URL, SUPABASE_KEY, update))

    except Exception as e:
        print(f"--- !!! КРИТИЧЕСКАЯ ОШИБКА В ВЕБХУКЕ !!! ---")
        print(traceback.format_exc())
            
    return 'ok', 200
