import os
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot

# === НАСТРОЙКИ ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
URL_DASHBOARD = "https://aleksei23122012.github.io/DMdashbordbot/Dashboard.htm?v=12" # Новая версия
URL_KNOWLEDGE_BASE = "https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"
URL_ALMANAC = "https://baza-znaniy-app.vercel.app/"
URL_OTZIV = "https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"

# Создаем объект бота
bot = Bot(token=BOT_TOKEN)
# Создаем Flask-приложение
app = Flask(__name__)

# Это главная функция, которая будет вызываться при получении сообщения
@app.route('/', methods=['POST'])
def webhook():
    # Получаем данные из запроса от Telegram
    update_data = request.get_json()
    
    if update_data:
        # Превращаем JSON в объект Update
        update = Update.de_json(update_data, bot)
        
        # Проверяем, что это сообщение и текст в нем - /start
        if update.message and update.message.text == '/start':
            # === Новая синхронная логика ===
            # Создаем клавиатуру
            keyboard = [
                [KeyboardButton("База знаний", web_app=WebAppInfo(url=URL_KNOWLEDGE_BASE))],
                [KeyboardButton("Дашборд", web_app=WebAppInfo(url=URL_DASHBOARD))],
                [KeyboardButton("Отработка возражений", web_app=WebAppInfo(url=URL_ALMANAC))],
                [KeyboardButton("Отзывы и предложения", web_app=WebAppInfo(url=URL_OTZIV))]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            # Отправляем сообщение СИНХРОННО
            bot.send_message(
                chat_id=update.effective_chat.id,
                text="Привет! 😊\n\nЯ — твой помощник...", # Ваш длинный текст
                reply_markup=reply_markup
            )
            
    # Возвращаем Telegram ответ "ok", чтобы он знал, что мы получили сообщение
    return 'ok', 200
