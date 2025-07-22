import os
import asyncio
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot

# === НАСТРОЙКИ (ВОТ ОНИ!) ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Ваши URL-адреса, которые мы вернули на место
URL_DASHBOARD = "https://aleksei23122012.github.io/DMdashbordbot/Dashboard.htm?v=11" # Новая версия!
URL_KNOWLEDGE_BASE = "https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"
URL_ALMANAC = "https://baza-znaniy-app.vercel.app/"
URL_OTZIV = "https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

async def handle_start(update: Update):
    # Создаем клавиатуру со всеми вашими кнопками
    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url=URL_KNOWLEDGE_BASE))],
        [KeyboardButton("Дашборд", web_app=WebAppInfo(url=URL_DASHBOARD))],
        [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url=URL_ALMANAC))],
        [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url=URL_OTZIV))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! 😊\n\nЯ — твой помощник. Выбирай, что хочешь узнать или сделать:\n\n" # Ваш текст
        "✨ База знаний — полезные статьи и советы.\n"
        "✨ Дашборд — вся важная информация у тебя под рукой.\n"
        "✨ Отработка возражений — лайфхаки и рекомендации.\n"
        "✨ Отзывы и предложения — расскажи, как я могу стать лучше!\n\n"
        "Нажимай на кнопку ниже и начнем! 🚀",
        reply_markup=reply_markup
    )

@app.route('/', methods=['POST'])
def webhook():
    update_data = request.get_json()
    if update_data:
        update = Update.de_json(update_data, bot)
        if update.message and update.message.text == '/start':
            asyncio.run(handle_start(update))
    return 'ok', 200

# Код ниже можно удалить, так как веб-хук мы уже установили вручную
# и Vercel сам будет вызывать функцию webhook при получении запроса.
