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

import csv


router: Router = Router()
router.message.filter(IsSuperAdmin(), IsAdmin(), IsMC())


class FSMStaffStates(StatesGroup):
    edit_or_new_game = State()
    define_tour = State()
    edit_tour_step1 = State()
    download_csv = State()
    edit_tour_step2 = State()
    edit_tour_step3 = State()
    edit_step1 = State()
    edit_step2 = State()
    edit_step3 = State()
    edit_step4 = State()
    edit_step5 = State()
    edit_step6 = State()
    edit_step7 = State()
    edit_step8 = State()
    edit_step9 = State()
    edit_step10 = State()
    save_game = State()
    confirm_wrong = State()
    confirm_correct = State()
    select_name = State()
    select_tours = State()
    delete_game = State()
    delete_game2 = State()
    confirm_delete_game = State()
    delete_tour = State()
    choose_team = State()
    add_another_one_team = State()
    delete_team = State()


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
                                                                             new_tour='Новый тур',
                                                                             new_step_tour='Новый шаг тура'))
    await state.set_state(FSMStaffStates.edit_or_new_game)


@router.callback_query(StateFilter(FSMStaffStates.edit_or_new_game), F.data == 'new_game')
async def new_game_callback(callback: CallbackQuery, state: FSMContext):
    """Пишем в сообщении имя для новой игры"""
    await callback.message.edit_text(text='Напишите название вашей игры')
    await state.set_state(FSMStaffStates.select_name)


@router.message(StateFilter(FSMStaffStates.select_name), F.text)
async def select_name_handler(message: Message, state: FSMContext):
    """Вводим количество туров"""
    await state.update_data(game_title=message.text)
    await message.answer(text='Отлично! Теперь давайте выберем количество туров',
                         reply_markup=create_inline_kb(width=2, **{str(i): str(i) for i in range(1, 11)}))
    await state.set_state(FSMStaffStates.select_tours)


@router.callback_query(StateFilter(FSMStaffStates.select_tours))
async def select_tours_handler(callback: CallbackQuery, state: FSMContext):
    """Вносим в базу данные игры"""
    data_dict = await state.get_data()
    with ExecuteQuery(pool, commit=True) as cursor:
        cursor.execute(f"INSERT INTO game(title, quantity) "
                       f"VALUES ('{data_dict['game_title']}', {int(callback.data)});")
    await state.clear()
    await callback.message.edit_text(text='Данные загружены!')
    await state.set_state(default_state)


# Начинаем редактирование тура


@router.callback_query(StateFilter(FSMStaffStates.edit_or_new_game), F.data == 'new_tour')
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
                                                                       **{str(i): str(i) for i in range(1, quantity + 1) if i not in tours_numbers},
                                                                       import_csv='Загрузить из файла CSV'))
        await state.set_state(FSMStaffStates.edit_tour_step1)
    else:
        await callback.message.edit_text(text='Задания для всех туров установлены!')
        await state.clear()
        await state.set_state(default_state)


@router.callback_query(StateFilter(FSMStaffStates.edit_tour_step1), F.data == 'import_csv')
async def import_csv_handler(callback: CallbackQuery, state: FSMContext):
    """Просим загрузить файл для импорта туров и степов"""
    await callback.message.edit_text(text='Загрузите файл с турами для игры')
    await state.set_state(FSMStaffStates.download_csv)


