from aiogram.filters.command import Command
from aiogram import html
from aiogram import Router
from aiogram import types
from keyboards import make_row_keyboard

start_router = Router()
start_list = ["Добавить покупку", "Посмотреть расходы"]
default_categories = ["Продукты", "Транспорт", "Медицина", "Одежда"]


# Хэндлер на команду /start
@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Здравствуйте, {html.quote(message.from_user.full_name)}!",
                         reply_markup=make_row_keyboard(start_list))


