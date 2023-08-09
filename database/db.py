import psycopg2.pool
from config.config import load_db_password
from dataclasses import dataclass


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


@dataclass
class TourSchema:
    tour_id: int
    game_id: int
    tour_number: int
    title: str
    description: str
    option_1: str
    option_2: str
    option_3: str
    option_4: str
    answer: str
    wrong: int
    correct: int
#
# CREATE TABLE step_tour
# (
#     step_tour_id SERIAL PRIMARY KEY,
#     game_id INTEGER,
# 	tour_number INTEGER,
# 	title CHARACTER VARYING(50),
# 	description TEXT,
# 	option_1 CHARACTER VARYING(30),
# 	option_2 CHARACTER VARYING(30),
# 	option_3 CHARACTER VARYING(30),
# 	option_4 CHARACTER VARYING(30),
# 	answer CHARACTER VARYING(30),
# 	wrong INTEGER,
# 	correct INTEGER,
# 	FOREIGN KEY (game_id) REFERENCES game (game_id) ON DELETE CASCADE
# );
