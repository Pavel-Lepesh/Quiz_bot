from aiogram import Router
from aiogram.types import Message, User
from lexicon.lexicon import COMMANDS_FOR_STAFF
from database.db import pool, ExecuteQuery


router: Router = Router()


@router.message()
async def process_none(message: Message):
    """Отвечаем на неожиданное сообщение, но если это бот, меняем chat_id"""

    if message.new_chat_members:
        user: User = message.new_chat_members[0]
        if user.is_bot:
            chat_id = message.chat.id

            with ExecuteQuery(pool, commit=True) as cursor:
                cursor.execute(f'UPDATE chat_data '
                               f'SET chat_id = {str(chat_id)} '
                               f'WHERE chat_data_id = 1;')

    else:
        await message.answer(text=COMMANDS_FOR_STAFF['not_handled'])
