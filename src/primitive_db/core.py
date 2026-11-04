'''Управление таблицами и записями.'''

from primitive_db.constants import (
    BOOL_FALSE_VALUES,
    BOOL_TRUE_VALUES,
    ID_COLUMN,
    QUOTE_CHARS,
    TYPE_BOOL,
    TYPE_INT,
    VALID_TYPES,
)
from primitive_db.decorators import (
    confirm_action,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data


def _unquote(text):
    '''Убирает обрамляющие одинарные или двойные кавычки.'''
    return text.strip(QUOTE_CHARS)


def to_bool(value_to_convert):
    '''Приводит значение к bool или вызывает ValueError.'''
    value = _unquote(str(value_to_convert)).lower()
    if value in BOOL_TRUE_VALUES:
        return True
    if value in BOOL_FALSE_VALUES:
        return False
    raise ValueError(f'Некорректное значение: {value_to_convert}')


_CONVERTERS = {TYPE_INT: int, TYPE_BOOL: to_bool}


def _convert(value, type_name):
    '''Приводит значение к типу по его имени; по умолчанию — str.'''
    return _CONVERTERS.get(type_name, str)(value)


def _type_name_of(value):
    '''Возвращает имя типа значения: bool, int или None для str.'''
    if isinstance(value, bool):
        return TYPE_BOOL
    if isinstance(value, int):
        return TYPE_INT
    return None


def validate_condition(clause, table_schema):
    '''Проверяет типы значений условия по схеме таблицы.'''
    types_by_name = dict(table_schema)
    for column_name, raw_value in clause.items():
        column_type = types_by_name.get(column_name)
        if column_type == TYPE_INT:
            try:
                int(raw_value)
            except (TypeError, ValueError):
                raise ValueError(
                    f'Значение "{raw_value}" не приводится к int '
                    f'для столбца "{column_name}".'
                )
        elif column_type == TYPE_BOOL:
            to_bool(raw_value)


def _matches(record, clause):
    '''Проверяет, подходит ли запись под все условия фильтра.'''
    for key, value in clause.items():
        if key not in record:
            return False
        try:
            if _convert(value, _type_name_of(record[key])) != record[key]:
                return False
        except (TypeError, ValueError):
            return False
    return True


@handle_db_errors
def create_table(metadata, table_name, raw_columns):
    '''Создаёт таблицу, добавляет ID:int и сохраняет схему.'''
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return None

    columns = [[ID_COLUMN, TYPE_INT]]
    seen = {ID_COLUMN}

    for raw_column in raw_columns:
        if ':' not in raw_column:
            raise ValueError(
                f'Отсутствует разделитель в описании столбца: {raw_column}'
            )
        name, type_ = (
            _unquote(part) for part in raw_column.split(':', 1)
        )
        if type_ not in VALID_TYPES:
            raise ValueError(f'Неподдерживаемый тип данных: {type_}')
        if name == ID_COLUMN:
            continue
        if name in seen:
            raise ValueError(
                f'Обнаружен дубликат имени столбца: {name}'
            )
        seen.add(name)
        columns.append([name, type_])

    metadata[table_name] = columns
    columns_str = ', '.join(
        f'{name}:{type_}' for name, type_ in columns
    )
    print(
        f'Таблица "{table_name}" успешно создана '
        f'со столбцами: {columns_str}'
    )
    return metadata


def list_tables(metadata):
    '''Выводит список всех существующих таблиц.'''
    if not metadata:
        print('Нет созданных таблиц.')
        return
    for table_name in metadata:
        print(f'- {table_name}')


@handle_db_errors
@confirm_action('удаление таблицы')
def drop_table(metadata, table_name):
    '''Удаляет таблицу из метаданных после подтверждения.'''
    if table_name not in metadata:
        return None
    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    '''Проверяет значения, генерирует ID и добавляет запись.'''
    if table_name not in metadata:
        raise KeyError(table_name)

    schema = metadata[table_name]
    expected = len(schema) - 1
    if len(values) != expected:
        raise ValueError(
            f'Ожидалось {expected} значений, '
            f'получено {len(values)}.'
        )

    records = load_table_data(table_name)
    new_id = max(
        (int(r[ID_COLUMN]) for r in records), default=0
    ) + 1

    new_record = {ID_COLUMN: new_id}
    for (name, type_), value in zip(schema[1:], values):
        new_record[name] = _convert(value, type_)

    records.append(new_record)
    return records


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    '''Возвращает записи, подходящие под условие WHERE.'''
    if not where_clause:
        return table_data
    return [r for r in table_data if _matches(r, where_clause)]


@handle_db_errors
@log_time
def update(table_data, set_clause, where_clause):
    '''Обновляет поля записей, подходящих под условие WHERE.'''
    if ID_COLUMN in set_clause:
        raise ValueError(
            'Запрещено изменять уникальный идентификатор ID таблицы!'
        )

    for record in table_data:
        if not _matches(record, where_clause):
            continue
        for key, value in set_clause.items():
            if key in record:
                record[key] = _convert(
                    value, _type_name_of(record[key])
                )
    return table_data


@handle_db_errors
@confirm_action('удаление записей')
@log_time
def delete(table_data, where_clause):
    '''Удаляет записи, подходящие под условие WHERE.'''
    return [r for r in table_data if not _matches(r, where_clause)]


@handle_db_errors
def info(metadata, table_name, table_records):
    '''Печатает схему таблицы и количество записей в ней.'''
    schema = metadata[table_name]
    columns = ', '.join(
        f'{name}:{type_}' for name, type_ in schema
    )
    print(f'Таблица: {table_name}\nСтолбцы: {columns}')
    print(f'Количество записей: {len(table_records)}')