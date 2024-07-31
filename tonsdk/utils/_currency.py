import decimal
import logging
from enum import Enum
from typing import Any, Union


class TonCurrencyEnum(str, Enum):
    nanoton = 'nanoton'
    ton = 'ton'


units = {
    TonCurrencyEnum.nanoton:       decimal.Decimal('1'),
    TonCurrencyEnum.ton:           decimal.Decimal('1000000000'),
}

integer_types = (int,)
string_types = (bytes, str, bytearray)

MIN_VAL = 0
MAX_VAL = 2 ** 256 - 1


def is_integer(value: Any) -> bool:
    return isinstance(value, integer_types) and not isinstance(value, bool)


def is_string(value: Any) -> bool:
    return isinstance(value, string_types)


def to_nano(number: Union[int, float, str, decimal.Decimal], unit: str) -> int:
    """
    Конвертируйте заданную сумму из указанной единицы в нанограммы, наименьшую единицу криптовалюты TON.
    number (Union[int, float, str, decimal.Decimal]): Количество, которое нужно преобразовать в нанограммы.
        Это может быть целое число, число с плавающей точкой, строка или decimal.Decimal.
    unit (str, необязательно): Единица измерения числового параметра . По умолчанию «ton». Поддерживаемые единицы:
        «тонна»: сумма в ТОННАХ.
        «нано»: количество уже указано в нанограммах.
        «микро»: сумма в микроТОННАХ.
        «милли»: Сумма в миллитоннах.
        «килотонна»: количество указывается в килотоннах.
        «мегатонна»: сумма в мегатоннах.
        «гигатонна»: сумма в гигатоннах.
    return: int : Преобразованное количество в нанограммах.
    """
    logging.info(f'number: {number}, type(number): {type(number)}')
    # проверка что единицы ton или nanoton
    if unit.lower() not in units:
        raise ValueError(
            "Unknown unit.  Must be one of {0}".format("/".join(units.keys()))
        )
    # если number строка, то переводим в число
    if is_integer(number) or is_string(number):
        d_number = decimal.Decimal(value=number)
    # если number float
    elif isinstance(number, float):
        d_number = decimal.Decimal(value=str(number))
    # если number число
    elif isinstance(number, decimal.Decimal):
        d_number = number
    else:
        raise TypeError(
            "Unsupported type.  Must be one of integer, float, or string")

    s_number = str(number)
    # получаем ключ по init
    unit_value = units[unit.lower()]
    # если number == 0
    if d_number == decimal.Decimal(0):
        return 0
    logging.info(f's_number: {s_number}, d_number: {d_number}')
    if d_number < 1 and "." in s_number:
        with decimal.localcontext() as ctx:
            multiplier = len(s_number) - s_number.index(".") - 1
            print("multiplier", multiplier)
            ctx.prec = multiplier
            d_number = decimal.Decimal(
                value=number, context=ctx) * 10 ** multiplier
        unit_value /= 10 ** multiplier
    print("d_number decimal.localcontext", d_number)
    with decimal.localcontext() as ctx:
        ctx.prec = 999
        result_value = decimal.Decimal(
            value=d_number, context=ctx) * unit_value
    print("result_value", result_value)
    if result_value < MIN_VAL or result_value > MAX_VAL:
        raise ValueError(
            "Resulting nanoton value must be between 1 and 2**256 - 1")

    return int(result_value)


def from_nano(number: int, unit: str) -> Union[int, decimal.Decimal]:
    """
    Конвертировать указанное количество из нанограммов в указанную единицу криптовалюты TON.
    Параметры:
        number (целое): Количество в нанограммах, которое необходимо преобразовать.
        unit (str, необязательно): Целевая единица для преобразования числа . По умолчанию «ton». Поддерживаемые единицы:
            «тонна»: конвертировать в ТОННУ.
            «нано»: преобразование не требуется, так как количество уже указано в нанограммах.
            «микро»: конвертировать в микро TON.
            «милли»: конвертировать в милли-ТОННУ.
            «килотонна»: перевести в килотонну.
            «мегатонна»: конвертировать в мегатонну.
            «гигатонна»: конвертировать в гигатонну.
    Возврат:
        int : Преобразованная сумма в указанной единице.
    Поднимает:
        ValueError : Если предоставленное число не является допустимым целым числом или указана неподдерживаемая единица измерения.
    """
    logging.info(f'from_nano: {number}, {unit}')
    if unit.lower() not in units:
        raise ValueError(
            "Unknown unit.  Must be one of {0}".format("/".join(units.keys()))
        )

    if number == 0:
        return 0
    # MIN_VAL = 0
    # MAX_VAL = 2 ** 256 - 1
    if number < MIN_VAL or number > MAX_VAL:
        print("number", number, "number < MIN_VAL", number < MIN_VAL, "number > MAX_VAL", number > MAX_VAL)
        raise ValueError("value must be between 1 and 2**256 - 1")

    unit_value = units[unit.lower()]

    with decimal.localcontext() as ctx:
        ctx.prec = 999
        d_number = decimal.Decimal(value=number, context=ctx)
        result_value = d_number / unit_value

    return result_value
