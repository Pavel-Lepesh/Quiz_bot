from re import fullmatch


class GameValidationError(Exception):
    pass


def tour_validation(dict_values):
    for key in ['tour_number', 'quantity']:
        if not fullmatch(r'\d+', dict_values[key]):
            raise GameValidationError(f'Значение {key} должно быть числом!')


def step_tour_validation(dict_values):
    for key in ['step_tour_number', 'wrong', 'correct']:
        if not fullmatch(r'-?\d+', dict_values[key]):
            raise GameValidationError(f'Значение {key} должно быть числом!')

    if dict_values['answer'] not in ['option_1', 'option_2', 'option_3', 'option_4']:
        raise GameValidationError('answer должен соответствовать шаблону "option_n", где n - номер варианта от 1 до 4')
