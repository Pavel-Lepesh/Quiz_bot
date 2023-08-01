from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import logging


from config.config import load_config
from aiogram.fsm.strategy import FSMStrategy
from handlers import other_handlers, superadmin_handlers, staff_handlers


async def main():
    logging.basicConfig(level=logging.INFO)

    storage: MemoryStorage = MemoryStorage()

    bot: Bot = Bot(token=load_config().tg_bot.token, parse_mode='HTML')
    dp: Dispatcher = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.CHAT)

    dp.include_router(superadmin_handlers.router)
    dp.include_router(staff_handlers.router)
    dp.include_router(other_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
