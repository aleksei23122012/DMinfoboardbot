import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot

# === ТОЛЬКО FLASK ===
app = Flask(__name__)

# === Самый простой обработчик ===
async def send_final_test_reply(bot, update: Update):
    """Просто отправляет уникальный ответ."""
    try:
        await bot.send_message(
            chat_id=update.message.chat_id,
            text="ПОБЕДА НАД КЕШЕМ: v_final_barebones" # Уникальный текст, которого не было раньше
        )
        print("--- УСПЕХ: ОТВЕТ 'v_final_barebones' ОТПРАВЛЕН ---")
    except Exception as e:
        print(f"--- ОШИБКА в send_final_test_reply: {e} ---")


# === ГЛАВНЫЙ ВЕБХУК: МИНИМАЛЬНАЯ ВЕРСИЯ ===
@app.route('/', methods=['POST'])
def webhook():
    print("--- ВХОД В 'ГОЛЫЙ' ВЕБХУК ---")
    try:
        BOT_TOKEN = os.environ['BOT_TOKEN']
        bot = Bot(token=BOT_TOKEN)
        
        update_data = request.get_json()
        update = Update.de_json(update_data, bot)
        
        if update.message and update.message.text == '/start':
            asyncio.run(send_final_test_reply(bot, update))

    except Exception as e:
        print(f"--- ОШИБКА В 'ГОЛОМ' ВЕБХУКЕ: {e} ---")
            
    return 'ok', 200
