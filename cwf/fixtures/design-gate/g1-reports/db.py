import time

_ROWS = {1: [10, 20, 30], 2: [5, 5]}


def fetch_account_rows(account_id):
    time.sleep(2)
    return list(_ROWS.get(account_id, []))
