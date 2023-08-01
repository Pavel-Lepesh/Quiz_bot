import psycopg2.pool
from config.config import load_db_password


pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    database="Quiz_members",
    user="postgres",
    password=load_db_password().tg_bot.db_password,
    host="127.0.0.1",
    port="5432"
)


class ExecuteQuery:
    """Выполняет в контексте роль курсора с его методами"""
    def __init__(self, current_pool, commit=False):
        self.pool = current_pool
        self.commit = commit

    def __enter__(self):
        self.conn = self.pool.getconn()
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.commit:
            self.cursor.execute('COMMIT')
        self.cursor.close()
        self.pool.putconn(self.conn)
