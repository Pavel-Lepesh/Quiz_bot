from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from database.db import pool, ExecuteQuery
from keyboards.staff_kbs import create_inline_kb
from lexicon.lexicon import COMMANDS_FOR_PLAYERS


router: Router = Router()


class FSMPlayersStates(StatesGroup):
    new_player = State()
    confirm_role = State()
    update_base = State()


#  Общие команды


@router.message(Command(commands=['help']))
async def command_help_handler(message: Message, bot: Bot):
    """Отправляем сообщение MC"""
    with ExecuteQuery(pool) as cursor:
        cursor.execute("SELECT user_id FROM quiz_staff "
                       "WHERE mc = true;")
        mc_id = cursor.fetchone()[0]
    await message.answer(text='Ваша просьба о помощи отправлена ведущему.')
    await bot.send_message(chat_id=mc_id, text=f'Игрок с именем {message.from_user.full_name} просит помощи.')


#  Регистрируем пользователей


@router.message(Command(commands=['start']))
async def command_start_handler(message: Message, state: FSMContext):
    """Предлагаем список команд"""
    with ExecuteQuery(pool) as cursor:
        cursor.execute(f"SELECT user_id FROM player "
                       f"WHERE user_id = {message.from_user.id};")
        user_exist = cursor.fetchone()
    if not user_exist:
        with ExecuteQuery(pool) as cursor:
            cursor.execute("SELECT team_id, name FROM team;")
            teams = {str(id_): name for id_, name in cursor.fetchall()}
        await message.answer(text=COMMANDS_FOR_PLAYERS['start'],
                             reply_markup=create_inline_kb(width=1, **teams))
        await state.set_state(FSMPlayersStates.new_player)
    else:
        await message.answer(text='Вы уже зарегистрировались в игре :(\n\n'
                                  'Если вам нужна помощь, обратитесь к персоналу')


@router.callback_query(StateFilter(FSMPlayersStates.new_player))
async def new_player_handler(callback: CallbackQuery, state: FSMContext):
    """Предлагаем выбор: капитан, либо игрок"""
    await state.update_data(team_id=callback.data,
                            user_id=callback.from_user.id,
                            fullname=callback.from_user.full_name)
    await callback.message.edit_text(text='Выберите свою роль',
                                     reply_markup=create_inline_kb(width=2, captain='Капитан', player='Игрок'))
    await state.set_state(FSMPlayersStates.confirm_role)


@router.callback_query(StateFilter(FSMPlayersStates.confirm_role))
async def confirm_role_handler(callback: CallbackQuery, state: FSMContext):
    """Подтверждаем роль"""
    await state.update_data(captain=True if callback.data == 'captain' else False)
    await callback.message.edit_text(text='Вы уверены?',
                                     reply_markup=create_inline_kb(width=2, yes='Да', no='Нет'))
    await state.set_state(FSMPlayersStates.update_base)


@router.callback_query(StateFilter(FSMPlayersStates.update_base))
async def update_base_handler(callback: CallbackQuery, state: FSMContext):
    """Вносим игрока в базу данных"""
    if callback.data == 'yes':
        state_data = await state.get_data()
        correct_data = ', '.join([repr(value) for value in state_data.values()])
        with ExecuteQuery(pool, commit=True) as cursor:
            cursor.execute(f"INSERT INTO player(team_id, user_id, fullname, captain) "
                           f"VALUES ({correct_data});")
        await callback.message.edit_text(text=COMMANDS_FOR_PLAYERS['complete_registration'])
    else:
        await callback.message.edit_text(text=COMMANDS_FOR_PLAYERS['wrong_answer'])
    await state.clear()  # опционально, попробовать вариант когда данные будут непосредственно в хранилище
    await state.set_state(default_state)
