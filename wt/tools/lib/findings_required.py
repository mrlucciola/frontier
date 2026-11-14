"""Does this store require --findings on done?

usage: findings_required.py STORE_REPO

Exit 0 when STORE_REPO/.pm/config.json has `findings_required` true; exit 1 when it is
false, absent, or the file is missing or unreadable.
"""
import json
import os
import sys


def main(argv):
    if len(argv) != 1:
        sys.stderr.write(__doc__)
        return 2
    try:
        with open(os.path.join(argv[0], ".pm", "config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        return 1
    return 0 if isinstance(cfg, dict) and cfg.get("findings_required") is True else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
