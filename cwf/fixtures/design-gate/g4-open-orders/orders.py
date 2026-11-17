ORDERS = [
    {"id": 1, "status": "open"},
    {"id": 2, "status": "shipped"},
    {"id": 3, "status": "open"},
    {"id": 4, "status": "cancelled"},
]


def orders_with_status(status, orders=None):
    return [o for o in (ORDERS if orders is None else orders) if o["status"] == status]
