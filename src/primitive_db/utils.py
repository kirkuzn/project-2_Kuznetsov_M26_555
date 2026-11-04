'''Вспомогательные функции для работы с файловой системой.'''

import json
import os

from primitive_db.constants import DATA_DIR, FILE_EXT


def load_metadata(storage_filepath):
    '''Загружает метаданные из JSON-файла.'''
    try:
        with open(storage_filepath, 'r', encoding='utf-8') as metadata_file:
            return json.load(metadata_file)
    except FileNotFoundError:
        return {}


def save_metadata(storage_filepath, metadata_to_save):
    '''Сохраняет метаданные в JSON-файл.'''
    with open(storage_filepath, 'w', encoding='utf-8') as metadata_file:
        json.dump(metadata_to_save, metadata_file, ensure_ascii=False, indent=4)


def load_table_data(table_name):
    '''Загружает записи таблицы из файла.'''
    table_storage_path = os.path.join(DATA_DIR, f'{table_name}{FILE_EXT}')
    try:
        with open(table_storage_path, 'r', encoding='utf-8') as table_data_file:
            return json.load(table_data_file)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    '''Сохраняет записи таблицы в файл.'''
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    table_storage_path = os.path.join(DATA_DIR, f'{table_name}{FILE_EXT}')
    with open(table_storage_path, 'w', encoding='utf-8') as table_data_file:
        json.dump(data, table_data_file, ensure_ascii=False, indent=4)