import logging
import random
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# --- КОНФИГУРАЦИЯ ---
# Ваш токен уже вставлен:
TOKEN = "8532099515:AAE5Y1GX4QT--Nbmkepg4g4Rdhl737zLZhM"

# Логирование (чтобы видеть ошибки в консоли)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- СОСТОЯНИЯ ДИАЛОГА (Этапы) ---
(
    MAIN_MENU,          # 0. Главное меню
    PROBLEM_TYPE,       # 1. Выбор типа проблемы
    PROBLEM_WHAT,       # 2. Вопрос: Что случилось?
    PROBLEM_WHEN,       # 3. Вопрос: Когда?
    PROBLEM_WHERE,      # 4. Вопрос: Где?
    PROBLEM_MODEL,      # 5. Вопрос: Модель?
    INQUIRY_TYPE,       # 6. Тип справки
    COMPLAINT_TYPE,     # 7. Тип жалобы
    COMPLAINT_DESC,     # 8. Описание жалобы
    STATUS_CHECK        # 9. Проверка статуса
) = range(10)

# --- ФУНКЦИИ: СТАРТ И МЕНЮ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запуск бота, показывает главное меню."""
    keyboard = [
        ["Подача заявки на проблему", "Справка и консультация"],
        ["Жалоба и предложение", "Проверить статус заявки"]
    ]
    await update.message.reply_text(
        "👋 Здравствуйте! Это бот Сервисного Центра.\n"
        "Пожалуйста, выберите тип обращения:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Распределяет по веткам в зависимости от нажатой кнопки."""
    user_text = update.message.text
    
    # Ветка 1: Проблемы
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

    # Ветка 2: Справки
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

    # Ветка 3: Жалобы
    elif user_text == "Жалоба и предложение":
        keyboard = [["Жалоба на работу сервиса", "Предложения по улучшению"]]
        await update.message.reply_text(
            "Что вы хотите отправить?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return COMPLAINT_TYPE

    # Ветка 4: Статус
    elif user_text == "Проверить статус заявки":
        await update.message.reply_text(
            "Введите номер вашей заявки для проверки статуса:",
            reply_markup=ReplyKeyboardRemove()
        )
        return STATUS_CHECK
    else:
        await update.message.reply_text("Пожалуйста, выберите пункт из меню.")
        return MAIN_MENU

# --- ВЕТКА 1: ОФОРМЛЕНИЕ ЗАЯВКИ (ПОШАГОВО) ---

async def problem_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запоминаем тип, спрашиваем СУТЬ."""
    context.user_data['p_type'] = update.message.text
    await update.message.reply_text(
        "Что именно происходит? Опишите симптомы.",
        reply_markup=ReplyKeyboardRemove()
    )
    return PROBLEM_WHAT

async def get_what_ask_when(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запоминаем суть, спрашиваем ВРЕМЯ."""
    context.user_data['p_what'] = update.message.text
    await update.message.reply_text("Когда началась проблема?")
    return PROBLEM_WHEN

async def get_when_ask_where(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запоминаем время, спрашиваем МЕСТО."""
    context.user_data['p_when'] = update.message.text
    await update.message.reply_text("Напишите номер помещения и рабочего места.")
    return PROBLEM_WHERE

async def get_where_ask_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запоминаем место, спрашиваем МОДЕЛЬ."""
    context.user_data['p_where'] = update.message.text
    await update.message.reply_text("Укажите модель оборудования (или инвентарный номер).")
    return PROBLEM_MODEL

async def problem_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Финал заявки: генерация номера и отчет."""
    context.user_data['p_model'] = update.message.text
    data = context.user_data
    
    # Генерируем случайный номер заявки
    ticket_num = random.randint(10000, 99999)
    
    sla_info = (
        "\n🕒 **Время реакции сервиса:**\n"
        "- Критические проблемы: до 2 часов\n"
        "- Стандартные проблемы: до 24 часов"
    )
    
    report = (
        f"✅ **Заявка №{ticket_num} принята!**\n\n"
        f"📂 Тип: {data.get('p_type')}\n"
        f"❓ Суть: {data.get('p_what')}\n"
        f"⏰ Время начала: {data.get('p_when')}\n"
        f"📍 Место: {data.get('p_where')}\n"
        f"💻 Оборудование: {data.get('p_model')}\n"
        f"{sla_info}\n\n"
        f"ℹ️ *Сохраните номер заявки ({ticket_num}) для отслеживания.*"
    )

    await update.message.reply_text(report, parse_mode='Markdown')
    return ConversationHandler.END

# --- ВЕТКА 2: СПРАВКИ ---

async def inquiry_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if "специалистом" in choice:
        msg = "Оператор скоро подключится к этому чату. Ожидайте."
    else:
        msg = f"Информация по теме '{choice}' отправлена на вашу корпоративную почту."
        
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- ВЕТКА 3: ЖАЛОБЫ ---

async def complaint_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['c_type'] = update.message.text
    await update.message.reply_text(
        "Опишите суть жалобы или предложения подробно.", 
        reply_markup=ReplyKeyboardRemove()
    )
    return COMPLAINT_DESC

async def complaint_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Спасибо! Ваше обращение зафиксировано и передано руководству.", 
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# --- ВЕТКА 4: СТАТУС ---

async def status_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ticket = update.message.text
    # Здесь эмуляция. В реальности был бы запрос к базе данных.
    await update.message.reply_text(
        f"Статус заявки №{ticket}: 🛠 **В работе**\n"
        "Инженер уже занимается вашей проблемой.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# --- ОТМЕНА ---

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Действие отменено. Напишите /start чтобы начать заново.", 
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# --- ЗАПУСК ПРИЛОЖЕНИЯ ---

def main() -> None:
    # Создаем приложение с вашим токеном
    application = Application.builder().token(TOKEN).build()

    # Настраиваем логику диалогов
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # Главное меню
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            
            # Ветка проблем (цепочка вопросов)
            PROBLEM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, problem_type_handler)],
            PROBLEM_WHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_what_ask_when)],
            PROBLEM_WHEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_when_ask_where)],
            PROBLEM_WHERE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_where_ask_model)],
            PROBLEM_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, problem_finish)],
            
            # Ветка справок
            INQUIRY_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, inquiry_finish)],
            
            # Ветка жалоб
            COMPLAINT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, complaint_type_handler)],
            COMPLAINT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, complaint_finish)],
            
            # Ветка статуса
            STATUS_CHECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, status_check_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()

if __name__ == "__main__":
    main()
