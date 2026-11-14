"""pm ticket note: append a timestamped note."""
import argparse

import store as st
from store import TicketError

NOTE_KINDS = ("worker-return", "park", "finding", "decision", "edit-trail",
              "provenance", "measurement")


class _IntermixedParser(argparse.ArgumentParser):
    """Lets options precede the optional text (`note <id> --kind k 'text'`)."""
    _plain = False

    def parse_known_args(self, args=None, namespace=None):
        if self._plain:
            return super().parse_known_args(args, namespace)
        self._plain = True
        try:
            return self.parse_known_intermixed_args(args, namespace)
        finally:
            self._plain = False


def register(subparsers):
    sp = subparsers.add_parser("note", help="append a timestamped note")
    # A single id: `nargs="+"` would swallow the positional text.
    sp.add_argument("id")
    sp.add_argument("text", nargs="?", help="note text (or pass --text)")
    sp.add_argument("--text", dest="text_flag", metavar="TEXT",
                    help="alias for the positional TEXT argument")
    sp.add_argument("--kind", choices=NOTE_KINDS,
                    help="note kind (spec v2 stores); omitted: an untyped note")
    sp.__class__ = _IntermixedParser


def run(args):
    with st.locked_store(getattr(args, "repo", None),
                         lambda: f"pm: note {args.id}"[:120]) as store:
        _note(args, store)


def _note(args, store):
    t = store.get(args.id)
    text = args.text_flag if args.text_flag is not None else args.text
    if not text:
        raise TicketError("note requires text: pass it positionally or with --text")
    if args.kind and store.config.get("spec_version", 1) < 2:
        raise TicketError("note --kind needs a spec_version 2 store")
    t["notes"].append(st.make_note(text, args.kind))
    t["updated"] = st.now()
    print(f"note added to {t['id']}")
