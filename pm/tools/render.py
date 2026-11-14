"""Everything the user reads: refusals, usage errors, ticket text."""
import argparse
import sys


def refuse(text):
    sys.stderr.write("pm: %s\n" % text)
    sys.exit(1)


def usage_error(doc, text):
    sys.stderr.write("pm: %s\n%s\n" % (text, doc.strip().split("\n")[0]))
    sys.exit(2)


class _Parser(argparse.ArgumentParser):
    def __init__(self, doc):
        super().__init__(add_help=False)
        self.doc = doc

    def error(self, message):
        usage_error(self.doc, message[:1].lower() + message[1:] + ".")


def parser(doc):
    return _Parser(doc)
