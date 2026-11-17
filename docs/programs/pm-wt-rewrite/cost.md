# Instruction cost of pm and wt, before and after hook delivery

Measured on `2026-11-14` for ticket `fc-f9ab11` (epic `fc-ccecda`), at commit `98f4310`.
Byte counts are diagnostic. They are not token savings: a byte of prose, a path and
a JSON key tokenize differently, and nothing here was run through a tokenizer.
Every number sits beside the command that produced it. The scripts those commands
name are listed in full under "Scripts", because they are not committed files; save
each under `.tmp/` of the main checkout and run from `/Users/matthias/projects/frontier-clean`.

Machine load: all timings ran on a busy laptop, one run at a time, so absolute
milliseconds are noisy and only the old-against-new ordering is meaningful.
```sh
uptime
# 20:19  34 users, load averages: 3.33 3.57 3.50
```

## Today, before any ticket work

What a Claude session carries from the old system. The description rows are
always in context. The CLAUDE.md rows are always in context. A SKILL.md body is
read only when the skill is invoked, so those rows are a ceiling, not a baseline.
The session-start row is injected once, in a repository with a store.

| What | Bytes | Command |
| --- | --- | --- |
| pm skill `description:`, Claude form | 377 | `python3 -B .tmp/cost_desc.py /Users/matthias/frontier/skills/pm/SKILL.md` |
| worktree-lifecycle skill `description:`, Claude form | 510 | `python3 -B .tmp/cost_desc.py /Users/matthias/frontier/skills/worktree-lifecycle/SKILL.md` |
| pm skill `description:`, Codex form | 190 | `python3 -B .tmp/cost_desc.py /Users/matthias/frontier/skills/pm/SKILL.md` |
| worktree-lifecycle skill `description:`, Codex form | 219 | `python3 -B .tmp/cost_desc.py /Users/matthias/frontier/skills/worktree-lifecycle/SKILL.md` |
| `skills/pm/SKILL.md`, whole | 4739 | `wc -c /Users/matthias/frontier/skills/pm/SKILL.md` |
| `skills/worktree-lifecycle/SKILL.md`, whole | 6794 | `wc -c /Users/matthias/frontier/skills/worktree-lifecycle/SKILL.md` |
| CLAUDE.md lines 142-144, "Worktrees and tickets" recipe block | 279 | `sed -n '142,144p' /Users/matthias/frontier/instructions/claude-global/CLAUDE.md \| wc -c` |
| CLAUDE.md lines 160-169, "Branches and worktrees (shared checkouts)" | 3127 | `sed -n '160,169p' /Users/matthias/frontier/instructions/claude-global/CLAUDE.md \| wc -c` |
| CLAUDE.md lines 41-42, 76-81 and 154, other pm and wt paragraphs | 789 | `sed -n '41,42p;76,81p;154p' /Users/matthias/frontier/instructions/claude-global/CLAUDE.md \| wc -c` |
| old session-start injection, main checkout | 1318 | `python3 -B .tmp/cost_all.py` (row "old session-start, main checkout") |

The "other" row counts the `Ticket: <id> <pm status>` paragraph, the "Scope"
paragraph that names `wt finish` and worktrees, and the clause naming `pm` in
the "current time" recipe, at the lines in its own row. The "Findings" section names
tickets but states a general rule, and is not counted.

Always-carried total in a store repository, Claude form: both descriptions, the
three CLAUDE.md rows and the injection.

```sh
# 377 + 510 + 279 + 3127 + 789 + 1318 = 6400
python3 -B -c 'print(377 + 510 + 279 + 3127 + 789 + 1318)'
```

Both whole SKILL.md files add 11533 when invoked.
```sh
# 4739 + 6794 = 11533
python3 -B -c 'print(4739 + 6794)'
```

The deployed copies differ from the source. The deployed worktree-lifecycle skill is
from an older source commit and is larger than today's source.
```sh
wc -c /Users/matthias/.claude/skills/pm/SKILL.md /Users/matthias/.claude/skills/worktree-lifecycle/SKILL.md
# 4622 /Users/matthias/.claude/skills/pm/SKILL.md
# 17011 /Users/matthias/.claude/skills/worktree-lifecycle/SKILL.md
```

