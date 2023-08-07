from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, BotCommand
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
    edit_or_new_game = State()
    define_tour = State()
    edit_step1 = State()
    edit_step2 = State()
    edit_step3 = State()
    edit_step4 = State()
    edit_step5 = State()
    edit_step6 = State()
    edit_step7 = State()
    edit_step8 = State()
    save_game = State()
    confirm_wrong = State()
    confirm_correct = State()
    select_name = State()
    select_tours = State()
    delete_game = State()
    confirm_delete = State()


# команды общего назначения


@router.message(Command(commands=['info']))
async def info_handler(message: Message):
    """Информационное сообщение с возможностями бота(для сотрудников)"""
    await message.answer(text=COMMANDS_FOR_STAFF['info'])


@router.message(Command(commands=['getmenu']))
async def getmenu_handler(message: Message, bot: Bot):
    main_menu_commands = [BotCommand(command='/info', description='Получить информацию')]
    await bot.set_my_commands(main_menu_commands)
    await message.answer(text='menu')


@router.message(Command(commands=['exit_edit']))
async def exit_edit_handler(message: Message, state: FSMContext):
    await message.answer(text='Вы вышли из режима редактирования')
    await state.clear()
    await state.set_state(default_state)


# Здесь редактируем или выбираем игру


@router.message(StateFilter(default_state), Command(commands=['select_or_add_the_game']))
async def select_or_add_the_game_handler(message: Message, state: FSMContext):
    """Создаем новую игру или выбираем игру из базы данных"""
    await message.answer(text='Что выберите?', reply_markup=create_inline_kb(width=1,
                                                                             new_game='Новая игра',
                                                                             edit_game='Редактировать игру'))
    await state.set_state(FSMStaffStates.edit_or_new_game)


@router.callback_query(StateFilter(FSMStaffStates.edit_or_new_game), F.data == 'new_game')
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
    await state.clear()
    await message.answer(text='Данные загружены!')


# Начинаем редактирование тура


@router.callback_query(StateFilter(FSMStaffStates.edit_or_new_game), F.data == 'edit_game')
async def choose_edit_game_handler(callback: CallbackQuery, state: FSMContext):
    """Выбираем игру для редактирования"""
    with ExecuteQuery(pool) as cursor:
        cursor.execute("SELECT game_id, title "
                       "FROM game;")
        games = {str(id): title for id, title in cursor.fetchall()}
    await callback.message.edit_text(text='Выберите игру для редактирования',
                                     reply_markup=create_inline_kb(width=1, **games))
    await state.set_state(FSMStaffStates.define_tour)


@router.callback_query(StateFilter(FSMStaffStates.define_tour))
async def define_tour_handler(callback: CallbackQuery, state: FSMContext):
    """Определяем номер тура и сохраняем game_id"""
    game_id = callback.data
    await state.update_data(game_id=game_id)
    with ExecuteQuery(pool) as cursor:
        cursor.execute(f"SELECT quantity FROM game "
                       f"WHERE game_id = {game_id};")
        quantity = cursor.fetchone()[0]
        cursor.execute(f"SELECT tour_number FROM tour "
                       f"WHERE game_id = {game_id};")
        tours_numbers: list[int] = [i[0] for i in cursor.fetchall()]  # номера туров которые уже существуют
    if quantity != len(tours_numbers):  # если количество туров не совпадает с загруженными турами
        await callback.message.edit_text(text='Выберите номер тура',
                                         reply_markup=create_inline_kb(width=1,
                                                                       **{str(i): str(i) for i in range(1, quantity + 1) if i not in tours_numbers}))
        await state.set_state(FSMStaffStates.edit_step1)
    else:
        await callback.message.edit_text(text='Задания для всех туров установлены!')
        await state.set_state(default_state)


