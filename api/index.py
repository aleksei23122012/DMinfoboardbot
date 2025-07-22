import os
import asyncio
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot

# === НАСТРОЙКИ ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
URL_DASHBOARD = "https://aleksei23122012.github.io/DMdashbordbot/Dashboard.htm?v=13" # Снова новая версия
URL_KNOWLEDGE_BASE = "https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"
URL_ALMANAC = "https://baza-znaniy-app.vercel.app/"
URL_OTZIV = "https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# Эта функция ДОЛЖНА быть асинхронной, так как reply_text - асинхронный
async def handle_start_async(update: Update):
    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url=URL_KNOWLEDGE_BASE))],
        [KeyboardButton("Дашборд", web_app=WebAppInfo(url=URL_DASHBOARD))],
        [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url=URL_ALMANAC))],
        [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url=URL_OTZIV))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    # Используем await для реальной отправки сообщения
    await update.message.reply_text(
        "Привет! 😊\n\nЯ — твой помощник...", # Ваш текст
        reply_markup=reply_markup
    )

# Главная функция, которую вызывает Vercel - она остается синхронной
@app.route('/', methods=['POST'])
def webhook():
    update_data = request.get_json()
    if update_data:
        update = Update.de_json(update_data, bot)
        if update.message and update.message.text == '/start':
            # === ПРАВИЛЬНЫЙ ЗАПУСК АСИНХРОННОЙ ЗАДАЧИ ===
            # Это гарантирует, что мы не конфликтуем с существующим циклом событий
            asyncio.run(handle_start_async(update))
            
    return 'ok', 200
