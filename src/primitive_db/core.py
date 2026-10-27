VALID_TYPES = {'int', 'str', 'bool'}

# Создание таблицы, добавление в метаданные.
def create_table (metadata, table_name, columns):
    if table_name in metadata:
        print(f'Ошибка: Таблица \'{table_name}\' уже существует.')
        return None
    first_columns = [['ID', 'int']]
    for raw_column in columns:
        if ':' not in raw_column:
            print(f'Некорректное значение: {raw_column}. Попробуйте снова.')
            return None
        columns_name, columns_type = raw_column.split(':', 1)
        if columns_type not in VALID_TYPES:
            print(f'Некорректное значение: {raw_column}. Попробуйте снова.')
            return None
        if columns_name == 'ID':
            continue
        first_columns.append([columns_name, columns_type])
    metadata[table_name] = first_columns
    columns_str = ', '.join([f'{name}:{data_type}' for name, data_type in first_columns])    
    print(f'Таблица \'{table_name}\' успешно создана со столбцами: {columns_str} ')
    return metadata


# Фукция списка вывода таблиц.
def list_tables(metadata):
    if not metadata:
        print('Нет созданных таблиц.')
        return
    for table_name in metadata:
        print(f'- {table_name}')
    
# Функция удаления таблицы.
def drop_table(metadata, table_name):
    if table_name not in metadata:
        print(f'Ошибка: Таблица \'{table_name}\' не существует ')
        return None
    del metadata[table_name]
    print(f'Таблица \'{table_name}\' успешно удалена')
    return metadata