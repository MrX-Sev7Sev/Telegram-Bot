import os
import logging
import uuid
import re
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("Error: BOT_TOKEN not found in .env")
    exit()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

MOCK_DATABASE = {}

(
    MAIN_MENU,
    PROBLEM_TYPE,
    PROBLEM_WHAT,
    PROBLEM_WHEN,
    PROBLEM_WHERE,
    PROBLEM_MODEL,
    INQUIRY_TYPE,
    INQUIRY_EMAIL,
    COMPLAINT_TYPE,
    COMPLAINT_DESC,
    STATUS_CHECK
) = range(11)

def load_bad_words(filename="banlist.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        return ["хуй", "пизд", "бля", "еба", "сук", "муд", "хер", "говно", "залуп", "гандон"]

BAD_WORDS = load_bad_words()

VALID_TIME_KEYWORDS = [
    "сегодня", "две недели назад", "три недели назад", "месяц назад", "вчера", "позавчера", "на прошлой неделе", 
    "утром", "вечером", "днем", "ночью", "сейчас", "давно"
]

def validate_text(text: str) -> tuple[bool, str]:
    text_lower = text.lower()
    
    replacements = {
        'a': 'а', 'b': 'ь', 'e': 'е', 'k': 'к', 'm': 'м', 'h': 'н', 'o': 'о', 'p': 'р', 
        'c': 'с', 't': 'т', 'y': 'у', 'x': 'х', '0': 'о', '3': 'з'
    }
    for eng, rus in replacements.items():
        text_lower = text_lower.replace(eng, rus)

    for bad_word in BAD_WORDS:
        if bad_word in text_lower:
            return False, "⚠️ Обнаружена ненормативная лексика. Пожалуйста, выражайтесь корректно."

    special_chars = re.findall(r'[^\w\s]', text)
    if len(text) > 5 and len(special_chars) / len(text) > 0.4:
         return False, "⚠️ Слишком много спецсимволов."

    return True, ""

def validate_date(text: str) -> bool:
    text_lower = text.lower().strip()
    
    for kw in VALID_TIME_KEYWORDS:
        if kw in text_lower:
            return True
            
    date_pattern = r'\b\d{1,2}[./-]\d{1,2}'
    if re.search(date_pattern, text):
        return True
        
    return False

def validate_email(text: str) -> bool:
    return "@" in text and "." in text and len(text) > 5

def get_main_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["Подача заявки на проблему", "Справка и консультация"],
        ["Жалоба и предложение", "Проверить статус заявки"]
    ], resize_keyboard=True, one_time_keyboard=True)

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "👋 Здравствуйте! Это бот Сервисного Центра.\n"
        "Пожалуйста, выберите тип обращения:",
        reply_markup=get_main_menu_keyboard(),
    )
    return MAIN_MENU

