import os
import asyncio
import traceback
from flask import Flask, request
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Bot, error
from supabase import create_client, Client

# === Глобальная область: только создание Flask-приложения ===
app = Flask(__name__)


# === Асинхронные функции-обработчики ===
async def save_user_async(supabase_client, user_id: int):
    """Асинхронно сохраняет ID пользователя в базу данных Supabase."""
    try:
        # Используем asyncio.to_thread для безопасного выполнения синхронного кода
        await asyncio.to_thread(supabase_client.table('users').upsert, {'chat_id': user_id}, on_conflict='chat_id')
        # Этот лог появится, только если операция выше успешно завершится
        print(f"Пользователь {user_id} успешно сохранен/обновлен в Supabase.")
    except Exception as e:
        print(f"!!! ОШИБКА при сохранении пользователя {user_id}: {e}")

async def remove_user_async(supabase_client, user_id: int):
    """Асинхронно удаляет пользователя, который заблокировал бота."""
    try:
        await asyncio.to_thread(supabase_client.table('users').delete().eq('chat_id', user_id).execute)
        print(f"Пользователь {user_id} удален из базы (заблокировал бота).")
    except Exception as e:
        print(f"!!! ОШИБКА при удалении пользователя {user_id}: {e}")

# --- ГЛАВНОЕ ИЗМЕНЕНИЕ ЗДЕСЬ ---
async def handle_start_async(bot, supabase_client, update: Update):
    """Обрабатывает команду /start ПОСЛЕДОВАТЕЛЬНО."""
    user_id = update.message.chat_id
    
    # --- ШАГ 1: СНАЧАЛА СОХРАНЯЕМ В БАЗУ ---
    # `await` заставит код остановиться здесь и дождаться завершения.
    await save_user_async(supabase_client, user_id)
    
    # --- ШАГ 2: ТОЛЬКО ПОТОМ ОТПРАВЛЯЕМ ОТВЕТ ---
    keyboard = [
        [KeyboardButton("База знаний", web_app=WebAppInfo(url="https://aleksei2
[patch]--- a/telegram_bot.py
+++ b/telegram_bot.py
@@ -11,8 +11,6 @@
 # === НАСТРОЙКИ ===
 BOT_TOKEN = os.environ.get('BOT_TOKEN')
 # URL для дашборда здесь больше не нужен, так как он задан в @BotFather,
-# но мы оставим его для ясности и на случай будущих изменений.
-URL_DASHBOARD = "https://aleksei23122012.github.io/DMdashbordbot/Dashboard.htm?v=15" # Новая версия
 URL_KNOWLEDGE_BASE = "https://aleksei23122012.teamly.ru/space/00647e86-cd4b-46ef-9903-0af63964ad43/article/17e16e2a-92ff-463c-8bf4-eaaf202c0bc7"
 URL_ALMANAC = "https://baza-znaniy-app.vercel.app/"
 URL_OTZIV = "https://docs.google.com/forms/d/e/1FAIpQLSedAPNqKkoJxer4lISLVsQgmu6QpPagoWreyvYOz7DbFuanFw/viewform?usp=header"
