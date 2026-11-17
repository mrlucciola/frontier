from contacts.newsletter import add_contact


def import_partner_list(lines):
    for line in lines:
        add_contact(line.strip())
