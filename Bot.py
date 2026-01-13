import os
import logging
import random
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
    print("❌ ОШИБКА: Токен не найден! Проверьте настройки.")
    exit()


def main() -> None:
    application = Application.builder().token(TOKEN).build()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

(
    MAIN_MENU,
    PROBLEM_TYPE,
    PROBLEM_WHAT,
    PROBLEM_WHEN,
    PROBLEM_WHERE,
    PROBLEM_MODEL,
    INQUIRY_TYPE,
    COMPLAINT_TYPE,
    COMPLAINT_DESC,
    STATUS_CHECK
) = range(10)

def get_main_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["Подача заявки на проблему", "Справка и консультация"],
        ["Жалоба и предложение", "Проверить статус заявки"]
    ], resize_keyboard=True, one_time_keyboard=True)

async def start(update: Update, context: CallbackContext) -> int:
    """Запуск бота, показывает главное меню."""
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
        await update.message.reply_text(
            "Укажите тип проблемы:", 
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return PROBLEM_TYPE

    elif user_text == "Справка и консультация":
        keyboard = [
            ["Доступ к системам/ресурсам", "Инструкция по работе с ПО"],
            ["Информация о заказе оборудования", "Связь с живым специалистом"]
        ]
        await update.message.reply_text(
            "Выберите необходимую справку:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return INQUIRY_TYPE

    elif user_text == "Жалоба и предложение":
        keyboard = [["Жалоба на работу сервиса", "Предложения по улучшению"]]
        await update.message.reply_text(
            "Что вы хотите отправить?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return COMPLAINT_TYPE

    elif user_text == "Проверить статус заявки":
        await update.message.reply_text(
            "Введите номер вашей заявки для проверки статуса:",
            reply_markup=ReplyKeyboardRemove()
        )
        return STATUS_CHECK
    else:
        await update.message.reply_text("Пожалуйста, выберите пункт из меню.")
        return MAIN_MENU

async def problem_type_handler(update: Update, context: CallbackContext) -> int:
    context.user_data['p_type'] = update.message.text
    await update.message.reply_text(
        "Что именно происходит? Опишите симптомы.",
        reply_markup=ReplyKeyboardRemove()
    )
    return PROBLEM_WHAT

async def get_what_ask_when(update: Update, context: CallbackContext) -> int:
    context.user_data['p_what'] = update.message.text
    await update.message.reply_text("Когда началась проблема?")
    return PROBLEM_WHEN

async def get_when_ask_where(update: Update, context: CallbackContext) -> int:
    context.user_data['p_when'] = update.message.text
    await update.message.reply_text("Напишите номер помещения и рабочего места.")
    return PROBLEM_WHERE

async def get_where_ask_model(update: Update, context: CallbackContext) -> int:
    context.user_data['p_where'] = update.message.text
    await update.message.reply_text("Укажите модель оборудования (или инвентарный номер).")
    return PROBLEM_MODEL

async def problem_finish(update: Update, context: CallbackContext) -> int:
    """Финал заявки: отчет и возврат в меню."""
    context.user_data['p_model'] = update.message.text
    data = context.user_data
    
    ticket_num = random.randint(10000, 99999)
    
    report = (
        f"✅ **Заявка №{ticket_num} принята!**\n\n"
        f"📂 Тип: {data.get('p_type')}\n"
        f"❓ Суть: {data.get('p_what')}\n"
        f"⏰ Время: {data.get('p_when')}\n"
        f"📍 Место: {data.get('p_where')}\n"
        f"💻 Оборудование: {data.get('p_model')}\n\n"
        f"ℹ️ Сохраните номер: {ticket_num}"
    )

    await update.message.reply_text(report, parse_mode='Markdown')
    
    await update.message.reply_text(
        "Вы вернулись в главное меню. Чем еще могу помочь?",
        reply_markup=get_main_menu_keyboard()
    )
    
    return MAIN_MENU

async def inquiry_finish(update: Update, context: CallbackContext) -> int:
    choice = update.message.text
    if "специалистом" in choice:
        msg = "Оператор скоро подключится к этому чату. Ожидайте."
    else:
        msg = f"Информация по теме '{choice}' отправлена на почту."
        
    await update.message.reply_text(msg)
    
    await update.message.reply_text(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

async def complaint_type_handler(update: Update, context: CallbackContext) -> int:
    context.user_data['c_type'] = update.message.text
    await update.message.reply_text(
        "Опишите суть жалобы или предложения подробно.", 
        reply_markup=ReplyKeyboardRemove()
    )
    return COMPLAINT_DESC

async def complaint_finish(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Спасибо! Ваше обращение зафиксировано.")
    
    await update.message.reply_text(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

async def status_check_handler(update: Update, context: CallbackContext) -> int:
    ticket = update.message.text
    await update.message.reply_text(
        f"Статус заявки №{ticket}: 🛠 **В работе**",
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Действие отменено.", 
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

def main() -> None:
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("❌ ОШИБКА: Вы забыли вставить токен!")
        return

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
            INQUIRY_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, inquiry_finish)],
            COMPLAINT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, complaint_type_handler)],
            COMPLAINT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, complaint_finish)],
            STATUS_CHECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, status_check_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    print("🤖 Бот запускается...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
