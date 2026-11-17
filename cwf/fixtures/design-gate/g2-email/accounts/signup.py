def _valid_email(email):
    return "@" in email and "." in email.split("@")[-1]


def create_account(name, email):
    if not _valid_email(email):
        raise ValueError("invalid email")
    return {"name": name, "email": email}
