from aiogram.filters import BaseFilter
from aiogram.types import Message

from database.db import pool


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
        return is_admin[0]


class IsMC(BaseFilter):
    """Проверка на MC"""

    async def __call__(self, message: Message):
        conn = pool.getconn()
        cursor = conn.cursor()
        cursor.execute(f"SELECT mc FROM quiz_staff "
                       f"WHERE user_id = {message.from_user.id};")
        is_mc: tuple[bool] = cursor.fetchall()
        cursor.close()
        pool.putconn(conn)
        return is_mc[0]
