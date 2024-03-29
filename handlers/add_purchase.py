from aiogram.filters.state import  StatesGroup, State
from aiogram import Router
from aiogram import F
import json
from aiogram.fsm.context import FSMContext
from aiogram import types
import keyboards

class AddPurchase(StatesGroup):
    choosing_category = State()
    sum_input = State()


def available_categories(user_id: int) -> list:
    default_categories = ["Продукты", "Транспорт", "Медицина", "Одежда"]
    with open("personal_categories.json", "r", encoding='utf-8') as my_file:
        json_categories = my_file.read()

    personal_categories = json.loads(json_categories)
    return default_categories + personal_categories[user_id]


add_purchase_router = Router()


# Хэндлер на команду /add_purchase
@add_purchase_router.message(F.text == "Добавить покупку")
async def choose_category(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await message.answer(text="Выберите категорию или введите новую: ",
                         reply_markup=keyboards.make_categories_keyboard(available_categories(user_id)))

    await state.set_state(AddPurchase.choosing_category)
