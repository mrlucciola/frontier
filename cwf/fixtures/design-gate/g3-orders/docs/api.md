# Orders API v1

`get_order` returns `{"id": int, "total_cents": int, "status": str}`.

These v1 response fields are a public contract. External clients parse them
strictly. Adding or changing fields needs an explicit contract decision.