@router.callback_query(StateFilter(FSMStaffStates.edit_step1))
async def edit_game_step1_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Сохраняем tour_number и просим ввести название тура"""
    tour_number = callback.data
    data_dict = await state.get_data()
    with ExecuteQuery(pool) as cursor:
        cursor.execute(f"SELECT tour_number FROM tour "
                       f"WHERE game_id = {data_dict['game_id']} AND tour_number = {tour_number};")
        results = cursor.fetchall()

    if not results:
        await state.update_data(tour_number=tour_number)
        await bot.send_message(chat_id=callback.message.chat.id, text='Напишите название тура')
        await callback.message.delete()
        await state.set_state(FSMStaffStates.edit_step2)
    else:
        await callback.message.edit_text(text='Этот тур уже существует. Выберите другой:',
                                         reply_markup=callback.message.reply_markup)


@router.message(StateFilter(FSMStaffStates.edit_step2), F.text)
async def edit_game_step2_handler(message: Message, state: FSMContext):
    """Сохраняем title и просим задать основной вопрос тура"""
    await state.update_data(title=message.text)
    await message.answer(text='Задайте вопрос')
    await state.set_state(FSMStaffStates.edit_step3)


@router.message(StateFilter(FSMStaffStates.edit_step3), F.text)
async def edit_game_step3_handler(message: Message, state: FSMContext):
    """Сохраняем description и просим вводить варианты ответа"""
    await state.update_data(description=message.text)
    await message.answer(text='Теперь давайте введем ответы\nВведите первый вариант ответа')
    await state.set_state(FSMStaffStates.edit_step4)


@router.message(StateFilter(FSMStaffStates.edit_step4), lambda x: isinstance(x.text, str) and len(x.text) <= 30)
async def edit_game_step4_handler(message: Message, state: FSMContext):
    """Сохраняем первый вариант"""
    await state.update_data(option_1=message.text)
    await message.answer(text='Введите второй вариант ответа')
    await state.set_state(FSMStaffStates.edit_step5)


@router.message(StateFilter(FSMStaffStates.edit_step5), lambda x: isinstance(x.text, str) and len(x.text) <= 30)
async def edit_game_step5_handler(message: Message, state: FSMContext):
    """Сохраняем второй вариант"""
    await state.update_data(option_2=message.text)
    await message.answer(text='Введите третий вариант ответа')
    await state.set_state(FSMStaffStates.edit_step6)


@router.message(StateFilter(FSMStaffStates.edit_step6), lambda x: isinstance(x.text, str) and len(x.text) <= 30)
async def edit_game_step6_handler(message: Message, state: FSMContext):
    """Сохраняем третий вариант"""
    await state.update_data(option_3=message.text)
    await message.answer(text='Введите четвертый вариант ответа')
    await state.set_state(FSMStaffStates.edit_step7)


@router.message(StateFilter(FSMStaffStates.edit_step7), lambda x: isinstance(x.text, str) and len(x.text) <= 30)
async def edit_game_step7_handler(message: Message, state: FSMContext):
    """Сохраняем четвертый вариант и выбираем правильный ответ"""
    await state.update_data(option_4=message.text)
    data_dict = await state.get_data()
    # в этом моменте не запутаться с базой данных(возможно переименовать тип и названия полей)
    await message.answer(text='Какой из них является правильным?', reply_markup=create_inline_kb(width=1,
                                                                                                 option_1=data_dict[
                                                                                                     'option_1'],
                                                                                                 option_2=data_dict[
                                                                                                     'option_2'],
                                                                                                 option_3=data_dict[
                                                                                                     'option_3'],
                                                                                                 option_4=data_dict[
                                                                                                     'option_4']))

    await state.set_state(FSMStaffStates.edit_step8)


@router.callback_query(StateFilter(FSMStaffStates.edit_step8))
async def confirm_answer_handler(callback: CallbackQuery, state: FSMContext):
    """Сохраняем правильный ответ и выбираем количество баллов за неправильный"""
    await state.update_data(answer=callback.data)
    await callback.message.edit_text(text='Сколько отнимать баллов за неправильный ответ? (от -2 до 0)',
                                     reply_markup=create_inline_kb(width=3, **{'-2': '-2', '-1': '-1', '0': '0'}))
    await state.set_state(FSMStaffStates.confirm_wrong)


@router.callback_query(StateFilter(FSMStaffStates.confirm_wrong))
async def confirm_wrong_handler(callback: CallbackQuery, state: FSMContext):
    """Сохраняем количество баллов за неправильный ответ и выбираем количество за правильный"""
    await state.update_data(wrong=callback.data)
    await callback.message.edit_text(text='Сколько начислять баллов за правильный ответ? (от 1 до 2)',
                                     reply_markup=create_inline_kb(width=2, **{'1': '1', '2': '2'}))
    await state.set_state(FSMStaffStates.confirm_correct)


@router.callback_query(StateFilter(FSMStaffStates.confirm_correct))
async def confirm_correct_handler(callback: CallbackQuery, state: FSMContext):
    """Спрашиваем подтверждение на сохранение игры"""
    await state.update_data(correct=callback.data)
    await callback.message.edit_text(text='Сохраняем игру?', reply_markup=create_inline_kb(width=2, yes='Да', no='Нет'))
    await state.set_state(FSMStaffStates.save_game)


@router.callback_query(StateFilter(FSMStaffStates.save_game))
async def save_game_handler(callback: CallbackQuery, state: FSMContext):
    """Сохраняем игру в базу или ничего не делаем"""
    if callback.data == 'yes':
        data_dict = await state.get_data()
        correct_data = ', '.join([repr(value) for value in data_dict.values()])
        with ExecuteQuery(pool, commit=True) as cursor:
            cursor.execute(f'INSERT INTO tour(game_id, tour_number, title, description, option_1, option_2, option_3, option_4, answer, wrong, correct) '
                           f'VALUES ({correct_data});')
        await callback.message.edit_text(text='Игра сохранена!')
    else:
        await callback.message.delete()
    await state.clear()
    await state.set_state(default_state)


# Здесь удаляем игру


@router.message(IsSuperAdmin(), Command(commands=['delete_game']), StateFilter(default_state))
async def delete_game_handler(message: Message, state: FSMContext):
    """Приступаем к удалению игры"""
    with ExecuteQuery(pool) as cursor:
        cursor.execute("SELECT game_id, title "
                       "FROM game;")
        games = {str(id): title for id, title in cursor.fetchall()}
    await message.answer(text='Какую игру удалить?', reply_markup=create_inline_kb(width=1, **games))
    await state.set_state(FSMStaffStates.delete_game)


@router.callback_query(StateFilter(FSMStaffStates.delete_game))
async def confirm_delete_handler(callback: CallbackQuery, state: FSMContext):
    """Подтверждаем удаление игры"""
    await state.update_data(game_id=callback.data)
    await callback.message.edit_text(text='Вы уверены?', reply_markup=create_inline_kb(width=1,
                                                                                       yes='Да',
                                                                                       no='Нет'))
    await state.set_state(FSMStaffStates.confirm_delete)


@router.callback_query(StateFilter(FSMStaffStates.confirm_delete))
async def approve_delete_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Удаляем игру из базы данных"""
    if callback.data == 'yes':
        data_dict = await state.get_data()
        with ExecuteQuery(pool, commit=True) as cursor:
            game_id = int(data_dict['game_id'])
            cursor.execute(f"DELETE FROM game "
                           f"WHERE game_id = {game_id};")
        await bot.send_message(chat_id=callback.message.chat.id, text='Удаление завершено!')

    await callback.message.delete()
    await state.clear()
    await state.set_state(default_state)
