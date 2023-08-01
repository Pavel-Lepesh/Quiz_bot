from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from database.db import pool, ExecuteQuery
from lexicon.lexicon import COMMANDS_FOR_STAFF
from filters.filters import IsSuperAdmin, IsAdmin, IsMC
from keyboards.staff_kbs import create_inline_kb

router: Router = Router()
router.message.filter(IsSuperAdmin(), IsAdmin(), IsMC())


class FSMStaffStates(StatesGroup):
    new_game = State()
    select_name = State()
    select_tours = State()


@router.message(Command(commands=['info']))
async def info_handler(message: Message):
    """Информационное сообщение с возможностями бота(для сотрудников)"""
    await message.answer(text=COMMANDS_FOR_STAFF['info'])


@router.message(StateFilter(default_state), Command(commands=['select_or_add_the_game']))
async def select_or_add_the_game_handler(message: Message, state: FSMContext):
    """Создаем новую игру или выбираем игру из базы данных"""
    await message.answer(text='Что выберите?', reply_markup=create_inline_kb(width=1, new_game='Новая игра'))
    await state.set_state(FSMStaffStates.new_game)


@router.callback_query(StateFilter(FSMStaffStates.new_game), F.data == 'new_game')
async def new_game_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Пишем в сообщении имя для новой игры"""
    await callback.answer()
    await bot.send_message(chat_id=callback.message.chat.id, text='Напишите название вашей игры')
    await state.set_state(FSMStaffStates.select_name)


@router.message(StateFilter(FSMStaffStates.select_name), F.text)
async def select_name_handler(message: Message, state: FSMContext):
    """Вводим количество туров"""
    await state.update_data(game_title=message.text)
    await message.answer(text='Отлично! Теперь давайте выберем количество туров\n\n'
                              '<i>Введите количество туров (число от 1 до 10)</i>')
    await state.set_state(FSMStaffStates.select_tours)


@router.message(StateFilter(FSMStaffStates.select_tours), lambda x: int(x.text) in range(1, 11))
async def select_tours_handler(message: Message, state: FSMContext):
    """Вносим в базу данные игры"""
    data_dict = await state.get_data()
    with ExecuteQuery(pool, commit=True) as cursor:
        cursor.execute(f"INSERT INTO game(title, quantity) "
                       f"VALUES ('{data_dict['game_title']}', {int(message.text)});")
    await message.answer(text='Данные загружены!')
