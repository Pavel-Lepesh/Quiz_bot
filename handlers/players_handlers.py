from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from database.db import pool, ExecuteQuery
from keyboards.staff_kbs import create_inline_kb
from lexicon.lexicon import COMMANDS_FOR_PLAYERS
from keyboards.set_menu import set_players_menu


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


@router.message(Command(commands=['rules']))
async def rules_handler(message: Message):
    """Информационное сообщение для игроков"""
    await message.answer(text=COMMANDS_FOR_PLAYERS['rules'])


#  Регистрируем пользователей


@router.message(Command(commands=['start']))
async def command_start_handler(message: Message, state: FSMContext, bot: Bot):
    """Предлагаем список команд"""
    await set_players_menu(bot)  # ставим меню для игроков

    with ExecuteQuery(pool) as cursor:
        cursor.execute(f"SELECT user_id FROM player "
                       f"WHERE user_id = {message.from_user.id};")
        user_exist = cursor.fetchone()
    if not user_exist:
        with ExecuteQuery(pool) as cursor:
            cursor.execute("SELECT team_id, name FROM team;")
            teams = {str(id_): f'"{name}"' for id_, name in cursor.fetchall()}
        await message.answer(text=COMMANDS_FOR_PLAYERS['start'],
                             reply_markup=create_inline_kb(width=1, **teams, no_team='Моей команды нет в списке'))
        await state.set_state(FSMPlayersStates.new_player)
    else:
        await message.answer(text='Вы уже зарегистрировались в игре :(\n\n'
                                  'Если вам нужна помощь, обратитесь к персоналу')


@router.callback_query(StateFilter(FSMPlayersStates.new_player), F.data == 'no_team')
async def no_team_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Выходим из режима старта игры"""
    await bot.delete_my_commands()
    await callback.message.edit_text(text='Чтобы решить вашу проблему, обратитесь к персоналу квиза')
    await state.set_state(default_state)


@router.callback_query(StateFilter(FSMPlayersStates.new_player))
async def new_player_handler(callback: CallbackQuery, state: FSMContext):
    """Предлагаем выбор: капитан, либо игрок"""
    team_id = callback.data

    await state.update_data(team_id=team_id,
                            user_id=callback.from_user.id,
                            fullname=callback.from_user.full_name)

    with ExecuteQuery(pool) as cursor:
        cursor.execute(f'SELECT has_captain FROM team '
                       f'WHERE team_id = {team_id};')
        has_captain = cursor.fetchone()  # проверяем есть ли у команды капитан

    if not has_captain[0]:
        await callback.message.edit_text(text='Выберите свою роль',
                                         reply_markup=create_inline_kb(width=2, captain='Капитан', player='Игрок'))
        await state.set_state(FSMPlayersStates.confirm_role)
    else:
        await callback.message.edit_text(text='Выберите свою роль',
                                         reply_markup=create_inline_kb(width=2, player='Игрок'))
        await state.set_state(FSMPlayersStates.confirm_role)


@router.callback_query(StateFilter(FSMPlayersStates.confirm_role))
async def confirm_role_handler(callback: CallbackQuery, state: FSMContext):
    """Подтверждаем роль"""
    await state.update_data(captain=True if callback.data == 'captain' else False)
    await callback.message.edit_text(text='Вы уверены в выборе команды и роли?',
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

            if state_data['captain']:
                cursor.execute(f'UPDATE team '
                               f'SET has_captain = true '
                               f'WHERE team_id = {state_data["team_id"]};')

        await callback.message.edit_text(text=COMMANDS_FOR_PLAYERS['complete_registration'])
    else:
        await callback.message.edit_text(text=COMMANDS_FOR_PLAYERS['wrong_answer'])
    await state.clear()  # опционально, попробовать вариант когда данные будут непосредственно в хранилище
    await state.set_state(default_state)


# important handler (протестировать работу состояний здесь)
@router.callback_query(StateFilter(default_state))  # СОСТОЯНИЕ (решить какое использовать)
async def fix_answer_handler(callback: CallbackQuery, state: FSMContext):
    """Принимаем сообщение от mc, заносим ответ в бд"""
    user_id = callback.from_user.id
    step_tour_id = callback.data.split('_')[-1]
    user_answer = callback.data[:8]  # оставляем только option_num

    with ExecuteQuery(pool, commit=True) as cursor:
        cursor.execute(
            f"INSERT INTO answer(user_id, step_tour_id, user_answer)  "
            f"VALUES ('{user_id}', '{step_tour_id}', '{user_answer}');"
        )
    await callback.message.edit_text(text='Ваш ответ принят!')
