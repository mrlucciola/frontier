def change(value, delta):
    if value + delta < 0:
        raise ValueError('overdraft')
    return value + delta
