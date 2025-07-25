import os
import traceback
import sys
import requests
from flask import Flask, request
from telegram import Update, Bot

# === ТОЛЬКО FLASK ===
app = Flask(__name__)

# === ГЛАВНЫЙ ВЕБХУК: ТОЛЬКО ОДНА ЗАДАЧА - ЗАПИСЬ В БАЗУ ===
@app.route('/', methods=['POST'])
def webhook():
    print("\n--- [ФИНАЛЬНЫЙ ТЕСТ] Вход в вебхук. ---")
    sys.stdout.flush()
    try:
        # === Получение данных ===
        BOT_TOKEN = os.environ['BOT_TOKEN']
        SUPABASE_URL = os.environ['SUPABASE_URL']
        SUPABASE_KEY = os.environ['SUPABASE_KEY']
        
        bot = Bot(token=BOT_TOKEN)
        update_data = request.get_json()
        update = Update.de_json(update_data, bot)
        
        if not (update.message and update.message.text == '/start'):
            print("--- [ФИНАЛЬНЫЙ ТЕСТ] Запрос не является командой /start. Выход. ---")
            return "ok", 200

        user = update.message.from_user
        user_id = user.id
        username = user.username if user.username else ""

        print(f"--- [ФИНАЛЬНЫЙ ТЕСТ] Получен /start от {user_id}. Начинаю тест Supabase. ---")
        sys.stdout.flush()

        # === ПРЯМОЙ HTTP-ЗАПРОС К SUPABASE (САМЫЙ НАДЕЖНЫЙ МЕТОД) ===
        url = f"{SUPABASE_URL}/rest/v1/users"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        data = { "chat_id": user_id, "username": username }
        
        print("--- [ФИНАЛЬНЫЙ ТЕСТ] Отправляю POST-запрос в Supabase... ---")
        sys.stdout.flush()
        
        # Выполняем POST-запрос с явным таймаутом в 8 секунд
        response = requests.post(url, headers=headers, json=data, timeout=8)
        
        print(f"--- [ФИНАЛЬНЫЙ ТЕСТ] ПОЛУЧЕН ОТВЕТ ОТ SUPABASE: Статус {response.status_code}, Тело: {response.text} ---")
        sys.stdout.flush()

    except requests.exceptions.Timeout:
        print(f"--- [ФИНАЛЬНЫЙ ТЕСТ] !!! КРИТИЧЕСКАЯ ОШИБКА: Запрос к Supabase ОТВАЛИЛСЯ ПО ТАЙМАУТУ! Проблема в сети. ---")
        sys.stdout.flush()
    except Exception as e:
        print(f"--- [ФИНАЛЬНЫЙ ТЕСТ] !!! КРИТИЧЕСКАЯ ОШИБКА: {e} !!! ---")
        print(traceback.format_exc())
        sys.stdout.flush()
            
    print("--- [ФИНАЛЬНЫЙ ТЕСТ] Завершение работы вебхука. ---")
    sys.stdout.flush()
    return 'ok', 200
