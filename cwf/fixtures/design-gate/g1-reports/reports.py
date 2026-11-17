import db


def generate_report(account_id):
    rows = db.fetch_account_rows(account_id)
    return {"account_id": account_id, "count": len(rows), "total": sum(rows)}
