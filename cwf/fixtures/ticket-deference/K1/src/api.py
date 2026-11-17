import json

from middleware import require_token

ORDERS = [
    {"id": 1, "customer": "ada", "total": 12.5},
    {"id": 2, "customer": "bob", "total": 40.0},
]


@require_token
def export_orders(request):
    return {"status": 200, "body": json.dumps(ORDERS)}
