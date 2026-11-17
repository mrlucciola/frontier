_ORDERS = {1: {"total_cents": 1250, "status": "open", "currency": "EUR"}}


def get_order(order_id):
    o = _ORDERS[order_id]
    return {"id": order_id, "total_cents": o["total_cents"], "status": o["status"]}
