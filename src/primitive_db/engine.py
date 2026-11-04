"""Обработка команд пользователя."""

import os
import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import (
    DATA_DIR,
    FILE_EXT,
    FROM_KEYWORD,
    ID_COLUMN,
    INTO_KEYWORD,
    META_FILE,
    MIN_UPDATE_ARGS,
    QUOTE_CHARS,
    SET_KEYWORD,
    VALUES_KEYWORD,
    WHERE_KEYWORD,
)
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    info,
    insert,
    list_tables,
    select,
    update,
    validate_condition,
)
from primitive_db.decorators import create_cacher
from primitive_db.parser import parse_set, parse_values, parse_where
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

query_cacher_function, active_cache_dictionary = create_cacher()


def print_help():
    """Выводит справочную информацию о доступных командах."""
    print('***Операции с данными***')
    print()
    print('Функции:')
    print(
        '<command> create_table <имя_таблицы> '
        '<столбец1:тип> .. - создать таблицу'
    )
    print('<command> list_tables - показать список всех таблиц')
    print('<command> drop_table <имя_таблицы> - удалить таблицу')
    print(
        '<command> insert into <имя_таблицы> values '
        '(<значение1>, <значение2>, ...) - создать запись.'
    )
    print(
        '<command> select from <имя_таблицы> where '
        '<столбец> = <значение> - прочитать записи.'
    )
    print('<command> select from <имя_таблицы> - прочитать все записи.')
    print(
        '<command> update <имя_таблицы> set <столбец1> = <новое_значение1> '
        'where .. - обновить запись.'
    )
    print(
        '<command> delete from <имя_таблицы> where '
        '<столбец> = <значение> - удалить запись.'
    )
    print('<command> info <имя_таблицы> - вывести информацию о таблице.')
    print('<command> exit - выход из программы')
    print('<command> help - справочная информация')


def show_formatted_table(table_schema, records_list):
    """Выводит записи в виде таблицы."""
    table_column_names = [column_info[0] for column_info in table_schema]
    pretty_table_renderer = PrettyTable(table_column_names)
    for row_record in records_list:
        pretty_table_renderer.add_row(
            [row_record.get(name, '') for name in table_column_names]
        )
    print(pretty_table_renderer)


