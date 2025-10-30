#посмортеть int is == с 256-го числа
#C3 алгоритм линеризации
#mro как работает
#патерны проеткирования

from functools import wraps
from typing import Callable

def limit(limit: int):
    def wrapper(func: Callable):
        @wraps(func)
        def inner(*args, **kwargs):
            nonlocal limit
            if limit == 0:
                return 'Limit'
            result = func(*args, **kwargs)
            limit -= 1
            return result
        return inner
    return wrapper

@limit(1)
def print_hi(message: str):
    """
    docstring about print hi
    """
    return f'{message}'

print(print_hi('HELLO'))
print(print_hi.__doc__)
