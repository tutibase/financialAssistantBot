from aiogram.filters.state import StatesGroup, State
from aiogram import Router
from aiogram import F
import json
from aiogram.fsm.context import FSMContext
from aiogram import types
import keyboards
from aiogram.types import ReplyKeyboardRemove


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
    my_file.close()

    str_user_id = str(user_id)
    # если есть категории в файле, то добавляем их, иначе возвращаем стандартные
    if str_user_id in personal_categories:
        return default_categories + personal_categories[str_user_id]
    return default_categories


def add_category(user_id: int, message: types.Message):
    if not (message.text in available_categories(user_id)):
        # считывание категорий из файла
        with open("handlers/personal_categories.json", "r", encoding='utf-8') as my_file:
            json_categories = my_file.read()
        personal_categories = json.loads(json_categories)
        my_file.close()

        str_user_id = str(user_id)
        if str_user_id not in personal_categories:
            personal_categories[str_user_id] = [message.text]
        else:
            personal_categories[str_user_id].append(message.text)

        personal_categories_json = json.dumps(personal_categories, ensure_ascii=False)
        with open("handlers/personal_categories.json", "w", encoding='utf-8') as my_file:
             my_file.write(personal_categories_json)
        my_file.close()


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


# Хэндлер на обработку категории и переход в состояние ожидания ввода сумма
@add_purchase_router.message(AddPurchase.choosing_category, F.text)
async def category_chosen(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    add_category(user_id, message)
    await state.update_data(chosen_category=message.text.lower())
    await message.answer(
        text="Теперь введите сумму покупки или отправьте фото чека (QR-код)", reply_markup=ReplyKeyboardRemove())
    # установка состояния ввода суммы
    await state.set_state(AddPurchase.sum_input)


# Хэндлер на ввод суммы
@add_purchase_router.message(AddPurchase.sum_input, F.text)
async def text_sum_entered(message: types.Message, state: FSMContext):
    try:
        purchase_sum = abs(float(message.text))
        if purchase_sum <= 0:
            await message.answer(text="Введите сумму заново")
            return

        #добавить покупку в csv!!!!!!!!!!!!!
        await message.answer(text="Покупка добавлена",
                             reply_markup=keyboards.make_row_keyboard(["Добавить покупку","Посмотреть расходы"]))
        await state.clear()

    except ValueError:
        await message.answer(text="Введите сумму заново")
        return