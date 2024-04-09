import io
from aiogram.filters.state import StatesGroup, State
from aiogram import Router
from aiogram import F
import json
from aiogram.fsm.context import FSMContext
from aiogram import types
import keyboards
from aiogram.types import ReplyKeyboardRemove
from PIL import Image
from pyzbar.pyzbar import decode
from datetime import date
from handlers.default import start_list, default_categories
import pandas as pd


class AddPurchase(StatesGroup):
    """Класс состояний для конечного автомата добавления покупки"""
    choosing_category = State()
    sum_input = State()


def available_categories(user_id: int) -> list:
    """
    Список категорий конкретного пользователя (стандартные категории + введенные им ранее, хранящиеся в файле)
    :param user_id: Telegram id пользователя
    :return: Список категорий пользователя
    """

    # Считывание категорий из файла
    with open("users_data/personal_categories.json", "r", encoding='utf-8') as my_file:
        json_categories = my_file.read()
    personal_categories = json.loads(json_categories)
    my_file.close()

    str_user_id = str(user_id)
    # Если есть категории в файле, то добавляем их, иначе возвращаем стандартные
    if str_user_id in personal_categories:
        return default_categories + personal_categories[str_user_id]
    return default_categories


def add_category(user_id: int, message: types.Message):
    """
    Добавление в общий словарь (файл) категорий пользователей новой категории
    :param user_id: Telegram id пользователя
    :param message: отправленное пользовтелем сообщение с категорией
    """

    input_category = message.text.lower()
    user_categories = available_categories(user_id)
    # Если категории нет в категориях пользователя, то добавим её
    if not (input_category in [s.lower() for s in user_categories]):
        # Считывание категорий из файла
        with open("users_data/personal_categories.json", "r", encoding='utf-8') as my_file:
            json_categories = my_file.read()
        personal_categories = json.loads(json_categories)
        my_file.close()

        # Если до этого у пользователя не было своих категорий, то создаем для него новый словарь,
        # а иначе добавляем новую категорию к старым
        str_user_id = str(user_id)
        input_category = input_category[0].upper() + input_category[1:]
        if str_user_id not in personal_categories:
            personal_categories[str_user_id] = [input_category]
        else:
            personal_categories[str_user_id].append(input_category)

        # Записываем обновленный словарь в файл
        personal_categories_json = json.dumps(personal_categories, ensure_ascii=False)
        with open("users_data/personal_categories.json", "w", encoding='utf-8') as my_file:
            my_file.write(personal_categories_json)
        my_file.close()


# Добавить проверку на отсутсвие qr-кода!!!!!
def image_processing(img: Image) -> (float, date):
    """
    Обработка фото чека с QR-кодом и получение из него информации о покупке
    :param img: объект-изображение формата библиотеки PIL
    :return: пара значений (сумма покупки, дата покупки)
    """

    decoded_list = decode(img)
    qr_text = decoded_list[0].data.decode()
    qr_date_str = qr_text[qr_text.find('t=')+2:qr_text.find('t=')+10]
    qr_date = date(int(qr_date_str[0:4]), int(qr_date_str[4:6]), int(qr_date_str[6:]))

    qr_sum = float(qr_text[qr_text.find('s=')+2:qr_text.find('&fn=')])
    return qr_sum, qr_date


def new_row_purchase(user_id: int, purchase_date: date, purchase_sum, purchase_category: str):
    """
    Функция добавления новой покупки в csv файл
    :param user_id: Telegram id пользователя int
    :param purchase_date: дата покупки datetime.date
    :param purchase_sum: сумма покупки float
    :param purchase_category: категория покупки str
    """

    # Перевод категории в слово с большой буквы
    purchase_category = purchase_category[0].upper() + purchase_category[1:]

    # Загружаем существующий файл в DataFrame
    df = pd.read_csv('users_data/purchases.csv')

    # Добавляем новую строку с записями
    new_row = pd.Series({'id': user_id, 'date': purchase_date, 'sum': purchase_sum, 'category': purchase_category})
    df = pd.concat([df, new_row.to_frame().T], ignore_index=True)

    # Сохраняем обновленный DataFrame обратно в файл
    df.to_csv('users_data/purchases.csv', index=False)


# Создание роутера для связи диспетчера и хэндлеров
add_purchase_router = Router()


# Хэндлер на первый шаг к добавлению покупки
@add_purchase_router.message(F.text == "Добавить покупку")
async def choose_category(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    # Создание клавиатуры с доступными категориями и предложение выбрать одну из них
    await message.answer(text="Выберите категорию или введите новую",
                         reply_markup=keyboards.make_categories_keyboard(available_categories(user_id)))
    # Установка состояния выбора категории
    await state.set_state(AddPurchase.choosing_category)


# Хэндлер на обработку категории и переход в состояние ожидания ввода суммы
@add_purchase_router.message(AddPurchase.choosing_category, F.text)
async def category_chosen(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    add_category(user_id, message)  # добавление категории в файл
    await state.update_data(chosen_category=message.text.lower())  # добавлении информации о категории в state
    await message.answer(text="Теперь введите сумму покупки или отправьте фото чека (QR-код)",
                         reply_markup=ReplyKeyboardRemove())
    # Установка состояния ввода суммы
    await state.set_state(AddPurchase.sum_input)


# Хэндлер на ввод суммы текстом
@add_purchase_router.message(AddPurchase.sum_input, F.text)
async def text_sum_entered(message: types.Message, state: FSMContext):
    # Проверяем корректность введенной суммы. Если успех - то добавляем новую покупку, а иначе - ожидаем новый ввод
    try:
        purchase_sum = float(message.text)
        if purchase_sum <= 0:
            await message.answer(text="Введите сумму заново")
            return

        # Получаем ранее введенную категорию
        user_data = await state.get_data()

        # Добавляем покупку в файл
        new_row_purchase(message.from_user.id, date.today(), purchase_sum, user_data['chosen_category'])

        # Сообщение об успешном добавлении
        await message.answer(
            text=f"Покупка на сумму {purchase_sum} руб. в категории {user_data['chosen_category']} добавлена",
            reply_markup=keyboards.make_row_keyboard(start_list))
        # Сброс состояние диалога (выход из конечного автомата)
        await state.clear()

    except ValueError:
        await message.answer(text="Введите сумму заново")
        return


# Хэндлер на ввод суммы через фото чека
@add_purchase_router.message(AddPurchase.sum_input, F.photo)
async def photo_sum_entered(message: types.Message, state: FSMContext):
    # Переводим фото в байты фото и создаем из них объект BytesIO, который является файлоподобным объектом.
    # Затем используем Pillow для открытия изображения из этого объекта
    photo_bytes = await message.bot.download(file=message.photo[-1].file_id, destination=io.BytesIO())
    photo_bytes.seek(0)
    image = Image.open(photo_bytes)
    qr_sum, qr_date = image_processing(image)  # Извлечение из фото суммы и даты покупки

    # Получаем ранее введенную категорию
    user_data = await state.get_data()

    # Добавляем покупку в файл
    new_row_purchase(message.from_user.id, qr_date, qr_sum, user_data['chosen_category'])

    # Сообщение об успешном добавлении
    await message.answer(text=f"Покупка на сумму {qr_sum} руб. в категории {user_data['chosen_category']} добавлена",
                         reply_markup=keyboards.make_row_keyboard(start_list))
    # Сброс состояние диалога (выход из конечного автомата)
    await state.clear()
