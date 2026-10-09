"""Telegram-бот: тот же Оракул, но в мессенджере. Запускается на вашем компьютере."""

import asyncio
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters,
)

from . import config
from .astro import Profile, parse_birth_date
from .service import Oracle

NAME, BIRTH, MENU, QUESTION, CHAT = range(5)

BTN_HOROSCOPE = "🌟 Гороскоп на сегодня"
BTN_DAY = "🃏 Карта дня"
BTN_THREE = "⏳ Прошлое-настоящее-будущее"
BTN_LOVE = "❤️ Любовный расклад"
BTN_QUESTION = "❓ Вопрос картам"
BTN_CHAT = "💬 Чат с Оракулом"
BTN_PROFILE = "👤 Мой профиль"
BTN_BACK = "↩️ В меню"

MENU_KEYBOARD = ReplyKeyboardMarkup(
    [[BTN_HOROSCOPE, BTN_DAY], [BTN_THREE, BTN_LOVE], [BTN_QUESTION, BTN_CHAT], [BTN_PROFILE]],
    resize_keyboard=True,
)
BACK_KEYBOARD = ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True)

SPREAD_BY_BUTTON = {BTN_DAY: "day", BTN_THREE: "three", BTN_LOVE: "love"}


async def send_long(update: Update, text: str, keyboard=MENU_KEYBOARD) -> None:
    """Telegram ограничивает сообщение 4096 символами — режем по абзацам."""
    chunks, current = [], ""
    for para in text.split("\n"):
        if len(current) + len(para) + 1 > 4000:
            chunks.append(current)
            current = ""
        current += para + "\n"
    chunks.append(current)
    for chunk in filter(str.strip, chunks):
        await update.message.reply_text(chunk, reply_markup=keyboard)


async def run_blocking(update: Update, func, *args):
    """Запрос к ИИ идёт в отдельном потоке, пока бот показывает «печатает...»."""
    await update.message.chat.send_action(ChatAction.TYPING)
    task = asyncio.create_task(asyncio.to_thread(func, *args))
    while not task.done():
        await asyncio.sleep(4)
        if not task.done():
            await update.message.chat.send_action(ChatAction.TYPING)
    return task.result()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "✨ Здравствуйте! Я Оракул — гадаю на картах Таро и составляю гороскопы.\n\n"
        "Как вас зовут?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()[:50]
    await update.message.reply_text("Введите дату рождения в формате ДД.ММ.ГГГГ (например, 14.03.1995):")
    return BIRTH


async def got_birth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        birth = parse_birth_date(update.message.text)
    except ValueError as e:
        await update.message.reply_text(f"{e}. Попробуйте ещё раз:")
        return BIRTH
    oracle = Oracle(Profile(context.user_data["name"], birth))
    context.user_data["oracle"] = oracle
    sign, symbol, *_ = oracle.profile.zodiac
    await update.message.reply_text(
        f"Рад знакомству, {oracle.profile.name}! Ваш знак — {symbol} {sign}.\nЧто хотите узнать?",
        reply_markup=MENU_KEYBOARD,
    )
    return MENU


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    oracle: Oracle | None = context.user_data.get("oracle")
    if oracle is None:
        return await start(update, context)
    text = update.message.text

    if text == BTN_HOROSCOPE:
        await send_long(update, await run_blocking(update, oracle.horoscope))
    elif text in SPREAD_BY_BUTTON:
        cards, reading = await run_blocking(update, oracle.tarot, SPREAD_BY_BUTTON[text])
        cards_line = "\n".join(f"🃏 {c.position}: {c.title}" for c in cards)
        await send_long(update, f"{cards_line}\n\n{reading}" if oracle.uses_ai else reading)
    elif text == BTN_QUESTION:
        await update.message.reply_text("Задайте свой вопрос картам:", reply_markup=BACK_KEYBOARD)
        return QUESTION
    elif text == BTN_CHAT:
        await update.message.reply_text(
            "Спрашивайте Оракула о чём угодно. Чтобы вернуться, нажмите «В меню».",
            reply_markup=BACK_KEYBOARD,
        )
        return CHAT
    elif text == BTN_PROFILE:
        await update.message.reply_text(oracle.profile.summary(), reply_markup=MENU_KEYBOARD)
    else:
        await update.message.reply_text("Выберите пункт меню 👇", reply_markup=MENU_KEYBOARD)
    return MENU


async def question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_BACK:
        await update.message.reply_text("Меню:", reply_markup=MENU_KEYBOARD)
        return MENU
    oracle: Oracle = context.user_data["oracle"]
    cards, reading = await run_blocking(update, oracle.tarot, "question", update.message.text)
    cards_line = "\n".join(f"🃏 {c.position}: {c.title}" for c in cards)
    await send_long(update, f"{cards_line}\n\n{reading}" if oracle.uses_ai else reading)
    return MENU


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_BACK:
        await update.message.reply_text("Меню:", reply_markup=MENU_KEYBOARD)
        return MENU
    oracle: Oracle = context.user_data["oracle"]
    await send_long(update, await run_blocking(update, oracle.chat, update.message.text), BACK_KEYBOARD)
    return CHAT


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    if not config.TELEGRAM_TOKEN:
        raise SystemExit("Не задан TELEGRAM_BOT_TOKEN. Получите токен у @BotFather и добавьте в .env")
    if not config.ai_available():
        logging.warning("ANTHROPIC_API_KEY не задан — бот работает без ИИ")

    text = filters.TEXT & ~filters.COMMAND
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(text, menu)],
        states={
            NAME: [MessageHandler(text, got_name)],
            BIRTH: [MessageHandler(text, got_birth)],
            MENU: [MessageHandler(text, menu)],
            QUESTION: [MessageHandler(text, question)],
            CHAT: [MessageHandler(text, chat)],
        },
        fallbacks=[CommandHandler("start", start)],
    ))
    logging.info("Оракул запущен. Откройте бота в Telegram и отправьте /start")
    app.run_polling()


if __name__ == "__main__":
    main()
