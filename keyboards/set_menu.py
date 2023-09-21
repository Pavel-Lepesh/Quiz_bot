from aiogram import Bot
from aiogram.types import BotCommand

from lexicon.lexicon import MENU_COMMNADS_PLAYERS


async def set_players_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(
            command=command,
            description=description
        ) for command, description in MENU_COMMNADS_PLAYERS.items()
    ]
    await bot.set_my_commands(main_menu_commands)
