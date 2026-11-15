#!/usr/bin/python3
"""Write a stage's review verdict to its output/check.md, bound to the current files.

Usage:
  record.py <dir> <stage> --reviewer human --by <name> --decision pass|fail [--reason <text>]
  record.py <dir> <stage> --reviewer model --by <reviewer id> --decision pass|fail [--reason <text>]
  record.py <dir> <stage> --reviewer script

The reviewer kind must be the one the stage's Check section declares (human when it names
none). A script check runs the command after "Reviewer: script" from the workspace root and
takes the decision from its exit status. Writes nothing else.
"""
import argparse
import datetime
import subprocess
import sys
from pathlib import Path

# The skill directory is a linked source checkout; importing must not write bytecode into it.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace import contract, entry_status, find_root, input_files, inside, output_files, sha, stage_dirs  # noqa: E402

SCRIPT_TIMEOUT = 300


def refuse(msg):
    print(f"refused: {msg}", file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description="Record a bound ICM review verdict.")
    ap.add_argument("dir")
    ap.add_argument("stage", help="stage folder name or its two-digit number")
    ap.add_argument("--reviewer", required=True, choices=("human", "script", "model"))
    ap.add_argument("--decision", choices=("pass", "fail"))
    ap.add_argument("--by")
    ap.add_argument("--reason")
    a = ap.parse_args()

    root = find_root(Path(a.dir))
    if root is None:
        refuse("not an ICM workspace; run state.py to see why")
    entry = entry_status(root)
    if entry != "ok":
        refuse(f"entry {entry}")
    matches = [s for s in stage_dirs(root) if a.stage in (s.name, s.name[:2])]
    if len(matches) != 1:
        refuse(f"no single stage named {a.stage}; run state.py for the stage names")
    stage = matches[0]
    c = contract(stage)
    if c is None:
        refuse(f"{stage.name} has no CONTEXT.md")
    if a.reviewer != c["kind"]:
        refuse(f"{stage.name} declares a {c['kind']} check; record that, not a {a.reviewer} verdict")
    outputs, problems = output_files(stage)
    if problems or not outputs:
        refuse("; ".join(problems) or f"{stage.name} has no output to review; run the stage first")
    check = stage / "output" / "check.md"
    if check.is_symlink() or not inside(check.parent, stage):
        refuse("output/check.md is a symlink or leaves the stage")
    inputs, missing = input_files(stage, c["inputs"])
    if missing:
        refuse(f"declared inputs missing: {', '.join(missing)}")

    decision, by, reason = a.decision, a.by, a.reason
    if a.reviewer == "script":
        if decision or by:
            refuse("a script check takes its decision from the command; drop --decision and --by")
        if not c["command"]:
            refuse(f"{stage.name}'s Check names no command after 'Reviewer: script'")
        p = subprocess.run(c["command"], shell=True, cwd=root, capture_output=True, text=True, timeout=SCRIPT_TIMEOUT)
        tail = (p.stdout + p.stderr).strip().splitlines()
        decision, by = ("pass" if p.returncode == 0 else "fail"), c["command"]
        reason = reason or (tail[-1] if tail else f"exit {p.returncode}")
    if not decision or not by:
        refuse("--decision and --by are required for a human or model verdict")
    if decision == "fail" and not reason:
        refuse("a fail needs --reason")

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = ["pass" if decision == "pass" else f"fail: {reason}", ""]
    if decision == "pass" and reason:
        lines += [reason, ""]
    lines += ["```icm-review", f"stage: {stage.name}", f"reviewer: {a.reviewer}", f"by: {by}",
              f"decision: {decision}", f"recorded_at: {now}", f"contract: {c['sha']}"]
    lines += [f"output: {sha(p)} {rel}" for rel, p in sorted(outputs.items())]
    lines += [f"input: {d} {rel}" for rel, d in sorted(inputs.items())]
    lines += ["```", ""]
    check.write_text("\n".join(lines))
    print(f"wrote {check.relative_to(root)}: {decision} by {a.reviewer} {by}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
