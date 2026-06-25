import asyncio
import logging
import os
import random
import sys
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from messages import MESSAGES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "8942879472:AAEMVoZX0h5IoJOVigEPlJ-rkWXwBNQrD7E",
)

_user_id_raw = os.getenv("USER_CHAT_ID", "1153500999")
ALLOWED_USER_ID = int(_user_id_raw) if _user_id_raw else 1153500999


def get_msk_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Moscow")
    except Exception:
        logger.warning("tzdata не найдена, используем UTC+3")
        return timezone(timedelta(hours=3))


MSK = get_msk_tz()
SCHEDULE_HOURS = (10, 16, 20)
WISH_BUTTON = "💕 Пожелание"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=MSK)

sent_today: set[str] = set()
last_reset_date: str = ""


def wish_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=WISH_BUTTON)
    return builder.as_markup(resize_keyboard=True)


def is_allowed(user_id: int) -> bool:
    return user_id == ALLOWED_USER_ID


def pick_message() -> str:
    global sent_today, last_reset_date

    today = datetime.now(MSK).strftime("%Y-%m-%d")
    if today != last_reset_date:
        sent_today = set()
        last_reset_date = today

    available = [m for m in MESSAGES if m not in sent_today]
    if not available:
        sent_today = set()
        available = MESSAGES

    message = random.choice(available)
    sent_today.add(message)
    return message


async def send_sweet_message() -> None:
    text = pick_message()
    try:
        await bot.send_message(
            chat_id=ALLOWED_USER_ID,
            text=text,
            reply_markup=wish_keyboard(),
        )
        logger.info("Отправлено: %s", text[:50])
    except Exception:
        logger.exception("Не удалось отправить сообщение")


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if not is_allowed(message.from_user.id):
        return

    await message.answer(
        "Привет, милая! 👋\n\n"
        "Я — твой бот с пожеланиями. Буду присылать тёплые и "
        "мотивационные сообщения в 10:00, 16:00 и 20:00 по МСК 💕\n\n"
        "А если захочешь пожелание прямо сейчас — нажми кнопку ниже!",
        reply_markup=wish_keyboard(),
    )


@dp.message(F.text == WISH_BUTTON)
async def wish_on_button(message: Message) -> None:
    if not is_allowed(message.from_user.id):
        return

    await message.answer(pick_message(), reply_markup=wish_keyboard())


async def main() -> None:
    logger.info("Запуск бота...")
    logger.info("Python: %s", sys.version.replace("\n", " "))
    logger.info("Токен задан: %s", bool(BOT_TOKEN))
    logger.info("Пользователь: %d", ALLOWED_USER_ID)

    for hour in SCHEDULE_HOURS:
        scheduler.add_job(
            send_sweet_message,
            CronTrigger(hour=hour, minute=0, timezone=MSK),
        )

    scheduler.start()
    logger.info(
        "Бот запущен. Пользователь: %d. Пожеланий: %d. Расписание: %s:00 МСК",
        ALLOWED_USER_ID,
        len(MESSAGES),
        ", ".join(map(str, SCHEDULE_HOURS)),
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        logger.exception("Бот остановлен с ошибкой")
        raise
