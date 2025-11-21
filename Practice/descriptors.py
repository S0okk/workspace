def func(*, digit_list: list, param: int) -> dict:
    if digit_list is None:
        digit_list = []
    new_param = param + 10
    digit_list.append(new_param)
    for_return = {
        105: digit_list,
        "304": 304,
        (1, 2, tuple(digit_list)): "tuple"
    }
    return for_return

f = func(digit_list=[1], param=2)
print(f)