import logging
import json
import os
import random
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext
from telegram.ext import filters
from dotenv import load_dotenv
from flask import Flask
import threading
import re
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=5000)

load_dotenv()

def load_pushup_quotes():
    with open("pushup_quotes.json", "r", encoding="utf-8") as file:
        return json.load(file)

DATA_FILE = "pushup_data.json"
PUSHUP_QUOTES = load_pushup_quotes()

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            logging.error("Ошибка чтения JSON-файла. Создается новый пустой словарь.")
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

data = load_data()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

keyboard = [
    ["/status", "/pushups"],
    ["/register", "/remove"],
    ["/debts"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_random_quote():
    return random.choice(PUSHUP_QUOTES)

def process_pushup_quote(quote):
    match = re.search(r"долг вырос на (\d+) отжиманий", quote)
    if match:
        return int(match.group(1))
    return 0

# Функция для начисления 50 отжиманий каждому пользователю каждый день в 00:00
def reset_debts():
    for username in data:
        data[username]["debt"] += 50  # Начисляем 50 отжиманий
    save_data(data)
    logging.info("Долги всех пользователей обновлены на 50 отжиманий.")

# Планировщик задач для ежедневного выполнения
scheduler = BackgroundScheduler()
scheduler.add_job(reset_debts, CronTrigger(hour=0, minute=0))  # Ежедневно в 00:00
scheduler.start()

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Анжуманя!", reply_markup=reply_markup)

async def register(update: Update, context: CallbackContext) -> None:
    username = update.message.from_user.username
    if not username:
        await update.message.reply_text("У вас нет никнейма в тг. Поставьте его.")
        return
    
    if username in data:
        await update.message.reply_text("Вы уже зарегистрированы!")
    else:
        data[username] = {"debt": 50, "last_update": datetime.now().isoformat()}
        save_data(data)
        await update.message.reply_text(f"{username}, вы зарегистрированы! Ваш долг: 50 отжиманий.")

async def remove(update: Update, context: CallbackContext) -> None:
    if not data:
        await update.message.reply_text("Нет зарегистрированных пользователей. Какого хуя?")
        return
    
    keyboard = [[InlineKeyboardButton(user, callback_data=f"remove_{user}")] for user in data.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите лузера для удаления:", reply_markup=reply_markup)

async def confirm_remove(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    username = query.data.replace("remove_", "")
    if username in data:
        del data[username]
        save_data(data)
        await query.answer()
        await query.edit_message_text(f"Пользователь {username} изгнан из списка посланников Бога Анжуманий и потерпел большой сасай.")
    else:
        await query.answer("Пользователь не найден.")

async def pushups(update: Update, context: CallbackContext) -> None:
    username = update.message.from_user.username
    if username not in data:
        await update.message.reply_text("Вы не зарегистрированы! Используйте /register.")
        return
    
    try:
        count = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Введите количество отжиманий после команды, например: /pushups 20")
        return
    
    data[username]["debt"] = max(0, data[username]["debt"] - count)
    quote = get_random_quote()
    additional_debt = process_pushup_quote(quote)
    data[username]["debt"] += additional_debt
    save_data(data)
    
    await update.message.reply_text(f"{username}, ваш долг уменьшен на {count}! Осталось: {data[username]['debt']} отжиманий.\n\n{quote}")

async def status(update: Update, context: CallbackContext) -> None:
    username = update.message.from_user.username
    if username not in data:
        await update.message.reply_text("Вы не зарегистрированы! Используйте /register блять.")
        return
    
    await update.message.reply_text(f"{username}, ваш текущий долг: {data[username]['debt']} отжиманий.")

async def show_all_debts(update: Update, context: CallbackContext) -> None:
    debt_message = "Долги всех участников:\n"
    for username, info in data.items():
        debt = info["debt"]
        debt_message += f"{username}: {debt} отжиманий\n"
    
    await update.message.reply_text(debt_message)

async def error_handler(update: Update, context: CallbackContext) -> None:
    logging.error(f"Произошла ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")

if __name__ == "__main__":
    import asyncio
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("remove", remove))
    application.add_handler(CommandHandler("pushups", pushups))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("debts", show_all_debts))
    application.add_handler(CallbackQueryHandler(confirm_remove))
    application.add_error_handler(error_handler)
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    application.run_polling()
