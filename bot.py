import config
import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers import default, add_purchase

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=config.token, parse_mode="HTML")
# Диспетчер
dp = Dispatcher()
# связь диспетчера и роутеров (связь диспетчер — роутеры — хэндлеры)
dp.include_routers(default.start_router, add_purchase.add_purchase_router)


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

