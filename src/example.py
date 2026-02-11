def calc(a, b):
    if a <= 0 or b <= 0:
        return 0
    return a - b if a > b else b - a
