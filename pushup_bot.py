import logging
import json
import os
import random
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext
from telegram.ext import filters
import re

DATA_FILE = "pushup_data.json"

PUSHUP_QUOTES = [
    "Респект чувак",
    "+Рэп",
    "Респект плюс", 
    "Сразу видно, красава",
    "Нет, ну блять, эти отжимания были заебись",
    "Бог отжиманий гордится тобой",
    "А ты мне нравишься парень, ну ка сделай еще 2 отжимания. Долг вырос на 2 анжумания.",
    "Хочешь, чтобы тебя уважали? Отжимайся! А если не хочешь – отжимайся дважды пидор!",
    "Бог Отжиманий не делает разминку. Это мир готовится к его нагрузке.",
    "Ты не слабый, просто тебе ещё рано ебшить в лиге Богов Отжиманий.",
    "Когда Бог Отжиманий падает, Земля просит прощения за то, что оказалась у него под рукой.",
    "Не можешь отжаться больше? Ну и хрен с тобой, эволюция сама разберётся. Долг вырос на 100 отжиманий.",
    "Пока ты ноешь, что устал, Бог Отжиманий отжался ещё раз. Теперь твоя мать им гордится.",
    "Бог Отжиманий никогда не отдыхает. Он просто даёт вселенной догнать его прогресс.",
    "Каждое отжимание – шаг ближе к величию. Или к сраной боли в мышцах, что тоже неплохо.",
    "Бог Отжиманий не вспотевает – это Вселенная мокреет от его мощности.",
    "Ты не устал, ты просто зажрался. Отжимайся, пока не станет заебсь!",
    "Кто-то бежит от проблем. Бог Отжиманий отжимается, пока проблемы не убегут от него.",
    "Бог Отжиманий не кладёт ладони на пол. Он держит Землю, чтобы она не улетела нахер.",
    "Когда ты отжимаешься, Бог Отжиманий смотрит и думает: ну хоть старается, уже неплохо.",
    "Не можешь отжаться 50 раз? Ладно, начни с 51, слабак, твой долг вырос на 1 отжимание.",
    "Заебался делать отжимания, не переживай, я договорился. Твой долг вырастает еще на 25 отжиманий.",
    "Когда Бог Отжиманий сделал своё первое отжимание, динозавры не выдержали нагрузки.",
    "Ты не можешь сделать 50 отжиманий? Можешь. Просто хватит быть тряпкой!",
    "Когда ты делаешь отжимания, гравитация смеётся. Когда Бог Отжиманий делает – она пишет завещание.",
    "Если ты не можешь сделать 10 отжиманий, то сделай хотя бы одно. В честь памяти о своей гордости.",
    "Кто не может сделать 50 отжиманий, тот получает +50 кг к комплексу неполноценности.",
    "Говорят бог отжиманий пока отжимался, счёт его отжиманий привысил бесконечность, дважды.",
    "Девушка бросила? Подрочи и отожмись! Работа бесит? Отожмись и подрочи! Жизнь говно? Подрочи, отожмись и подрочи ещё раз! Бог Отжиманий разрешает."
]

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
    ["Мой долг", "Добавить отжимания"], 
    ["Зарегистрироваться", "Изгнать лузера"], 
    ["Долги пацанов"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_random_quote():
    return random.choice(PUSHUP_QUOTES)

def process_pushup_quote(quote):
    match = re.search(r"долг вырос на (\d+) отжиманий", quote)
    if match:
        return int(match.group(1))
    return 0

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
        if debt > 500:
            debt_message += f"{username}: {debt} отжиманий 🪦 (рест ин пис бро...)\n"
        elif debt > 300:
            debt_message += f"{username}: {debt} отжиманий 💀 (ему почти пизда)\n"
        elif debt > 100:
            debt_message += f"{username}: {debt} отжиманий ... (аккуратнее парень. бог следит за тобой)\n"
        else:
            debt_message += f"{username}: {debt} отжиманий\n"
    
    await update.message.reply_text(debt_message)

async def handle_text(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    username = update.message.from_user.username

    if text == "Мой долг":
        if username not in data:
            await update.message.reply_text("Вы не зарегистрированы! Используйте /register.")
            return
        await update.message.reply_text(f"{username}, ваш текущий долг: {data[username]['debt']} отжиманий.")
    
    elif text == "Добавить отжимания":
        await update.message.reply_text("Введите количество отжиманий командой, например: /pushups 20")
    
    elif text == "Зарегистрироваться":
        await register(update, context)
    
    elif text == "Удалить пользователя":
        await remove(update, context)
    
    elif text == "Долги всех участников":
        await show_all_debts(update, context)

async def error_handler(update: Update, context: CallbackContext) -> None:
    logging.error(f"Произошла ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")

application = Application.builder().token("7892017077:AAGdD3LMXoTwzclDNasSpf5eutD6gm6WflM").build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("register", register))
application.add_handler(CommandHandler("remove", remove))
application.add_handler(CommandHandler("pushups", pushups))
application.add_handler(CommandHandler("status", status))
application.add_handler(CommandHandler("debts", show_all_debts))
application.add_handler(CallbackQueryHandler(confirm_remove))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.add_error_handler(error_handler)

application.run_polling()