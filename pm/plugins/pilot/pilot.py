"""Shared by the pilot plugin's files: tickets labelled pilot and their contract."""
import datetime
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True

REVIEW_BY = re.compile(r"^\s*review_by:[ \t]*(\S*)", re.M)


def today():
    return (os.environ.get("PM_NOW") or datetime.datetime.utcnow().isoformat())[:10]


def open_pilots():
    out = subprocess.run(["pm", "ls", "label:pilot", "--json", "-n", "0"],
                         cwd=os.environ.get("PM_STORE") or None, stdout=subprocess.PIPE, universal_newlines=True)
    return [json.loads(line) for line in out.stdout.splitlines() if line.strip()]


def review_problem(t):
    """None when the review_by line is present and not past, else the sentence for it."""
    m = REVIEW_BY.search(t["body"])
    if not m:
        return "has no review_by: line"
    due = m.group(1)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", due):
        return "review_by %s is not YYYY-MM-DD" % (due or "(empty)")
    if due < today():
        return "review_by %s is past" % due
    return None


def overdue(t):
    m = REVIEW_BY.search(t["body"])
    return bool(m and re.match(r"^\d{4}-\d{2}-\d{2}$", m.group(1)) and m.group(1) < today())
