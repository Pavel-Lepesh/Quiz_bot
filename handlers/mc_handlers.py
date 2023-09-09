from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from database.db import pool, ExecuteQuery
from keyboards.staff_kbs import create_inline_kb
from filters.filters import IsMC


router: Router = Router()
router.message.filter(IsMC())


class FSMMcStates(StatesGroup):
    send_any_message = State()


@router.message(Command(commands=['send_message']))
async def prepare_message_handler(message: Message, state: FSMContext):
    """Вводим сообщение для рассылки"""
    await message.answer(text='Введите сообщение для рассылки')
    await state.set_state(FSMMcStates.send_any_message)

# предусмотреть вариант с отменой состояния отправки сообщения
@router.message(StateFilter(FSMMcStates.send_any_message))
async def send_message_handler(message: Message, state: FSMContext, bot: Bot):
    """Отправляем сообщение всем участникам игры"""
    with ExecuteQuery(pool) as cursor:
        cursor.execute("SELECT user_id FROM player;")
        all_id: list[tuple[int]] = cursor.fetchall()
    for item in all_id:
        await bot.send_message(chat_id=item[0], text=f'{message.text}')
    await message.answer(text='Сообщение отправлено')
    await state.set_state(default_state)
    await bot.send_message(text='ff')


@router.message(Command(commands=['start_game']))
async def start_game_handler(message:Message, state: FSMContext):
    pass