@router.message(StateFilter(FSMStaffStates.download_csv), F.document.mime_type == 'text/csv')
async def download_csv_handler(message: Message, state: FSMContext, bot: Bot):
    """Загрузка файла и обработка"""
    try:
        # загружаем файл и сохраняем его как data.csv
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path
        await bot.download_file(file_path, './data.csv')
    except Exception as error:
        await message.answer(text=f'Возникла проблема с загрузкой файла: {error}')

    try:
        # сохраняем туры и степы в БД
        with open('./data.csv', newline='') as file:
            state_data = await state.get_data()
            game_id = state_data['game_id']
            tour_number = None  # сюда сохраняем значение для поиска соответствующего tour_id
            rows = csv.DictReader(file, delimiter=';')

            for row in rows:
                if row['tour_number']:  # если в строке есть tour_number, значит это строку вносим как тур
                    tour_number = row['tour_number']
                    tour = ', '.join(map(repr, list(row.values())[:3]))
                    with ExecuteQuery(pool, commit=True) as cursor:
                        cursor.execute(f"INSERT INTO tour(game_id, tour_number, title, quantity) "
                                       f"VALUES ({game_id}, {tour});")
                else:  # для степов тура
                    step_tour = ', '.join(map(repr, list(row.values())[3:]))
                    with ExecuteQuery(pool) as cursor:
                        cursor.execute(f"SELECT tour_id FROM tour "
                                       f"WHERE game_id = {game_id} AND tour_number = {tour_number};")
                        tour_id = cursor.fetchone()[0]
                    with ExecuteQuery(pool, commit=True) as cursor:
                        cursor.execute(
                            f"INSERT INTO step_tour(tour_id, step_tour_number, title, description, option_1, option_2, option_3, option_4, answer, wrong, correct) "
                            f"VALUES ({tour_id}, {step_tour});")
    except Exception as error:
        await message.answer(text=f'Возникла ошибка с обработкой файла: {error}')
    else:
        await message.answer(text='Данные успешно загружены!')
    finally:
        await state.clear()
        await state.set_state(default_state)


@router.callback_query(StateFilter(FSMStaffStates.edit_tour_step1))
async def edit_tour_step1_handler(callback: CallbackQuery, state: FSMContext):
    """Сохраняем tour_number и просим ввести название тура"""
    await state.update_data(tour_number=callback.data)
    await callback.message.edit_text(text='Напишите название тура')
    await state.set_state(FSMStaffStates.edit_tour_step2)


@router.message(StateFilter(FSMStaffStates.edit_tour_step2), F.text)
async def edit_tour_step2_handler(message: Message, state: FSMContext):
    """Сохраняем title и просим задать количество вопросов в туре"""
    await state.update_data(title=message.text)
    await message.answer(text='Введите количество вопросов в туре',
                         reply_markup=create_inline_kb(width=2, **{str(i): str(i) for i in range(1, 11)}))
    await state.set_state(FSMStaffStates.edit_tour_step3)


@router.callback_query(StateFilter(FSMStaffStates.edit_tour_step3))
async def edit_tour_step3_handler(callback: CallbackQuery, state: FSMContext):
    """Сохраняем quantity и сам тур в базе данных"""
    await state.update_data(quantity=callback.data)
    data_dict = await state.get_data()
    correct_data = ', '.join([repr(value) for value in data_dict.values()])
    with ExecuteQuery(pool, commit=True) as cursor:
        cursor.execute(f"INSERT INTO tour(game_id, tour_number, title, quantity) "
                       f"VALUES ({correct_data});")
    await callback.message.edit_text(text=f'Ваш тур "{data_dict["title"]}" сохранен!')
    await state.clear()
    await state.set_state(default_state)


# Начинаем редактирование степа тура


@router.callback_query(StateFilter(FSMStaffStates.edit_or_new_game), F.data == 'new_step_tour')
async def edit_step_handler(callback: CallbackQuery, state: FSMContext):
    """Выбираем игру для редактирования"""
    with ExecuteQuery(pool) as cursor:
        cursor.execute("SELECT game_id, title "
                       "FROM game;")
        games = {str(id): title for id, title in cursor.fetchall()}
    await callback.message.edit_text(text='Выберите игру для редактирования',
                                     reply_markup=create_inline_kb(width=1, **games))
    await state.set_state(FSMStaffStates.edit_step1)


