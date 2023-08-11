from aiogram import Router
from aiogram.types import Message
from lexicon.lexicon import COMMANDS_FOR_STAFF


router: Router = Router()


@router.message()
async def process_none(message: Message):
    await message.answer(text=COMMANDS_FOR_STAFF['not_handled'])
