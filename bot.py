import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import init_db, add_booking, get_all_bookings

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

SERVICES = {
    "haircut": "✂️ Стрижка",
    "beard": "🧔 Моделирование бороды",
    "manicure": "💅 Маникюр",
    "pedicure": "🦶 Педикюр",
}

TIMES = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]


class Booking(StatesGroup):
    date = State()
    time = State()
    name = State()
    phone = State()


def services_keyboard():
    builder = InlineKeyboardBuilder()
    for key, name in SERVICES.items():
        builder.button(text=name, callback_data=f"service_{key}")
    builder.adjust(1)
    return builder.as_markup()


def dates_keyboard():
    builder = InlineKeyboardBuilder()
    today = datetime.now()
    for i in range(7):
        day = today + timedelta(days=i)
        builder.button(
            text=day.strftime("%d.%m"),
            callback_data=f"date_{day.strftime('%d.%m.%Y')}",
        )
    builder.adjust(3)
    return builder.as_markup()


def times_keyboard():
    builder = InlineKeyboardBuilder()
    for t in TIMES:
        builder.button(text=t, callback_data=f"time_{t}")
    builder.adjust(3)
    return builder.as_markup()


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать в салон красоты «Beauty»! 💇\n\n"
        "Я помогу записаться онлайн за минуту.\n"
        "Выберите услугу:",
        reply_markup=services_keyboard(),
    )


@dp.message(Command("bookings"))
async def show_bookings(message: Message):
    if str(message.from_user.id) != str(OWNER_ID):
        await message.answer("Эта команда доступна только администратору.")
        return

    rows = get_all_bookings()
    if not rows:
        await message.answer("Записей пока нет.")
        return

    text = "📋 Все записи:\n\n"
    for r in rows:
        text += (
            f"#{r[0]} — {r[3]}\n"
            f"🗓 {r[4]} в {r[5]}\n"
            f"👤 {r[1]}, 📞 {r[2]}\n\n"
        )
    await message.answer(text)


@dp.callback_query(F.data.startswith("service_"))
async def service_chosen(callback: CallbackQuery, state: FSMContext):
    key = callback.data.replace("service_", "")
    service_name = SERVICES.get(key)
    await state.update_data(service=service_name)
    await state.set_state(Booking.date)
    await callback.message.answer(
        f"Услуга: {service_name}\n\nВыберите дату:",
        reply_markup=dates_keyboard(),
    )
    await callback.answer()


@dp.callback_query(Booking.date, F.data.startswith("date_"))
async def date_chosen(callback: CallbackQuery, state: FSMContext):
    date = callback.data.replace("date_", "")
    await state.update_data(date=date)
    await state.set_state(Booking.time)
    await callback.message.answer(
        f"Дата: {date}\n\nВыберите время:",
        reply_markup=times_keyboard(),
    )
    await callback.answer()


@dp.callback_query(Booking.time, F.data.startswith("time_"))
async def time_chosen(callback: CallbackQuery, state: FSMContext):
    time = callback.data.replace("time_", "")
    await state.update_data(time=time)
    await state.set_state(Booking.name)
    await callback.message.answer("Как вас зовут? Напишите имя:")
    await callback.answer()


@dp.message(Booking.name)
async def name_entered(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Booking.phone)
    await message.answer("Укажите ваш номер телефона:")


@dp.message(Booking.phone)
async def phone_entered(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()

    add_booking(data["name"], data["phone"], data["service"], data["date"], data["time"])

    await message.answer(
        "✅ Вы успешно записаны!\n\n"
        f"Услуга: {data['service']}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n\n"
        "Ждём вас! Чтобы записаться снова — нажмите /start"
    )

    if OWNER_ID:
        await bot.send_message(
            OWNER_ID,
            "🔔 Новая запись!\n\n"
            f"Услуга: {data['service']}\n"
            f"Дата: {data['date']}\n"
            f"Время: {data['time']}\n"
            f"Имя: {data['name']}\n"
            f"Телефон: {data['phone']}"
        )

    await state.clear()


async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())