@router.callback_query(StateFilter(FSMStaffStates.edit_step1))
async def edit_step1_handler(callback: CallbackQuery, state: FSMContext):
    """Определяем номер тура для степов"""
    game_id = callback.data
    with ExecuteQuery(pool) as cursor:
        cursor.execute(f"SELECT tour_id, title, tour_number FROM tour "
                       f"WHERE game_id = {game_id};")
        query_data = sorted(cursor.fetchall(), key=lambda x: x[2])  # сортируем по tour_number
    await callback.message.edit_text(text='Выберите тур',
                                     reply_markup=create_inline_kb(width=1,
                                                                   **{str(tour_id): str(title) for tour_id, title, _ in query_data}))
    await state.set_state(FSMStaffStates.edit_step2)


@router.callback_query(StateFilter(FSMStaffStates.edit_step2))
async def edit_step2_handler(callback: CallbackQuery, state: FSMContext):
    """Сохраняем tour_id и выбираем step_tour_number"""
    tour_id = callback.data
    await state.update_data(tour_id=tour_id)
    with ExecuteQuery(pool) as cursor:
        cursor.execute(f"SELECT quantity FROM tour "
                      f"WHERE tour_id = {tour_id};")
        quantity = cursor.fetchone()[0]  # количество степов в туре
        cursor.execute(f"SELECT step_tour_number FROM step_tour "
                       f"WHERE tour_id = {tour_id};")
        step_tour_numbers: list[int] = [i[0] for i in cursor.fetchall()]  # номера степов которые уже существуют
    if quantity != len(step_tour_numbers):  # если количество туров не совпадает с загруженными турами
        await callback.message.edit_text(text='Выберите номер степа',
                                         reply_markup=create_inline_kb(width=1,
                                                                       **{str(i): str(i) for i in range(1, quantity + 1) if i not in step_tour_numbers}))
        await state.set_state(FSMStaffStates.edit_step3)
    else:
        await callback.message.edit_text(text='Все степы для этого тура установлены!')
        await state.clear()
        await state.set_state(default_state)


@router.callback_query(StateFilter(FSMStaffStates.edit_step3))
async def edit_step3_handler(callback: CallbackQuery, state: FSMContext):
    """Сохраняем step_tour_number"""
    await state.update_data(step_tour_number=callback.data)
    await callback.message.edit_text(text='Введите название степа')
    await state.set_state(FSMStaffStates.edit_step4)


@router.message(StateFilter(FSMStaffStates.edit_step4))
async def edit_step4_handler(message: Message, state: FSMContext):
    """Сохраняем title"""
    await state.update_data(title=message.text)
    await message.answer(text='Введите описание степа')
    await state.set_state(FSMStaffStates.edit_step5)


@router.message(StateFilter(FSMStaffStates.edit_step5), F.text)
async def edit_step5_handler(message: Message, state: FSMContext):
    """Сохраняем description и просим вводить варианты ответа"""
    await state.update_data(description=message.text)
    await message.answer(text='Теперь давайте введем ответы\nВведите первый вариант ответа')
    await state.set_state(FSMStaffStates.edit_step6)


@router.message(StateFilter(FSMStaffStates.edit_step6), lambda x: isinstance(x.text, str) and len(x.text) <= 30)
async def edit_6_handler(message: Message, state: FSMContext):
    """Сохраняем первый вариант"""
    await state.update_data(option_1=message.text)
    await message.answer(text='Введите второй вариант ответа')
    await state.set_state(FSMStaffStates.edit_step7)


@router.message(StateFilter(FSMStaffStates.edit_step7), lambda x: isinstance(x.text, str) and len(x.text) <= 30)
async def edit_step7_handler(message: Message, state: FSMContext):
    """Сохраняем второй вариант"""
    await state.update_data(option_2=message.text)
    await message.answer(text='Введите третий вариант ответа')
    await state.set_state(FSMStaffStates.edit_step8)


@router.message(StateFilter(FSMStaffStates.edit_step8), lambda x: isinstance(x.text, str) and len(x.text) <= 30)
async def edit_step8_handler(message: Message, state: FSMContext):
    """Сохраняем третий вариант"""
    await state.update_data(option_3=message.text)
    await message.answer(text='Введите четвертый вариант ответа')
    await state.set_state(FSMStaffStates.edit_step9)


