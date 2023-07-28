from aiogram import Router
from aiogram.types import Message


router: Router = Router()


@router.message()
async def process_none(message: Message):
    await message.answer('Действий нет')
