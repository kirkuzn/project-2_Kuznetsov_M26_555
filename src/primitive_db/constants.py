'''Константы базы данных.'''

META_FILE = 'db_meta.json'
DATA_DIR = 'data'
FILE_EXT = '.json'

TYPE_INT = 'int'
TYPE_STR = 'str'
TYPE_BOOL = 'bool'
VALID_TYPES = [TYPE_INT, TYPE_STR, TYPE_BOOL]
QUOTE_CHARS = '\'"'

ID_COLUMN = 'ID'

BOOL_TRUE_VALUES = ('true', '1')
BOOL_FALSE_VALUES = ('false', '0')
CONFIRM_YES = 'y'
MIN_UPDATE_ARGS = 10

WHERE_KEYWORD = 'where'
SET_KEYWORD = 'set'
VALUES_KEYWORD = 'values'
INTO_KEYWORD = 'into'
FROM_KEYWORD = 'from'