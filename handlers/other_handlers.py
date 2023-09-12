from aiogram import Router
from aiogram.types import Message, CallbackQuery
from lexicon.lexicon import COMMANDS_FOR_STAFF


router: Router = Router()


@router.message()
async def process_none(message: Message):
    await message.answer(text=COMMANDS_FOR_STAFF['not_handled'])


@router.callback_query()
async def other_callback_handler(callback: CallbackQuery):
    print('Отработано')
    await callback.answer()
