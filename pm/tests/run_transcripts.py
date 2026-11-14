#!/usr/bin/python3
"""Run the pm transcripts: each one is a shell session with its exact expected output.

    /usr/bin/python3 -B pm/tests/run_transcripts.py [--cli pm/cli/pm] [-k NAME ...] [--allow-pending] [-v]

A transcript is a text file under pm/tests/t/. Its format:

    Unindented lines are comments.
      $ pm new "first ticket"
      t-1
      $ pm take t-9
      pm: no ticket t-9. Search: pm ls all <words>
      [1]

A line starting with two spaces and `$ ` is a command. Lines starting `  > ` continue
it. The indented lines after it are the output it must print, stdout and stderr
together. A last line `[N]` is its exit code when that is not 0. Blank lines inside
the output are blank output lines; trailing blank lines are ignored on both sides.

Every transcript runs in one `sh`, so `cd` and `export` carry from one command to the
next. It starts in an empty directory `$T/work` with a private HOME, a fixed clock and
a fixed identity (see ENV below). The temporary directory prints as `$T`.
`$FIXTURES` is pm/tests/fixtures and `$PLUGINS` is pm/plugins.

While pm is being built, a verb that does not exist yet appends its name to the file
in $PM_UNBUILT_LOG and exits 70. A transcript whose first wrong step comes at or
after such a call counts as `pending`. One whose first wrong step comes before any
is `failed`: a built verb is wrong. The run exits 0 only when nothing failed and,
unless --allow-pending is given, nothing is pending.
"""
import argparse
import difflib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SALT = "---transcript-step"

# What every transcript starts with. A transcript changes these with `export`.
ENV = {
    "PM_NOW": "2026-01-01T00:00:00Z",   # pm reads the clock from here when set
    "PM_ACTOR": "ada",
    "PM_SESSION_ID": "s1",
    "LC_ALL": "C",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
}


def parse(path):
    """Return [(line number, command, expected output lines, expected exit code)]."""
    steps = []
    current = None
    with open(path) as f:
        for number, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if line.startswith("  $ "):
                current = [number, line[4:], [], 0]
                steps.append(current)
            elif line.startswith("  > ") and current and not current[2]:
                current[1] += "\n" + line[4:]
            elif line.startswith("  ") and current:
                current[2].append(line[2:])
            elif line.strip() == "" and current:
                current[2].append("")
            else:
                current = None  # a comment ends the step
    for step in steps:
        while step[2] and step[2][-1] == "":
            step[2].pop()
        last = step[2][-1] if step[2] else ""
        if last.startswith("[") and last.endswith("]") and last[1:-1].isdigit():
            step[3] = int(step[2].pop()[1:-1])
            while step[2] and step[2][-1] == "":
                step[2].pop()
    return steps


def run_one(path, cli):
    """Run one transcript. Return (problems, unbuilt verb names)."""
    steps = parse(path)
    tmp = os.path.realpath(tempfile.mkdtemp(prefix="pm-t-"))
    try:
        for name in ("work", "home", "bin", "plugins"):
            os.mkdir(os.path.join(tmp, name))
        os.symlink(cli, os.path.join(tmp, "bin", "pm"))
        unbuilt = os.path.join(tmp, "unbuilt")
        open(unbuilt, "w").close()

        env = dict(ENV, T=tmp, HOME=os.path.join(tmp, "home"),
                   FIXTURES=os.path.join(HERE, "fixtures"),
                   PLUGINS=os.path.join(os.path.dirname(HERE), "plugins"),
                   PATH=os.path.join(tmp, "bin") + ":/usr/bin:/bin",
                   PM_STORES=os.path.join(tmp, "stores"),
                   PM_PLUGINS=os.path.join(tmp, "plugins"),
                   PM_UNBUILT_LOG=unbuilt, TMPDIR=tmp)
        script = []
        for index, (_, command, _, _) in enumerate(steps):
            script.append("echo '@%d' >> \"$PM_UNBUILT_LOG\"" % index)
            script.append("{ %s\n} 2>&1" % command)
            script.append("printf '\\n%s %d %%s\\n' $?" % (SALT, index))
        try:
            done = subprocess.run(["/bin/sh", "-c", "\n".join(script)],
                                  cwd=os.path.join(tmp, "work"), env=env,
                                  capture_output=True, text=True, timeout=120)
            output = done.stdout + done.stderr
        except subprocess.TimeoutExpired:
            return ["timed out after 120 seconds"], []

        problems = []
        first_wrong = None
        rest = output.replace(tmp, "$T")
        for index, (number, command, expected, expected_code) in enumerate(steps):
            marker = "\n%s %d " % (SALT, index)
            if marker not in rest:
                problems.append("line %d: `%s` never finished" % (number, command))
                first_wrong = index if first_wrong is None else first_wrong
                break
            got_text, rest = rest.split(marker, 1)
            code_text, _, rest = rest.partition("\n")
            got = got_text.split("\n")
            while got and got[-1] == "":
                got.pop()
            if got != expected or int(code_text) != expected_code:
                diff = difflib.unified_diff(
                    expected + ["[%d]" % expected_code], got + ["[%s]" % code_text],
                    "expected", "got", lineterm="")
                problems.append("line %d: $ %s\n    %s"
                                % (number, command, "\n    ".join(diff)))
                first_wrong = index if first_wrong is None else first_wrong

        # A wrong step counts as pending only when an unbuilt verb was hit at or
        # before it. A wrong step that comes first is a real failure.
        verbs, step = set(), -1
        with open(unbuilt) as f:
            for word in f.read().split():
                if word.startswith("@"):
                    step = int(word[1:])
                elif first_wrong is not None and step <= first_wrong:
                    verbs.add(word)
        return problems, sorted(verbs)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cli", default=os.path.join(REPO, "pm", "cli", "pm"),
                        help="the pm executable to test (default: pm/cli/pm)")
    parser.add_argument("--dir", default=os.path.join(HERE, "t"),
                        help="directory of transcripts (default: pm/tests/t)")
    parser.add_argument("-k", dest="names", action="append", default=[],
                        help="only run transcripts whose file name contains this")
    parser.add_argument("--allow-pending", action="store_true",
                        help="exit 0 even when transcripts are pending on unbuilt verbs")
    parser.add_argument("-v", dest="verbose", action="store_true")
    args = parser.parse_args()

    cli = os.path.abspath(args.cli)
    if not os.path.isfile(cli):
        sys.exit("run_transcripts: no file at %s" % cli)
    names = sorted(n for n in os.listdir(args.dir) if n.endswith(".t")
                   and (not args.names or any(k in n for k in args.names)))
    if not names:
        sys.exit("run_transcripts: no transcript matches")

    passed, pending, failed, waiting_on = [], [], [], set()
    for name in names:
        problems, verbs = run_one(os.path.join(args.dir, name), cli)
        if not problems:
            passed.append(name)
            mark = "ok"
        elif verbs:
            pending.append(name)
            waiting_on.update(verbs)
            mark = "pending (%s)" % ", ".join(verbs)
        else:
            failed.append(name)
            mark = "FAILED"
        if args.verbose or mark == "FAILED":
            print("%s: %s" % (name, mark))
        if mark == "FAILED":
            for problem in problems:
                print("  " + problem)

    print("cli under test: %s" % cli)
    print("transcripts: passed %d, pending %d, failed %d"
          % (len(passed), len(pending), len(failed)))
    if waiting_on:
        print("unbuilt verbs still needed: %s" % ", ".join(sorted(waiting_on)))
    if failed or (pending and not args.allow_pending):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
