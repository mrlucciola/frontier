# Mailing services

- `accounts/signup.py`: creates an account from a signup request and subscribes
  the address to the newsletter.
- `contacts/newsletter.py`: stores newsletter contacts. It is also used by the
  newsletter form and by the partner list import in `contacts/importer.py`.

Each module checks email addresses its own way.
