'''Парсеры для сложных команд.'''

from primitive_db.constants import QUOTE_CHARS


def parse_where(expression_elements):
    '''Превращает элементы WHERE в словарь.'''
    if len(expression_elements) == 3 and expression_elements[1] == '=':
        key = expression_elements[0].strip(QUOTE_CHARS)
        value = expression_elements[2].strip(QUOTE_CHARS)
        return {key: value}
    return None


def parse_set(expression_elements):
    '''Превращает элементы SET в словарь.'''
    if len(expression_elements) == 3 and expression_elements[1] == '=':
        key = expression_elements[0].strip(QUOTE_CHARS)
        value = expression_elements[2].strip(QUOTE_CHARS)
        return {key: value}
    return None


def _split_respecting_quotes(text, separator):
    '''Делит строку.'''
    parts = []
    current_chars = []
    active_quote = None
    for char in text:
        if active_quote is None:
            if char in QUOTE_CHARS:
                active_quote = char
                current_chars.append(char)
            elif char == separator:
                parts.append(''.join(current_chars))
                current_chars = []
            else:
                current_chars.append(char)
        else:
            current_chars.append(char)
            if char == active_quote:
                active_quote = None
    parts.append(''.join(current_chars))
    return parts


def parse_values(values_arguments):
    '''Делит аргументы на значения'''
    cleaned_values = []
    for argument in values_arguments:
        for piece in _split_respecting_quotes(argument, ','):
            without_delimiters = piece.strip('() ')
            if without_delimiters == '':
                continue
            cleaned_values.append(without_delimiters.strip(QUOTE_CHARS))
    return cleaned_values