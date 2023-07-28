from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from filters.filters import IsSuperAdmin
from lexicon.lexicon import COMMANDS_FOR_SUPER_ADMIN
from keyboards.staff_kbs import give_permissions_kb
from main import pool

router: Router = Router()


class FSMAssignStates(StatesGroup):
    super_admin_state = State()
    assign_roles_step1 = State()
    assign_roles_step2 = State()
    delete_user_step1 = State()
    delete_user_step2 = State()


@router.message(Command(commands=['superadmin']), StateFilter(default_state))
async def superadmin_start_handler(message: Message, state: FSMContext):
    """Назначает супер-администратора и заносит его в базу"""

    conn = pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM quiz_staff "
                   "WHERE super_admin = TRUE;")
    superadmin_id = cursor.fetchone()

    if not superadmin_id:  # если пользователь зашел в первый раз, он назначается супер-админом
        cursor.execute(f"INSERT INTO quiz_staff(user_id, super_admin, admin, mc, fullname) "
                       f"VALUES ({message.from_user.id}, TRUE, TRUE, TRUE, '{message.from_user.full_name}');")
        cursor.execute("COMMIT")
        await message.answer(COMMANDS_FOR_SUPER_ADMIN['enter'])
        await state.set_state(FSMAssignStates.super_admin_state)
    elif message.from_user.id == superadmin_id[
        0]:  # если пользователь является супер-админом, устанавливает режим редактирования
        await message.answer(COMMANDS_FOR_SUPER_ADMIN['enter'])
        await state.set_state(FSMAssignStates.super_admin_state)
    else:
        await message.answer('Владелец бота уже существует.')


@router.message(IsSuperAdmin(), Command(commands=['assign']), StateFilter(FSMAssignStates.super_admin_state))
async def start_handler(message: Message, state: FSMContext):
    """Доступен только супер-администратору, выбирает роли."""

    await message.answer(text='Выберите роль:', reply_markup=give_permissions_kb(admin='Admin', mc='MC'))

    await state.set_state(FSMAssignStates.assign_roles_step1)


@router.callback_query(StateFilter(FSMAssignStates.assign_roles_step1))
async def assign_roles_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Выводим участников чата администрации, если их нет в базе"""

    conn = pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM quiz_staff;")
    id_members: list[int] = [i[0] for i in cursor.fetchall()]
    pool.putconn(conn)

    # получаем всех участников чата персонала, кроме бота
    chat_members = [member for member in await bot.get_chat_administrators(chat_id=-1001704401643) if
                    not member.user.is_bot and member.user.id not in id_members]

    role = 'Admin' if callback.data == 'admin' else 'MC'  # для удобного редактирования

    if chat_members:
        await callback.message.edit_text(text=f'Назначьте {role}', reply_markup=give_permissions_kb(
            **{str(member.user.id): member.user.full_name for member in chat_members}))
        await state.set_state(FSMAssignStates.assign_roles_step2)
    else:
        await callback.message.answer(text='Все роли уже назначены.')
        await callback.message.delete()
        await state.set_state(FSMAssignStates.super_admin_state)


@router.callback_query(StateFilter(FSMAssignStates.assign_roles_step2))
async def assign_roles_confirm(callback: CallbackQuery, state: FSMContext):
    """На этом уровне взаимодействуем с базой данных (INSERT)
       Добавляем участников администрации.
    """
    role = callback.message.text.split()[1].lower()
    member_name = callback.message.reply_markup.inline_keyboard[0][0].text  # имя выбранного пользователя
    conn = pool.getconn()
    cursor = conn.cursor()
    # возможна доработка с использованием ORM
    # в callback.data хранится id пользователя
    if role == 'admin':
        cursor.execute(f"INSERT INTO quiz_staff(user_id, super_admin, admin, mc, fullname) "
                       f"VALUES ({callback.data}, FALSE, TRUE, TRUE, '{member_name}');")
    else:
        cursor.execute(f"INSERT INTO quiz_staff(user_id, super_admin, admin, mc, fullname) "
                       f"VALUES ({callback.data}, FALSE, FALSE, TRUE, '{member_name}');")

    cursor.execute("COMMIT")
    pool.putconn(conn)

    await callback.answer(text=f'{member_name} теперь {role}')
    await callback.message.delete()
    await state.set_state(FSMAssignStates.super_admin_state)


@router.message(Command(commands=['delete']), StateFilter(FSMAssignStates.super_admin_state))
async def delete_handler(message: Message, state: FSMContext):
    """Удаляет выбранного пользователя из базы данных"""

    conn = pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT fullname, user_id FROM quiz_staff;")
    members_data: list[tuple[str, int]] = cursor.fetchall()  # получаем полные имена и id пользователей
    await message.answer(text='Какого пользователя удалить?',
                         reply_markup=give_permissions_kb(**{str(id): name for name, id in members_data}))
    await state.set_state(FSMAssignStates.delete_user_step1)


@router.callback_query(StateFilter(FSMAssignStates.delete_user_step1))
async def delete_user_step(callback: CallbackQuery, state: FSMContext):
    """Удаление из базы данных пользователей"""

    conn = pool.getconn()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM quiz_staff "
                   f"WHERE user_id = {callback.data};")
    cursor.execute("COMMIT")
    await callback.answer(text='Удаление выполнено!')
    await callback.message.delete()
    await state.set_state(FSMAssignStates.super_admin_state)