@router.message(StateFilter(FSMStaffStates.edit_step9), lambda x: isinstance(x.text, str) and len(x.text) <= 30)
async def edit_step9_handler(message: Message, state: FSMContext):
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

    await state.set_state(FSMStaffStates.edit_step10)


@router.callback_query(StateFilter(FSMStaffStates.edit_step10))
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
            cursor.execute(f'INSERT INTO step_tour(tour_id, step_tour_number, title, description, option_1, option_2, option_3, option_4, answer, wrong, correct) '
                           f'VALUES ({correct_data});')
        await callback.message.edit_text(text='Игра сохранена!')
    else:
        await callback.message.delete()
    await state.clear()
    await state.set_state(default_state)


# Здесь удаляем части игры


@router.message(IsSuperAdmin(), Command(commands=['delete']), StateFilter(default_state))
async def delete_handler(message: Message, state: FSMContext):
    """Приступаем к удалению"""
    with ExecuteQuery(pool) as cursor:
        cursor.execute("SELECT game_id, title "
                       "FROM game;")
        games = {str(id): title for id, title in cursor.fetchall()}
    if games:
        await message.answer(text='Выберите игру', reply_markup=create_inline_kb(width=1, **games))
        await state.set_state(FSMStaffStates.delete_game)
    else:
        await message.answer(text='Игры не найдены.')
        await state.set_state(default_state)


@router.callback_query(StateFilter(FSMStaffStates.delete_game))
async def delete_handler2(callback: CallbackQuery, state: FSMContext):
    """Выбираем тур, либо удаляем игру"""
    game_id = callback.data
    await state.update_data(game_id=game_id)
    with ExecuteQuery(pool) as cursor:
        cursor.execute(f"SELECT tour_id, title FROM tour "
                       f"WHERE game_id = {game_id};")
        tours = {str(id): title for id, title in cursor.fetchall()}
    await callback.message.edit_text(text='Выберите тур для удаления, либо удалите игру',
                                     reply_markup=create_inline_kb(width=1, **tours, game_delete='Удалить эту игру'))
    await state.set_state(FSMStaffStates.delete_game2)


@router.callback_query(StateFilter(FSMStaffStates.delete_game2), F.data == 'game_delete')
async def confirm_delete_game_handler(callback: CallbackQuery, state: FSMContext):
    """Подтверждаем удаление игры"""
    await callback.message.edit_text(text='Вы уверены?', reply_markup=create_inline_kb(width=1,
                                                                                       yes='Да',
                                                                                       no='Нет'))
    await state.set_state(FSMStaffStates.confirm_delete_game)


@router.callback_query(StateFilter(FSMStaffStates.confirm_delete_game))
async def approve_delete_game_handler(callback: CallbackQuery, state: FSMContext):
    """Удаляем игру из базы данных"""
    if callback.data == 'yes':
        data_dict = await state.get_data()
        with ExecuteQuery(pool, commit=True) as cursor:
            game_id = int(data_dict['game_id'])
            cursor.execute(f"DELETE FROM game "
                           f"WHERE game_id = {game_id};")
        await callback.message.edit_text(text='Удаление завершено!')
    else:
        await callback.message.delete()

    await state.clear()
    await state.set_state(default_state)


@router.callback_query(StateFilter(FSMStaffStates.delete_game2))
async def delete_tour_handler(callback: CallbackQuery, state: FSMContext):
    """Выбираем тур или удаляем степ"""
    await state.clear()  # очищаем хранилище, чтобы game_id не вызывал конфликтов
    tour_id = callback.data
    await state.update_data(tour_id=tour_id)
    with ExecuteQuery(pool) as cursor:
        cursor.execute(f"SELECT step_tour_id, title FROM step_tour "
                       f"WHERE tour_id = {tour_id};")
        steps = {str(id): title for id, title in cursor.fetchall()}

    await callback.message.edit_text(text='Выберите степ для удаления, либо удалите тур',
                                     reply_markup=create_inline_kb(width=1, **steps, tour_delete='Удалить этот тур'))
    await state.set_state(FSMStaffStates.delete_tour)


