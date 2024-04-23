from aiogram import html
from aiogram import types
from keyboards import make_row_keyboard
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

default_router = Router()
start_list = ["Добавить покупку", "Посмотреть расходы"]
default_categories = ["Продукты", "Транспорт", "Медицина", "Одежда"]
available_periods = ["Последний год","Последний месяц","Конкретный период","Конкретная дата"]

# Хэндлер на команду /start
@default_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Здравствуйте, {html.quote(message.from_user.full_name)}!",
                         reply_markup=make_row_keyboard(start_list))


# Хэндлер на выход из автомата состояний
@default_router.message(StateFilter(None), Command(commands=["cancel"]))
@default_router.message(default_state, F.text.lower() == "отмена")
async def cmd_cancel_no_state(message: Message, state: FSMContext):
    # Стейт сбрасывать не нужно, удалим только данные
    await state.set_data({})
    await message.answer(text="Нечего отменять",
                         reply_markup=make_row_keyboard(start_list))


# Хэндлер на выход из автомата состояний 2
@default_router.message(Command(commands=["cancel"]))
@default_router.message(F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text="Действие отменено",
                         reply_markup=make_row_keyboard(start_list))