How the injection was produced: the registered hook (`/usr/bin/python3` on
`~/frontier/hooks/pm/session_start.py`) with a session-start JSON on stdin, `cwd` set to
the main checkout, in a sandbox where the hook's ledger write goes to `.tmp/cost-ledger`.
It calls the installed `pm ticket summary` against the real store, so the number
moves with that store. The old system has no prompt hook. The old stop hook is
silent unless the session holds a claim.

## The new system

Store copy: the main checkout's `.pm/tickets.jsonl` and `.pm/config.json` copied to
`.tmp/cost-store/.pm`, then `pm import` with a scratch registry and `GIT_DIR` pointed at
a missing path so no backup touches a real repository.

```sh
python3 -B .tmp/cost_import.py
# imported 84 tickets: 25 open, 3 taken, 56 done
```

The no-store directory is `/Users/matthias/.claude/.tmp/cost-nostore`, not a directory
under the repository's `.tmp/`: the lookup walks up from the working directory, and the
repository itself has a `.pm/`. The one ticket held by `cost-session-a` was taken with
`PM_SESSION_ID=cost-session-a PM_ACTOR=claude /usr/bin/python3 -B pm/cli/pm take` in the
copy, before the rows below were measured; it changes the session-start text for every
other session.

Bytes per event; stop writes to stderr and exits with the code in its row when it blocks.

| Event | Stdout bytes | Stderr bytes | Exit | Command |
| --- | --- | --- | --- | --- |
| session-start, imported copy | 730 | 0 | 0 | `python3 -B .tmp/cost_all.py` (row "new session-start, imported copy") |
| prompt naming three existing ids | 319 | 0 | 0 | `python3 -B .tmp/cost_all.py` (row "new prompt, three ticket ids") |
| prompt naming no id | 0 | 0 | 0 | `python3 -B .tmp/cost_all.py` (row "new prompt, no ticket id") |
| stop, nothing held | 0 | 0 | 0 | `python3 -B .tmp/cost_all.py` (row "new stop, nothing held") |
| stop, session holds one ticket | 0 | 309 | 2 | `python3 -B .tmp/cost_all.py` (row "new stop, session holds one ticket") |
| session-start, no store | 0 | 0 | 0 | `python3 -B .tmp/cost_all.py` (row "new session-start, no store") |
| prompt, no store | 0 | 0 | 0 | `python3 -B .tmp/cost_all.py` (row "new prompt, no store") |
| stop, no store | 0 | 0 | 0 | `python3 -B .tmp/cost_all.py` (row "new stop, no store") |

The old session-start injection for the same store is the first table's last row, so
the new one is smaller in a store repository, and both inject nothing outside one. The
new system carries no skill and no global instruction text, per the design's "Harness
hooks"; the global CLAUDE.md and the two skills have not been edited in this ticket, so
the first section's rows stay in a session until the cutover removes them.

wt's own guidance, from `wt/cli/wt` run from the main checkout. It is read on request,
not injected.

| What | Stdout bytes | Stderr bytes | Command |
| --- | --- | --- | --- |
| `wt help` | 748 | 0 | `python3 -B .tmp/cost_wthelp.py` (row "help") |
| `wt help start` | 573 | 0 | `python3 -B .tmp/cost_wthelp.py` (row "help start") |
| `wt help finish` | 648 | 0 | `python3 -B .tmp/cost_wthelp.py` (row "help finish") |
| `wt help land` | 648 | 0 | `python3 -B .tmp/cost_wthelp.py` (row "help land") |
| `wt help park`, the longest | 676 | 0 | `python3 -B .tmp/cost_wthelp.py` (row "help park") |
| `wt help status` | 257 | 0 | `python3 -B .tmp/cost_wthelp.py` (row "help status") |
| `wt help prune` | 294 | 0 | `python3 -B .tmp/cost_wthelp.py` (row "help prune") |
| `wt help selftest` | 157 | 0 | `python3 -B .tmp/cost_wthelp.py` (row "help selftest") |

