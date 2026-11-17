from contacts.newsletter import add_contact


def _valid_email(email):
    return "@" in email and "." in email.split("@")[-1]


def create_account(name, email):
    if not _valid_email(email):
        raise ValueError("invalid email")
    add_contact(email)
    return {"name": name, "email": email}
