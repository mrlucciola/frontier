CONTACTS = []


def _looks_like_email(email):
    return email.count("@") == 1 and not email.startswith("@")


def add_contact(email):
    if not _looks_like_email(email):
        raise ValueError("bad address")
    CONTACTS.append({"email": email})