## One ticket's life, old against new

Two scratch repositories, `.tmp/cost-life-old` and `.tmp/cost-life-new`, each with a
seed commit and an empty store, a scratch registry and telemetry off. Old run uses the
installed `pm` and `wt` on PATH; new run puts a `pm` symlink to `pm/cli/pm` first on
PATH and runs `wt/cli/wt`. Each run files a ticket, starts it, commits one file in the
worktree, adds a note, and finishes it, all as one session. Bytes are the command's
own output; the setup commit is not counted.

```sh
python3 -B .tmp/cost_life.py old
# pm ticket create: exit=0 stdout=10 stderr=0
# wt start:         exit=0 stdout=368 stderr=0
# pm ticket note:   exit=0 stdout=24 stderr=0
# wt finish:        exit=0 stdout=75 stderr=135
python3 -B .tmp/cost_life.py new
# pm new:           exit=0 stdout=5 stderr=0
# wt start:         exit=0 stdout=260 stderr=0
# pm note:          exit=0 stdout=11 stderr=0
# wt finish:        exit=0 stdout=70 stderr=135
```

| Step | Old stdout | Old stderr | New stdout | New stderr | Command |
| --- | --- | --- | --- | --- | --- |
| file | 10 | 0 | 5 | 0 | `python3 -B .tmp/cost_life.py old` and `python3 -B .tmp/cost_life.py new` |
| take | 368 | 0 | 260 | 0 | `python3 -B .tmp/cost_life.py old` and `python3 -B .tmp/cost_life.py new` |
| note | 24 | 0 | 11 | 0 | `python3 -B .tmp/cost_life.py old` and `python3 -B .tmp/cost_life.py new` |
| finish | 75 | 135 | 70 | 135 | `python3 -B .tmp/cost_life.py old` and `python3 -B .tmp/cost_life.py new` |
| total | 477 | 135 | 346 | 135 | `python3 -B .tmp/cost_life.py old` and `python3 -B .tmp/cost_life.py new` |

The stderr on finish is wt's "no --findings" warning, identical in both. The ids differ
in length (`cs-5f1128` against `cs-1`) and the worktree paths are the same length
(`cost-life-old`, `cost-life-new`), so path text contributes the same bytes to both.
The old `wt start` also prints three lines of exits; the new one prints one line.

## Hook wall time

Each hook ran `runs=25` times, `time.perf_counter` around `subprocess.run` including process
start, one run at a time. Median and max in milliseconds. Load caveat: see the top;
the rows were measured in one pass in the order shown, so drift across the pass
is not removed.

| Hook | Median ms | Max ms | Command |
| --- | --- | --- | --- |
| old session-start, main checkout | 133.7 | 139.8 | `python3 -B .tmp/cost_all.py` (row "old session-start, main checkout") |
| old stop, nothing claimed | 103.6 | 113.1 | `python3 -B .tmp/cost_all.py` (row "old stop, nothing claimed by the session") |
| old session-start, no store | 31.4 | 38.8 | `python3 -B .tmp/cost_all.py` (row "old session-start, no store") |
| old stop, no store | 102.7 | 107.4 | `python3 -B .tmp/cost_all.py` (row "old stop, no store") |
| new session-start, imported copy | 90.2 | 96.9 | `python3 -B .tmp/cost_all.py` (row "new session-start, imported copy") |
| new prompt, three ids | 52.1 | 54.7 | `python3 -B .tmp/cost_all.py` (row "new prompt, three ticket ids") |
| new prompt, no id | 48.5 | 52.5 | `python3 -B .tmp/cost_all.py` (row "new prompt, no ticket id") |
| new stop, nothing held | 49.0 | 56.5 | `python3 -B .tmp/cost_all.py` (row "new stop, nothing held") |
| new stop, session holds one | 48.6 | 52.8 | `python3 -B .tmp/cost_all.py` (row "new stop, session holds one ticket") |
| new session-start, no store | 44.3 | 47.7 | `python3 -B .tmp/cost_all.py` (row "new session-start, no store") |
| new prompt, no store | 46.7 | 59.8 | `python3 -B .tmp/cost_all.py` (row "new prompt, no store") |
| new stop, no store | 48.5 | 52.4 | `python3 -B .tmp/cost_all.py` (row "new stop, no store") |