async def main_menu_handler(update: Update, context: CallbackContext) -> int:
    user_text = update.message.text
    
    if user_text == "Подача заявки на проблему":
        keyboard = [
            ["Аппаратная проблема", "Программная проблема"],
            ["Сетевая проблема", "Другое"]
        ]
        await update.message.reply_text("Укажите тип проблемы:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
        return PROBLEM_TYPE

    elif user_text == "Справка и консультация":
        keyboard = [
            ["Доступ к системам/ресурсам", "Инструкция по работе с ПО"],
            ["Информация о заказе оборудования", "Связь с живым специалистом"]
        ]
        await update.message.reply_text("Выберите тему:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
        return INQUIRY_TYPE

    elif user_text == "Жалоба и предложение":
        keyboard = [["Жалоба на работу сервиса", "Предложения по улучшению"]]
        await update.message.reply_text("Что вы хотите отправить?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
        return COMPLAINT_TYPE

    elif user_text == "Проверить статус заявки":
        await update.message.reply_text("Введите номер вашей заявки для проверки статуса:", reply_markup=ReplyKeyboardRemove())
        return STATUS_CHECK
    else:
        await update.message.reply_text("Пожалуйста, выберите пункт из меню.", reply_markup=get_main_menu_keyboard())
        return MAIN_MENU

async def problem_type_handler(update: Update, context: CallbackContext) -> int:
    context.user_data['p_type'] = update.message.text
    await update.message.reply_text("Что именно происходит? Опишите симптомы.", reply_markup=ReplyKeyboardRemove())
    return PROBLEM_WHAT

async def get_what_ask_when(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    
    is_valid, error_msg = validate_text(text)
    if not is_valid:
        await update.message.reply_text(error_msg)
        return PROBLEM_WHAT

    context.user_data['p_what'] = text
    await update.message.reply_text("Когда началась проблема? (Например: 'сегодня', 'вчера' или '15.01')")
    return PROBLEM_WHEN

async def get_when_ask_where(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    
    if not validate_date(text):
        await update.message.reply_text("⚠️ Непонятная дата. Напишите 'вчера', 'сегодня' или дату в формате ДД.ММ")
        return PROBLEM_WHEN

    context.user_data['p_when'] = text
    await update.message.reply_text("Напишите номер помещения и рабочего места.")
    return PROBLEM_WHERE

async def get_where_ask_model(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    
    is_valid, error_msg = validate_text(text)
    if not is_valid:
        await update.message.reply_text(error_msg)
        return PROBLEM_WHERE

    context.user_data['p_where'] = text
    await update.message.reply_text("Укажите модель оборудования (или инвентарный номер).")
    return PROBLEM_MODEL

async def problem_finish(update: Update, context: CallbackContext) -> int:
    context.user_data['p_model'] = update.message.text
    data = context.user_data
    
    ticket_num = str(uuid.uuid4())[:8].upper()
    
    MOCK_DATABASE[ticket_num] = {
        "status": "В работе",
        "type": data.get('p_type'),
        "desc": data.get('p_what')
    }

    report = (
        f"✅ **Заявка №{ticket_num} создана!**\n\n"
        f"📂 Тип: {data.get('p_type')}\n"
        f"❓ Суть: {data.get('p_what')}\n"
        f"⏰ Время: {data.get('p_when')}\n"
        f"📍 Место: {data.get('p_where')}\n"
        f"💻 Оборудование: {data.get('p_model')}\n\n"
        f"ℹ️ Сохраните номер для проверки статуса."
    )

    await update.message.reply_text(report, parse_mode='Markdown')
    await update.message.reply_text("Главное меню:", reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

async def inquiry_type_handler(update: Update, context: CallbackContext) -> int:
    choice = update.message.text
    context.user_data['i_choice'] = choice
    
    if "специалистом" in choice:
        await update.message.reply_text("Оператор скоро подключится к диалогу. Ожидайте.")
        await update.message.reply_text("Главное меню:", reply_markup=get_main_menu_keyboard())
        return MAIN_MENU
    else:
        await update.message.reply_text("Введите ваш Email для получения инструкции:", reply_markup=ReplyKeyboardRemove())
        return INQUIRY_EMAIL

async def inquiry_email_handler(update: Update, context: CallbackContext) -> int:
    email = update.message.text
    
    if not validate_email(email):
        await update.message.reply_text("⚠️ Некорректный Email. Попробуйте еще раз (нужен символ @ и точка).")
        return INQUIRY_EMAIL

    choice = context.user_data.get('i_choice')
    await update.message.reply_text(f"✅ Инструкция по теме '{choice}' отправлена на **{email}**.", parse_mode='Markdown')
    await update.message.reply_text("Главное меню:", reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

async def complaint_type_handler(update: Update, context: CallbackContext) -> int:
    context.user_data['c_type'] = update.message.text
    await update.message.reply_text("Опишите суть подробно.", reply_markup=ReplyKeyboardRemove())
    return COMPLAINT_DESC

async def complaint_finish(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    
    is_valid, error_msg = validate_text(text)
    if not is_valid:
        await update.message.reply_text(error_msg)
        return COMPLAINT_DESC

    await update.message.reply_text("Спасибо! Ваше обращение зафиксировано.")
    await update.message.reply_text("Главное меню:", reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

async def status_check_handler(update: Update, context: CallbackContext) -> int:
    ticket = update.message.text.strip().upper()
    
    if ticket in MOCK_DATABASE:
        status = MOCK_DATABASE[ticket]['status']
        desc = MOCK_DATABASE[ticket]['desc']
        await update.message.reply_text(
            f"🎫 **Заявка №{ticket}**\n"
            f"Статус: 🛠 **{status}**\n"
            f"Проблема: {desc}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Заявка №{ticket} не найдена.\n"
            "Возможно, номер указан неверно, либо заявка архивирована (база данных обновляется раз в сутки).",
        )
    
    await update.message.reply_text("Главное меню:", reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Действие отменено.", reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, start)
        ],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            PROBLEM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, problem_type_handler)],
            PROBLEM_WHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_what_ask_when)],
            PROBLEM_WHEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_when_ask_where)],
            PROBLEM_WHERE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_where_ask_model)],
            PROBLEM_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, problem_finish)],
            INQUIRY_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, inquiry_type_handler)],
            INQUIRY_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, inquiry_email_handler)],
            COMPLAINT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, complaint_type_handler)],
            COMPLAINT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, complaint_finish)],
            STATUS_CHECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, status_check_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    print("🤖 Bot is running...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
