from aiogram.filters.state import  StatesGroup, State
from aiogram import Router
from aiogram import F
import json
from aiogram.fsm.context import FSMContext
from aiogram import types
import keyboards


class AddPurchase(StatesGroup):
    """класс состояний для конечного автомата добавления покупки"""
    choosing_category = State()
    sum_input = State()


def available_categories(user_id: int) -> list:
    """
    Список категорий конкретного пользователя (стандартные категории + введенные им ранее, хранящиеся в файле)
    :param user_id: Telegram id пользователя
    :return: Список категорий пользователя
    """
    default_categories = ["Продукты", "Транспорт", "Медицина", "Одежда"]

    # считывание категорий из файла
    with open("handlers/personal_categories.json", "r", encoding='utf-8') as my_file:
        json_categories = my_file.read()
    personal_categories = json.loads(json_categories)

    # если есть категории в файле, то добавляем их, иначе возвращаем стандартные
    if user_id in personal_categories:
        return default_categories + personal_categories[user_id]
    return default_categories


# создание роутера для связи диспетчера и хэндлеров
add_purchase_router = Router()


# Хэндлер на первый шаг к добавлению покупки
@add_purchase_router.message(F.text == "Добавить покупку")
async def choose_category(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    # создание клавиатуры с доступными категориями и предложение выбрать одну из них
    await message.answer(text="Выберите категорию или введите новую: ",
                         reply_markup=keyboards.make_categories_keyboard(available_categories(user_id)))
    # установка состояния выбора категории
    await state.set_state(AddPurchase.choosing_category)
