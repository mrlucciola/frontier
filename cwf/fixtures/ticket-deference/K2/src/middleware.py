def require_token(handler):
    def wrapped(request):
        if request.get("token") != "secret":
            return {"status": 401, "body": "unauthorized"}
        return handler(request)

    return wrapped