@router.callback_query(StateFilter(FSMStaffStates.delete_tour), F.data == 'tour_delete')
async def confirm_delete_tour(callback: CallbackQuery, state: FSMContext):
    """Подтверждаем удаление тура"""
    data_dict = await state.get_data()
    tour_id = data_dict['tour_id']
    with ExecuteQuery(pool, commit=True) as cursor:
        cursor.execute(f"DELETE FROM tour "
                       f"WHERE tour_id = {tour_id};")
    await callback.message.edit_text(text='Удаление завершено!')
    await state.clear()
    await state.set_state(default_state)


@router.callback_query(StateFilter(FSMStaffStates.delete_tour))
async def step_tour_delete_handler(callback: CallbackQuery, state: FSMContext):
    """Удаляем степ тура"""
    step_tour_id = callback.data
    with ExecuteQuery(pool, commit=True) as cursor:
        cursor.execute(f"DELETE FROM step_tour "
                       f"WHERE step_tour_id = {step_tour_id};")
    await state.clear()
    await callback.message.edit_text(text='Удаление завершено!')
    await state.set_state(default_state)


# Здесь добавляем команды


@router.message(Command(commands=['add_team']))
async def add_team_handler(message: Message, state: FSMContext):
    """Приступаем к добавлению команды"""
    await message.answer(text='Введите название новой команды')
    await state.set_state(FSMStaffStates.choose_team)


@router.message(StateFilter(FSMStaffStates.choose_team))
async def define_team_handler(message: Message, state: FSMContext, bot: Bot):
    """Добавляем команду в базу данных"""
    with ExecuteQuery(pool, commit=True) as cursor:
        cursor.execute(f"INSERT INTO team(name) "
                       f"VALUES ('{message.text}');")
    await bot.send_message(chat_id=message.chat.id, text=f'Команда "{message.text}" добавлена!')
    await message.answer(text='Хотите добавить еще одну команду?',
                         reply_markup=create_inline_kb(width=2, yes='Да', no='Нет'))
    await state.set_state(FSMStaffStates.add_another_one_team)


@router.callback_query(StateFilter(FSMStaffStates.add_another_one_team))
async def add_another_one_team_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Добавляем еще одну команду, либо отказываемся"""
    if callback.data == 'yes':
        await callback.message.delete()
        await bot.send_message(chat_id=callback.message.chat.id, text='Введите название новой команды')
        await state.set_state(FSMStaffStates.choose_team)
    else:
        await callback.message.delete()
        await state.set_state(default_state)


# Здесь удаляем команду


@router.message(Command(commands=['delete_team']))
async def delete_team_handler(message: Message, state: FSMContext):
    """Приступаем к удалению команды"""
    with ExecuteQuery(pool) as cursor:
        cursor.execute("SELECT team_id, name FROM team;")
        teams = {str(id): name for id, name in cursor.fetchall()}
    if teams:
        await message.answer(text='Выберите команду, которую хотите удалить',
                             reply_markup=create_inline_kb(width=1, **teams))
        await state.set_state(FSMStaffStates.delete_team)
    else:
        await message.answer(text='Команды не найдены')


@router.callback_query(StateFilter(FSMStaffStates.delete_team))
async def confirm_delete_team_handler(callback: CallbackQuery, state: FSMContext):
    """Удаляем команду"""
    team_id = callback.data
    with ExecuteQuery(pool, commit=True) as cursor:
        cursor.execute(f"DELETE FROM team "
                       f"WHERE team_id = {team_id};")
    await callback.message.edit_text(text='Удаление завершено')
    await state.set_state(default_state)