Old stop is slow because it lists claimed rows across every registered store through
the installed `pm`, even outside a store. The old no-store session-start is fastest
because it exits before starting `pm`.

## Not measured

- The old stop hook when the session does hold a claim (its blocking path): that needs a
  claim in the real store, and this ticket does not write one. An operator who wants it
  claims any ticket in a scratch store registered for the installed `pm`, then runs
  `python3 -B .tmp/cost_run.py 25 <store repo> '{"session_id":"<id>","stop_hook_active":false}' PM_HOLD_STATE_DIR=<scratch> -- /usr/bin/python3 /Users/matthias/frontier/hooks/pm/stop.py`.
- Tokens. Nothing here ran a tokenizer.
- Codex. The Codex-form descriptions are counted, but no Codex session was started to see
  what it loads.
- Whether Claude Code actually loads the description of every skill, or truncates it:
  the byte rows assume the full description is carried.

## Scripts

`.tmp/cost_desc.py`, the descriptions:

```python
import sys

for path in sys.argv[1:]:
    lines = open(path, encoding="utf-8").read().split("\n")
    i = lines.index("<!-- if:codex -->")
    codex = lines[i + 1][len("description: "):]
    j = lines.index("<!-- else -->")
    k = lines.index("<!-- endif -->")
    assert lines[j + 1] == "description: >"
    claude = " ".join(l.strip() for l in lines[j + 2:k])
    print("%s codex=%d claude=%d" % (path, len(codex.encode()), len(claude.encode())))
```

`.tmp/cost_import.py`, the store copy:

```python
import os
import subprocess

TMP = "/Users/matthias/projects/frontier-clean/.tmp"
STORE = TMP + "/cost-store"
PM = "/Users/matthias/projects/frontier-clean/pm/cli/pm"
reg = TMP + "/cost-registry-new"
open(reg, "w").close()
env = dict(os.environ, PM_STORES=reg, GIT_DIR=TMP + "/cost-no-git")
env.pop("PM_NOW", None)
r = subprocess.run(["/usr/bin/python3", "-B", PM, "import"], cwd=STORE, env=env,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
print(r.returncode)
print(r.stdout[-2000:])
print(r.stderr[-2000:])
print(os.listdir(STORE + "/.pm"))
```

`.tmp/cost_run.py`, runs one command N times and prints bytes and times:

```python
import json
import os
import statistics
import subprocess
import sys
import time

# usage: cost_run.py N CWD STDIN_JSON [KEY=VALUE ...] -- COMMAND ARG...
n, cwd, stdin = int(sys.argv[1]), sys.argv[2], sys.argv[3]
cut = sys.argv.index("--")
env = dict(os.environ)
for k in ("PM_NOW", "PM_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID"):
    env.pop(k, None)
for kv in sys.argv[4:cut]:
    k, _, v = kv.partition("=")
    env[k] = v
argv = sys.argv[cut + 1:]
times = []
for _ in range(n):
    t = time.perf_counter()
    r = subprocess.run(argv, cwd=cwd, env=env, input=stdin, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True)
    times.append((time.perf_counter() - t) * 1000)
print("exit=%d stdout=%d stderr=%d runs=%d median=%.1fms max=%.1fms" % (
    r.returncode, len(r.stdout.encode()), len(r.stderr.encode()), n,
    statistics.median(times), max(times)))
```

`.tmp/cost_all.py`, the twelve hook cases:

```python
import json
import subprocess

MAIN = "/Users/matthias/projects/frontier-clean"
STORE = MAIN + "/.tmp/cost-store"
NOSTORE = "/Users/matthias/.claude/.tmp/cost-nostore"
PM = MAIN + "/pm/cli/pm"
PY = "/usr/bin/python3"
OLD = ["PM_TELEMETRY_DIR=-", "CLAUDE_HOOKS_LEDGER_DIR=" + MAIN + "/.tmp/cost-ledger",
       "PM_HOLD_STATE_DIR=" + MAIN + "/.tmp/cost-holds"]
NEW = ["PM_STORES=" + MAIN + "/.tmp/cost-registry-new"]
IDS = "look at fc-f9ab11, fc-ccecda and fc-03292e please"


def js(event, cwd, sid, **kw):
    return json.dumps(dict(cwd=cwd, session_id=sid, hook_event_name=event, **kw))


CASES = [
    ("old session-start, main checkout", MAIN, js("SessionStart", MAIN, "cost-session-b"), OLD,
     [PY, "/Users/matthias/frontier/hooks/pm/session_start.py"]),
    ("old stop, nothing claimed by the session", MAIN,
     js("Stop", MAIN, "cost-session-b", stop_hook_active=False), OLD,
     [PY, "/Users/matthias/frontier/hooks/pm/stop.py"]),
    ("old session-start, no store", NOSTORE, js("SessionStart", NOSTORE, "cost-session-b"), OLD,
     [PY, "/Users/matthias/frontier/hooks/pm/session_start.py"]),
    ("old stop, no store", NOSTORE, js("Stop", NOSTORE, "cost-session-b", stop_hook_active=False), OLD,
     [PY, "/Users/matthias/frontier/hooks/pm/stop.py"]),
    ("new session-start, imported copy", STORE, js("SessionStart", STORE, "cost-session-b"), NEW,
     [PY, "-B", PM, "hook", "session-start"]),
    ("new prompt, three ticket ids", STORE, js("UserPromptSubmit", STORE, "cost-session-b", prompt=IDS), NEW,
     [PY, "-B", PM, "hook", "prompt"]),
    ("new prompt, no ticket id", STORE, js("UserPromptSubmit", STORE, "cost-session-b", prompt="hello"), NEW,
     [PY, "-B", PM, "hook", "prompt"]),
    ("new stop, nothing held", STORE, js("Stop", STORE, "cost-session-b", stop_hook_active=False), NEW,
     [PY, "-B", PM, "hook", "stop"]),
    ("new stop, session holds one ticket", STORE, js("Stop", STORE, "cost-session-a", stop_hook_active=False), NEW,
     [PY, "-B", PM, "hook", "stop"]),
    ("new session-start, no store", NOSTORE, js("SessionStart", NOSTORE, "cost-session-b"), NEW,
     [PY, "-B", PM, "hook", "session-start"]),
    ("new prompt, no store", NOSTORE, js("UserPromptSubmit", NOSTORE, "cost-session-b", prompt=IDS), NEW,
     [PY, "-B", PM, "hook", "prompt"]),
    ("new stop, no store", NOSTORE, js("Stop", NOSTORE, "cost-session-b", stop_hook_active=False), NEW,
     [PY, "-B", PM, "hook", "stop"]),
]
for label, cwd, stdin, env, cmd in CASES:
    r = subprocess.run([PY, "-B", MAIN + "/.tmp/cost_run.py", "25", cwd, stdin] + env + ["--"] + cmd,
                       stdout=subprocess.PIPE, universal_newlines=True)
    print("%-44s %s" % (label, r.stdout.strip()))
```

`.tmp/cost_wthelp.py`, wt help sizes:

```python
import subprocess

WT = "/Users/matthias/projects/frontier-clean/wt/cli/wt"
for verb in [None, "start", "finish", "land", "park", "status", "prune", "selftest"]:
    argv = [WT, "help"] + ([verb] if verb else [])
    r = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       cwd="/Users/matthias/projects/frontier-clean")
    print("%-22s exit=%d stdout=%d stderr=%d" % (" ".join(argv[1:]), r.returncode,
                                                 len(r.stdout), len(r.stderr)))
```

`.tmp/cost_life.py`, one ticket's life. Run `git init -b main .tmp/cost-life-old` and
`git init -b main .tmp/cost-life-new` from the main checkout first, and check each with
`git -C <path> rev-parse --show-toplevel`.

