from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import logging
import psycopg2.pool


from config.config import load_config, load_db_password
from handlers import other_handlers, staff_handlers 


pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    database="Quiz_members",
    user="postgres",
    password=load_db_password().tg_bot.db_password,
    host="127.0.0.1",
    port="5432"
)

conn = pool.getconn()
pool.putconn(conn)
staff_handlers.pool = pool


async def main():
    logging.basicConfig(level=logging.INFO)

    storage: MemoryStorage = MemoryStorage()

    bot: Bot = Bot(token=load_config().tg_bot.token, parse_mode='HTML')
    dp: Dispatcher = Dispatcher(storage=storage)

    dp.include_router(staff_handlers.router)
    dp.include_router(other_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
