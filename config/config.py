from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str = None
    db_password: str = None


@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(tg_bot=TgBot(token=env('BOT_TOKEN')))


def load_db_password(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(tg_bot=TgBot(db_password=env('DATABASE_PASSWORD')))
