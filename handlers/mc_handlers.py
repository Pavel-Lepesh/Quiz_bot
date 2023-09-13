from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from database.db import pool, ExecuteQuery
from keyboards.staff_kbs import create_inline_kb
from filters.filters import IsMC
from lexicon.lexicon import COMMANDS_FOR_MC


router: Router = Router()
router.message.filter(IsMC())


class FSMMcStates(StatesGroup):
    send_any_message = State()
    choose_game = State()
    choose_step = State()
    save_question = State()
    send_question = State()


# Команды общего назначения


@router.message(Command(commands=['mc_info']))
async def mc_info_handler(message: Message):
    """Отправляем mc список доступных команд"""
    await message.answer(text=COMMANDS_FOR_MC['info'])


@router.message(Command(commands=['exit_game']))
async def exit_game_handler(message: Message, state: FSMContext):
    """Удаляем game_id и остальные данные из хранилища, тем самым выходя из игры"""
    await state.clear()
    await state.set_state(default_state)
    await message.answer(text='Вы вышли из игры\n\nДля начала новой игры введите /start_game')


# Режим игры для ведущего


@router.message(Command(commands=['start_game']))
async def start_game_handler(message: Message, state: FSMContext):
    """Выбираем игру в которую будем играть"""
    with ExecuteQuery(pool) as cursor:
        cursor.execute('SELECT game_id, title FROM game;')
        games = {str(id): title for id, title in cursor.fetchall()}
    await message.answer(text='Выберите игру в которую будем играть', reply_markup=create_inline_kb(width=1,
                                                                                                    **games))
    await state.set_state(FSMMcStates.choose_game)


@router.callback_query(StateFilter(FSMMcStates.choose_game))
async def choose_game_handler(callback: CallbackQuery, state: FSMContext):
    """Сохраняем game_id для дальнейшего использования"""
    game_id = callback.data
    await state.update_data(game_id=int(game_id))
    await callback.message.edit_text(text=f'Вы выбрали игру\n\nМожно приступать к отправке участникам игры раундов '
                                          f'Введите команду /go')
    await state.set_state(default_state)


@router.message(Command(commands=['go']))
async def go_command_handler(message: Message, state: FSMContext):
    """Выбираем тур, а затем степ"""
    try:
        data_dict = await state.get_data()
        game_id = data_dict['game_id']
        with ExecuteQuery(pool) as cursor:
            cursor.execute(f'SELECT tour_id, title FROM tour '
                           f'WHERE game_id = {game_id};')
            tours = {str(id): title for id, title in cursor.fetchall()}
        await message.answer(text='Выберите тур для игры',
                             reply_markup=create_inline_kb(width=1, **tours))
        await state.set_state(FSMMcStates.choose_step)
    except KeyError:
        await message.answer(text='Вы еще не выбрали игру!')


@router.callback_query(StateFilter(FSMMcStates.choose_step))
async def choose_step_handler(callback: CallbackQuery, state: FSMContext):
    """Выбираем степ"""
    tour_id = callback.data

    with ExecuteQuery(pool) as cursor:
        cursor.execute(f'SELECT step_tour_id, title FROM step_tour '
                       f'WHERE tour_id = {tour_id};')
        steps = {str(id): title for id, title in cursor.fetchall()}
    await callback.message.edit_text(text='Выберите степ',
                                     reply_markup=create_inline_kb(width=1, **steps))
    await state.set_state(FSMMcStates.save_question)


@router.callback_query(StateFilter(FSMMcStates.save_question))
async def choose_question_handler(callback: CallbackQuery, state: FSMContext):
    """Сохраняем данные вопроса в storage перед отправкой игрокам"""
    step_tour_id = callback.data
    with ExecuteQuery(pool) as cursor:
        cursor.execute(
            f'SELECT title, description, option_1, option_2, option_3, option_4 '
            f'FROM step_tour '
            f'WHERE step_tour_id = {step_tour_id};'
        )
        data_step = (step_tour_id,) + cursor.fetchone()
    keys = ('step_tour_id', 'title', 'description', 'option_1', 'option_2', 'option_3', 'option_4')

    await state.update_data(**{key: value for key, value in zip(keys, data_step)})

    await callback.message.edit_text(text='Отправить выбранный вопрос игрокам?',
                                     reply_markup=create_inline_kb(width=1, yes='Да', no='Нет'))
    await state.set_state(FSMMcStates.send_question)


# important handler
@router.callback_query(StateFilter(FSMMcStates.send_question))
async def send_question_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отправляем сообщение, либо отказываемся от отправки"""
    if callback.data == 'yes':
        data_dict = await state.get_data()  # все данные степа
        message_text = f'<b>{data_dict["title"]}</b>\n\n{data_dict["description"]}'
        message_buttons = {f'option_1_{data_dict["step_tour_id"]}': data_dict['option_1'],
                           f'option_2_{data_dict["step_tour_id"]}': data_dict['option_2'],
                           f'option_3_{data_dict["step_tour_id"]}': data_dict['option_3'],
                           f'option_4_{data_dict["step_tour_id"]}': data_dict['option_4']}  # вторым числом пишем step_tour_id
        additionally_text = (f'\n<b>Варианты ответов:</b>\n'
                             f'1. {data_dict["option_1"]}\n'
                             f'2. {data_dict["option_2"]}\n'
                             f'3. {data_dict["option_3"]}\n'
                             f'4. {data_dict["option_4"]}\n')

        with ExecuteQuery(pool) as cursor:
            cursor.execute(
                'SELECT user_id, captain FROM player;'
            )
            users: list[tuple[int, bool], ...] = cursor.fetchall()

        await state.set_state(default_state)  # ОЧЕНЬ ВАЖНЫЙ МОМЕНТ (использовать default_state во время тестирования \
                                              # в другом случае использовать состояние игроков в обчном режиме

        for user in users:
            await bot.send_message(chat_id=user[0],
                                   text=message_text if user[1] else message_text + additionally_text,
                                   reply_markup=create_inline_kb(width=2, **message_buttons) if user[1] else None,
                                   )  # капитану команды присылается сообщение с кнопками, игрокам без

        await callback.message.delete()

    else:
        await callback.message.delete()
        await state.set_state(default_state)

