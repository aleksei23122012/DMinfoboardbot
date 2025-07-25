import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot

# === ТОЛЬКО FLASK ===
app = Flask(__name__)

# === Самый простой обработчик ===
async def send_final_test_reply(bot, update: Update):
    """Просто отправляет уникальный ответ."""
    await bot.send_message(
        chat_id=update.message.chat_id,
        text="ПОСЛЕДНИЙ ТЕСТ: v_barebones" # Уникальный текст, которого не было раньше
    )
    print("--- УСПЕХ: ОТВЕТ 'v_barebones' ОТПРАВЛЕН ---")


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