```python
import os
import re
import subprocess
import sys

which = sys.argv[1]  # old | new
extra_finish = sys.argv[2:]
TMP = "/Users/matthias/projects/frontier-clean/.tmp"
REPO = TMP + "/cost-life-" + which
NEWBIN = TMP + "/cost-newbin"
os.makedirs(NEWBIN, exist_ok=True)
link = NEWBIN + "/pm"
if not os.path.islink(link):
    os.symlink("/Users/matthias/projects/frontier-clean/pm/cli/pm", link)
WTNEW = "/Users/matthias/projects/frontier-clean/wt/cli/wt"

reg = TMP + "/cost-life-registry-" + which
with open(reg, "w") as f:
    f.write('{"stores": []}\n' if which == "old" else "")
env = dict(os.environ, PM_TELEMETRY_DIR="-",
           WT_FAULT_REPORT_DIR=TMP + "/cost-faults", GIT_CONFIG_GLOBAL="/dev/null",
           GIT_CONFIG_SYSTEM="/dev/null", GIT_AUTHOR_NAME="cost", GIT_AUTHOR_EMAIL="c@example.invalid",
           GIT_COMMITTER_NAME="cost", GIT_COMMITTER_EMAIL="c@example.invalid",
           PM_SESSION_ID="cost-life-" + which, PM_AGENT="claude/worker")
env["PM_STORES_FILE" if which == "old" else "PM_STORES"] = reg
for k in ("WT_ACTOR", "PM_ACTOR", "CLAUDE_CODE_SESSION_ID", "CODEX_THREAD_ID", "PM_NOW"):
    env.pop(k, None)
if which == "new":
    env["PATH"] = NEWBIN + ":" + env["PATH"]
    WT = WTNEW
else:
    WT = "wt"
PM = "pm"


def sh(argv, cwd=REPO, show=False):
    r = subprocess.run(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True)
    if show:
        print("$ " + " ".join(argv))
        print("  exit=%d stdout=%d stderr=%d" % (r.returncode, len(r.stdout.encode()), len(r.stderr.encode())))
        for line in r.stdout.splitlines():
            print("  out| " + line)
        for line in r.stderr.splitlines():
            print("  err| " + line)
    return r


def git(*a):
    r = sh(["git", "-c", "commit.gpgsign=false"] + list(a))
    assert r.returncode == 0, r.stderr
    return r


top = sh(["git", "rev-parse", "--show-toplevel"]).stdout.strip()
assert top == REPO, top
if not os.path.exists(REPO + "/README.md"):
    with open(REPO + "/README.md", "w") as f:
        f.write("seed\n")
    git("add", "--", "README.md")
    git("commit", "-q", "-m", "seed")
    if which == "old":
        r = sh([PM, "ticket", "init", "--prefix", "cs"])
    else:
        r = sh([PM, "init", "cs"])
    print("init", r.returncode, r.stdout.strip(), r.stderr.strip())
    git("add", "-A")
    git("commit", "-q", "-m", "store")

if which == "old":
    create = sh([PM, "ticket", "create", "Measure one ticket's life"], show=True)
else:
    create = sh([PM, "new", "Measure one ticket's life"], show=True)
tid = re.search(r"\bcs-[0-9a-z]+", create.stdout).group(0)
print("id", tid)
sh([WT, "start", tid, "--as", "claude"], show=True)
wtpath = REPO + "/.worktrees/" + tid
if os.path.isdir(wtpath):
    with open(wtpath + "/work.txt", "w") as f:
        f.write("work\n")
    sh(["git", "-c", "commit.gpgsign=false", "-C", wtpath, "add", "--", "work.txt"])
    sh(["git", "-c", "commit.gpgsign=false", "-C", wtpath, "commit", "-q", "-m", "work"])
note = [PM, "ticket", "note", tid, "Measured note text"] if which == "old" else [PM, "note", tid, "Measured note text"]
sh(note, show=True)
sh([WT, "finish", tid] + extra_finish, show=True)
```
