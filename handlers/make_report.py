from aiogram.filters.state import StatesGroup, State
from aiogram import Router
from aiogram import F
import json
from aiogram.fsm.context import FSMContext
from aiogram import types
import keyboards
from aiogram.types import ReplyKeyboardRemove
from handlers.default import available_periods, start_list
from handlers.add_purchase import available_categories
from datetime import datetime, timedelta
import pandas as pd

class MakeReport(StatesGroup):
    """класс состояний для конечного автомата создания отчета"""
    choosing_period = State()
    choosing_category = State()
    specific_period_input = State()
    specific_date_input = State()


# создание роутера для связи диспетчера и хэндлеров
make_report_router = Router()


# Хэндлер на первый шаг к просмотру расходов
@make_report_router.message(F.text == "Посмотреть расходы")
async def choose_period(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    # создание клавиатуры с доступными категориями и предложение выбрать одну из них
    await message.answer(text="Выберите период: ",
                         reply_markup=keyboards.make_2col_keyboard(available_periods))
    # установка состояния выбора периода
    await state.set_state(MakeReport.choosing_period)


# Хэндлер на обработку конкретного периода и переход в состояние ожидания ввода периода
@make_report_router.message(MakeReport.choosing_period, F.text == "Конкретный период")
async def specific_period_chosen(message: types.Message, state: FSMContext):
    await message.answer(
        text="Введите дату начала периода в формате дд.мм.гггг :)", reply_markup=ReplyKeyboardRemove())
    # установка состояния ввода периода
    await state.set_state(MakeReport.specific_period_input)


# Хэндлер на обработку конкретной даты и переход в состояние ожидания ввода даты
@make_report_router.message(MakeReport.choosing_period, F.text == "Конкретная дата")
async def specific_date_chosen(message: types.Message, state: FSMContext):
    await message.answer(
        text="Введите дату в формате дд.мм.гггг :)", reply_markup=ReplyKeyboardRemove())
    # установка состояния ввода даты
    await state.set_state(MakeReport.specific_date_input)


# Хэндлер на обработку последнего года и переход в состояние ожидания ввода категории
@make_report_router.message(MakeReport.choosing_period, F.text == "Последний год")
async def last_year_chosen(message: types.Message, state: FSMContext):
    start = datetime.today()
    finish = start - timedelta(days=365)
    await state.update_data(first_date=start)
    await state.update_data(second_date=finish)
    user_id = message.from_user.id
    listik = ["Все категории"] + available_categories(user_id)
    await message.answer(
        text="Выберите категорию: ", reply_markup=keyboards.make_2col_keyboard(listik))
    await state.set_state(MakeReport.choosing_category)
    await state.update_data(available_categories=listik)


# Хэндлер на обработку последнего месяца и переход в состояние ожидания ввода категории
@make_report_router.message(MakeReport.choosing_period, F.text == "Последний месяц")
async def last_month_chosen(message: types.Message, state: FSMContext):
    start = datetime.today()
    finish = start - timedelta(days=30)
    await state.update_data(first_date=start)
    await state.update_data(second_date=finish)
    user_id = message.from_user.id
    listik = ["Все категории"] + available_categories(user_id)
    await message.answer(
        text="Выберите категорию: ", reply_markup=keyboards.make_2col_keyboard(listik))
    await state.set_state(MakeReport.choosing_category)
    await state.update_data(available_categories=listik)

# Хэндлер на ввод конкретного периода
@make_report_router.message(MakeReport.specific_period_input, F.text)
async def specific_period_entered(message: types.Message, state: FSMContext):
    try:
        date_string = message.text
        date_format = "%d.%m.%Y"
        date_obj = datetime.strptime(date_string, date_format)
        print(date_obj)

    except ValueError:
        await message.answer(text="Введите дату начала периода в формате дд.мм.гггг заново")
        return

    if 'first_date' not in await state.get_data():
        await state.update_data(first_date=date_obj)
        await message.answer(
            text="Введите дату конца периода в формате дд.мм.гггг :)")
        return

    await state.update_data(second_date=date_obj)
    user_id = message.from_user.id
    listik = ["Все категории"] + available_categories(user_id)
    await message.answer(
        text="Выберите категорию :)", reply_markup=keyboards.make_2col_keyboard(listik))
    await state.set_state(MakeReport.choosing_category)
    await state.update_data(available_categories = listik)


# Хэндлер на ввод конкретной даты
@make_report_router.message(MakeReport.specific_date_input, F.text)
async def specific_date_entered(message: types.Message, state: FSMContext):
    try:
        date_string = message.text
        date_format = "%d.%m.%Y"
        date_obj = datetime.strptime(date_string, date_format)
        print(date_obj)

    except ValueError:
        await message.answer(text="Введите дату начала периода в формате дд.мм.гггг заново")
        return

    await state.update_data(first_date=date_obj)
    await state.update_data(second_date=date_obj)
    user_id = message.from_user.id
    listik = ["Все категории"] + available_categories(user_id)
    await message.answer(
        text="Выберите категорию: ", reply_markup=keyboards.make_2col_keyboard(listik))
    await state.set_state(MakeReport.choosing_category)
    await state.update_data(available_categories=listik)


# Хэндлер на вывод отчета
@make_report_router.message(MakeReport.choosing_category, F.text)
async def make_report(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    listik = user_data['available_categories']
    if message.text not in listik:
        await message.answer(
            text="Ты дурак что ли: клавиатура для лохов сделана??????")
        return

    if message.text == 'Все категории':
        categories = user_data['available_categories']
    else:
        categories = [message.text]

    if user_data['first_date'] > user_data['second_date']:
        user_data['first_date'], user_data['second_date'] = user_data['second_date'], user_data['first_date']

    df = pd.read_csv('users_data/purchases.csv')
    df['date'] = pd.to_datetime(df['date'])
    df_filtered = df[(df['id'] == message.from_user.id) &
                     (df['date'] >= user_data['first_date']) & (df['date'] <= user_data['second_date'])]

    reply_message = 'Вот ваши траты за этот период:\n'
    for i in categories:
        category_sum = (df_filtered[df_filtered['category'] == i])['sum'].sum()
        if category_sum == 0:
            continue
        reply_message += f"{i}: {category_sum} руб. \n"

    if reply_message == 'Вот ваши траты за этот период:\n':
        reply_message = 'У вас нет трат за этот период'

    await message.answer(
        text=reply_message,
        reply_markup=keyboards.make_row_keyboard(start_list))
    # Сброс состояние диалога (выход из конечного автомата)
    await state.clear()