def _require_table(metadata, table_name):
    """Возвращает схему таблицы или None."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None
    return metadata[table_name]


def _validate_clause(clause, table_schema):
    """Проверка типов по условию."""
    try:
        validate_condition(clause, table_schema)
        return True
    except ValueError as error:
        print(f'Ошибка валидации: {error}')
        return False


def _columns_missing(clause, schema_keys):
    """Проверяет колонки и печатает ошибку."""
    for column in clause:
        if column not in schema_keys:
            print(f'Ошибка: Таблица или столбец {column} не найден.')
            return True
    return False


def _print_affected(table_name, action_singular, action_plural,
                    affected_ids, from_table=False):
    """Сообщает, какие записи изменены."""
    if len(affected_ids) == 1:
        if from_table:
            print(
                f'Запись с ID={affected_ids[0]} '
                f'успешно {action_singular} '
                f'из таблицы "{table_name}".'
            )
        else:
            print(
                f'Запись с ID={affected_ids[0]} '
                f'в таблице "{table_name}" '
                f'успешно {action_singular}.'
            )
        return
    ids_list = ', '.join(str(record_id) for record_id in affected_ids)
    if from_table:
        print(
            f'Записи с ID {ids_list} '
            f'успешно {action_plural} '
            f'из таблицы "{table_name}".'
        )
    else:
        print(
            f'Записи с ID {ids_list} '
            f'в таблице "{table_name}" '
            f'успешно {action_plural}.'
        )


def run(storage_filepath=META_FILE):
    """Цикл чтения и выполнения команд."""
    print_help()
    print()

    while True:
        try:
            user_input_string = prompt.string('>>>Введите команду: ').strip()
            if not user_input_string:
                continue

            current_metadata = load_metadata(storage_filepath)
            command_arguments = shlex.split(user_input_string, posix=False)

            if not command_arguments:
                continue
            command_name = command_arguments[0].strip(QUOTE_CHARS)

            match command_name:
                case 'exit':
                    break

                case 'help':
                    print_help()

                case 'list_tables':
                    list_tables(current_metadata)

                case 'create_table':
                    if len(command_arguments) < 3:
                        print('Ошибка: Не указано имя таблицы или столбцы.')
                        continue
                    table_name = command_arguments[1].strip(QUOTE_CHARS)
                    updated_metadata = create_table(
                        current_metadata, table_name, command_arguments[2:]
                    )
                    if updated_metadata is not None:
                        save_metadata(storage_filepath, updated_metadata)
                        active_cache_dictionary.clear()

                case 'drop_table':
                    if len(command_arguments) < 2:
                        print('Ошибка: Не указано имя таблицы.')
                        continue
                    table_name = command_arguments[1].strip(QUOTE_CHARS)
                    if _require_table(current_metadata, table_name) is None:
                        continue
                    updated_metadata = drop_table(current_metadata, table_name)
                    if updated_metadata is not None:
                        save_metadata(storage_filepath, updated_metadata)
                        try:
                            table_data_path = os.path.join(
                                DATA_DIR, f'{table_name}{FILE_EXT}'
                            )
                            os.remove(table_data_path)
                        except FileNotFoundError:
                            pass
                        active_cache_dictionary.clear()

                case 'insert':
                    if (
                        len(command_arguments) < 5
                        or command_arguments[1] != INTO_KEYWORD
                        or command_arguments[3] != VALUES_KEYWORD
                    ):
                        print('Ошибка: Неверный синтаксис команды INSERT.')
                        continue
                    table_name = command_arguments[2].strip(QUOTE_CHARS)
                    if _require_table(current_metadata, table_name) is None:
                        continue
                    cleaned_values = parse_values(command_arguments[4:])
                    updated_data = insert(
                        current_metadata, table_name, cleaned_values
                    )
                    if updated_data is not None:
                        save_table_data(table_name, updated_data)
                        print(
                            f'Запись с ID={updated_data[-1][ID_COLUMN]} '
                            f'успешно добавлена в таблицу "{table_name}".'
                        )
                        active_cache_dictionary.clear()

                case 'select':
                    if (
                        len(command_arguments) < 3
                        or command_arguments[1] != FROM_KEYWORD
                    ):
                        print('Ошибка: Неверный синтаксис команды SELECT.')
                        continue
                    table_name = command_arguments[2].strip(QUOTE_CHARS)
                    table_schema = _require_table(current_metadata, table_name)
                    if table_schema is None:
                        continue

                    if len(command_arguments) == 3:
                        cache_lookup_key = f'{table_name}_all'
                        records = query_cacher_function(
                            cache_lookup_key,
                            lambda: load_table_data(table_name),
                        )
                        if records is not None:
                            show_formatted_table(table_schema, records)
                    elif (
                        len(command_arguments) >= 5
                        and command_arguments[3] == WHERE_KEYWORD
                    ):
                        filter_criteria = parse_where(command_arguments[4:])
                        if not filter_criteria:
                            print('Некорректное значение выражения WHERE.')
                            continue
                        target_key = next(iter(filter_criteria))
                        schema_keys = [col[0] for col in table_schema]
                        if target_key not in schema_keys:
                            print(f'Ошибка: Столбец {target_key} не найден.')
                            continue
                        if not _validate_clause(filter_criteria, table_schema):
                            continue
                        cache_lookup_key = (
                            f'{table_name}_{target_key}_'
                            f'{filter_criteria[target_key]}'
                        )
                        selected_records = query_cacher_function(
                            cache_lookup_key,
                            lambda: select(
                                load_table_data(table_name),
                                filter_criteria,
                            ),
                        )
                        if selected_records is not None:
                            show_formatted_table(table_schema, selected_records)
                    else:
                        print('Ошибка: Неверный синтаксис выражения WHERE.')

                case 'update':
                    if (
                        len(command_arguments) < MIN_UPDATE_ARGS
                        or command_arguments[2] != SET_KEYWORD
                    ):
                        print('Ошибка: Неверный синтаксис команды UPDATE.')
                        continue
                    try:
                        where_index = command_arguments.index(WHERE_KEYWORD, 3)
                    except ValueError:
                        print(
                            'Ошибка: Неверный синтаксис команды UPDATE — '
                            'отсутствует WHERE.'
                        )
                        continue
                    table_name = command_arguments[1].strip(QUOTE_CHARS)
                    table_schema = _require_table(current_metadata, table_name)
                    if table_schema is None:
                        continue

                    set_clause = parse_set(command_arguments[3:where_index])
                    where_clause = parse_where(command_arguments[where_index + 1:])
                    if not set_clause or not where_clause:
                        print('Некорректное значение в выражениях.')
                        continue

                    schema_keys = [col[0] for col in table_schema]
                    if _columns_missing(set_clause, schema_keys):
                        continue
                    if _columns_missing(where_clause, schema_keys):
                        continue

                    if not _validate_clause(set_clause, table_schema):
                        continue
                    if not _validate_clause(where_clause, table_schema):
                        continue

                    current_table_data = load_table_data(table_name)
                    matched_records = select(current_table_data, where_clause)
                    if not matched_records:
                        print('Записей, подходящих под условие, не найдено.')
                        continue

                    affected_ids = [
                        record[ID_COLUMN] for record in matched_records
                    ]
                    updated_data = update(
                        current_table_data, set_clause, where_clause
                    )
                    if updated_data is not None:
                        save_table_data(table_name, updated_data)
                        _print_affected(
                            table_name, 'обновлена', 'обновлены', affected_ids
                        )
                        active_cache_dictionary.clear()

                case 'delete':
                    if (
                        len(command_arguments) < 5
                        or command_arguments[1] != FROM_KEYWORD
                        or command_arguments[3] != WHERE_KEYWORD
                    ):
                        print('Ошибка: Неверный синтаксис команды DELETE.')
                        continue
                    table_name = command_arguments[2].strip(QUOTE_CHARS)
                    table_schema = _require_table(current_metadata, table_name)
                    if table_schema is None:
                        continue

                    filter_criteria = parse_where(command_arguments[4:])
                    if not filter_criteria:
                        print('Некорректное значение выражения WHERE.')
                        continue

                    schema_keys = [col[0] for col in table_schema]
                    if _columns_missing(filter_criteria, schema_keys):
                        continue
                    if not _validate_clause(filter_criteria, table_schema):
                        continue

                    current_table_data = load_table_data(table_name)
                    matched_records = select(current_table_data, filter_criteria)
                    if not matched_records:
                        print('Записей, подходящих под условие, не найдено.')
                        continue

                    affected_ids = [
                        record[ID_COLUMN] for record in matched_records
                    ]
                    remaining_records = delete(
                        current_table_data, filter_criteria
                    )
                    if remaining_records is not None:
                        save_table_data(table_name, remaining_records)
                        _print_affected(
                            table_name, 'удалена', 'удалены', affected_ids,
                            from_table=True,
                        )
                        active_cache_dictionary.clear()

                case 'info':
                    if len(command_arguments) < 2:
                        print('Ошибка: Не указано имя таблицы.')
                        continue
                    table_name = command_arguments[1].strip(QUOTE_CHARS)
                    if _require_table(current_metadata, table_name) is None:
                        continue
                    current_table_data = load_table_data(table_name)
                    info(current_metadata, table_name, current_table_data)

                case _:
                    print(f'Функции {command_name} нет. Попробуйте снова.')

        except KeyboardInterrupt:
            print('Выход из программы.')
            raise SystemExit