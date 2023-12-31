COMMANDS_FOR_SUPER_ADMIN = {
    'enter': 'Добро пожаловать, супер-админ!\n'
             'Вы находитесь в режиме редактирования\n'
             'Список доступных команд:\n\n'
             '/assign - чтобы назначить роли участникам чата\n'
             '/delete - чтобы разжаловать участника чата\n'
             '/exit - чтобы выйти из режима редактирования'
}

COMMANDS_FOR_STAFF = {
    'info': '<b>Список команд для персонала</b>\n\n'
            'Список доступных команд:\n'
            '/superadmin - меню доступное супер-администратору\n'
            '/select_or_add_the_game - выберите игру для редактирования, либо создайте новую\n'
            '/delete - меню для удаления игр <i>(в том числе степов и туров)</i>\n'
            '/add_team - добавьте команду\n'
            '/edit_players - редактировать состав команды <i>(удаление игроков и назначение администраторов)</i>\n'
            '/delete_team - удалить команду\n'
            '/exit_edit - используйте для выхода из режимов редактирования игры, сбрасывает чат до первоначального состояния<i>(при выходе уже введенные данные стираются)</i>',
    'not_handled': 'Я могу отвечать только на определенные команды 🤷‍♂️\n\n'
                   'Если вы находитесь в режиме редактирования и хотите завершить сеанс, введите команду /exit_edit'
}

COMMANDS_FOR_PLAYERS = {
    'start': 'Привет! Давай выберем твою команду',
    'wrong_answer': 'Введите команду /start чтобы снова приступить к выбору команды\n\n'
                    'Если у вас возникли проблемы введите команду /help',
    'complete_registration': 'Отлично! Вы зарегистрированы. Ожидайте начала игры.',
    'rules': ''
}

COMMANDS_FOR_MC = {
    'info': '<b>Команды для Ведущего:</b>\n'
            '/start_game - выбираем игру в которую будем играть, все дальнейшие команды '
            'будут относится к ней\n'
            '/go - запустить процесс выбора вопроса для отправки игрокам\n'
            '/exit_game - выйти из игры'
}

MENU_COMMNADS_PLAYERS = {
    '/rules': 'правила игры',
    '/help': 'попросить ведущего подойти к вам'
}
