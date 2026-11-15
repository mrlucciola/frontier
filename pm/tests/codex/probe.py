"""usage: probe.py CAPTURE_FILE EVENT

A Codex hook that records what Codex sends and changes nothing. Appends one JSON line
{"event", "argv", "stdin"} to CAPTURE_FILE, prints nothing, always exits 0.
"""
import json
import sys


def main(argv):
    try:
        stdin = "" if sys.stdin is None or sys.stdin.isatty() else sys.stdin.read()
        line = json.dumps({"event": argv[2] if len(argv) > 2 else None,
                           "argv": argv[1:], "stdin": stdin})
        with open(argv[1], "a") as out:
            out.write(line + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
