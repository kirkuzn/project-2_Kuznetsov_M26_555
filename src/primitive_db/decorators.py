"""Модуль декораторов базы данных."""

import time

from primitive_db.constants import CONFIRM_YES


def handle_db_errors(target_function):
    """Декоратор для обработки ошибок."""
    def error_wrapper(*args, **kwargs):
        try:
            return target_function(*args, **kwargs)
        except FileNotFoundError:
            print(
                'Ошибка: Файл данных не найден. '
                'Возможно, база данных не инициализирована.'
            )
            return None
        except KeyError as exception_error:
            print(f'Ошибка: Таблица или столбец {exception_error} не найден.')
            return None
        except ValueError as exception_error:
            print(f'Ошибка валидации: {exception_error}')
            return None
        except Exception as exception_error:
            print(f'Произошла непредвиденная ошибка: {exception_error}')
            return None
    return error_wrapper


def confirm_action(action_display_name):
    """Декоратор для обработки подтверждений операций."""
    def decorator_wrapper(target_function):
        def action_wrapper(*args, **kwargs):
            confirmation_prompt = input(
                f'Вы уверены, что хотите выполнить '
                f'"{action_display_name}"? [y/n]: '
            ).strip().lower()
            if confirmation_prompt == CONFIRM_YES:
                return target_function(*args, **kwargs)
            print('Операция отменена пользователем.')
            return None
        return action_wrapper
    return decorator_wrapper


def log_time(target_function):
    """Декоратор для вывода времени выполнения функции."""
    def time_wrapper(*args, **kwargs):
        start_monotonic_time = time.monotonic()
        execution_result = target_function(*args, **kwargs)
        end_monotonic_time = time.monotonic()
        total_elapsed_seconds = end_monotonic_time - start_monotonic_time
        print(
            f'Функция <{target_function.__name__}> выполнилась за '
            f'{total_elapsed_seconds:.3f} секунд.'
        )
        return execution_result
    return time_wrapper


def create_cacher():
    """Создает кэш."""
    query_cache_storage = {}

    def cache_result(cache_key, fetch_value_function):
        """Возвращает значение из кэша."""
        if cache_key not in query_cache_storage:
            query_cache_storage[cache_key] = fetch_value_function()
        return query_cache_storage[cache_key]

    return cache_result, query_cache_storage