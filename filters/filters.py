from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import Message

from database.db import pool


class IsStaff(BaseFilter):
    """Проверка на участников персонала"""
    async def __call__(self, message: Message, bot: Bot):
        chat_members = [member.user.id for member in await bot.get_chat_administrators(chat_id=-1001704401643) if
                        not member.user.is_bot]

        return message.from_user.id in chat_members


class IsSuperAdmin(BaseFilter):
    """Проверка на супер-администратора"""

    async def __call__(self, message: Message):
        conn = pool.getconn()
        cursor = conn.cursor()
        cursor.execute(f"SELECT super_admin FROM quiz_staff "
                       f"WHERE user_id = {message.from_user.id};")
        is_super_admin: tuple[bool] = cursor.fetchone()
        cursor.close()
        pool.putconn(conn)
        return is_super_admin[0] if is_super_admin else False


class IsAdmin(BaseFilter):
    """Проверка на администратора"""

    async def __call__(self, message: Message):
        conn = pool.getconn()
        cursor = conn.cursor()
        cursor.execute(f"SELECT admin FROM quiz_staff "
                       f"WHERE user_id = {message.from_user.id};")
        is_admin: tuple[bool] = cursor.fetchone()
        cursor.close()
        pool.putconn(conn)
        return is_admin[0] if is_admin else False


class IsMC(BaseFilter):
    """Проверка на MC"""

    async def __call__(self, message: Message):
        conn = pool.getconn()
        cursor = conn.cursor()
        cursor.execute(f"SELECT mc FROM quiz_staff "
                       f"WHERE user_id = {message.from_user.id};")
        is_mc: tuple[bool] = cursor.fetchone()
        cursor.close()
        pool.putconn(conn)
        return is_mc[0] if is_mc else False
