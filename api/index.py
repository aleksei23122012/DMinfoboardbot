import os
import asyncio
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot

# === НАСТРОЙКИ ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
# URL для дашборда здесь больше не нужен, так как он задан в @BotFather,
# но мы оставим его для ясности и на случай будущих изменений.
URL_DASHBOARD = "https://aleksei23122012.github.io/DMdashbordbot/Dashboard.htm?v=15" # Новая версия
URL_KNOWLEDGE_BASE = "https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"
URL_ALMANAC = "https://baza-znaniy-app.vercel.app/"
URL_OTZIV = "https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# Асинхронная функция для отправки приветственного сообщения
async def handle_start_async(update: Update):
    # === ИЗМЕНЕНИЕ: Кнопка "Дашборд" удалена из этого списка ===
    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url=URL_KNOWLEDGE_BASE))],
        [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url=URL_ALMANAC))],
        [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url=URL_OTZIV))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # Текст приветствия теперь указывает на кнопку Меню
    await update.message.reply_text(
        "Привет! 😊\n\n"
        "Чтобы открыть главный дашборд, нажми на кнопку **Меню** слева от поля ввода.\n\n"
        "А с помощью кнопок ниже ты можешь открыть другие полезные разделы:",
        reply_markup=reply_markup
    )

# Главная функция, которую вызывает Vercel
@app.route('/', methods=['POST'])
def webhook():
    update_data = request.get_json()
    if update_data:
        update = Update.de_json(update_data, bot)
        if update.message and update.message.text == '/start':
            # Запускаем асинхронную отправку сообщения
            asyncio.run(handle_start_async(update))
            
    return 'ok', 200
