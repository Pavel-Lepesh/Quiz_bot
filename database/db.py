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
