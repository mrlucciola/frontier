# Reports service

`reports.generate_report(account_id)` builds an account report from the database.
The database fetch in `db.py` is slow. Reports are served by several worker processes.
