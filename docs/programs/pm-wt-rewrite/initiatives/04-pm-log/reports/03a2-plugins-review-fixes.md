TICKET
fc-a731f4 (fix round on its branch, from reports/03a-review.md)

DID
1. store.change: when any pre-* file exists, `check` runs outside the lock and the pre hooks run on it; under the lock the events are compared (ts and by ignored); a difference refuses "the store changed while pm was checking. Run the command again." and appends nothing.
2. No pre-* file: no outside-lock check, no pre hooks (plugins.any_pre).
3. A pre hook that exits non-zero with no output refuses "plugin <name> refused <op> <id>."
4. OSError from a plugin file: pre and cmd refuse "plugin <name> could not run <file>: <strerror>."; orient and post print "pm: warning: ..." on stderr and carry on. _post registers its atexit flush before running hooks, so the verb's output prints first and a post hook cannot fail the verb.
5. pilot.open_pilots runs `pm` with cwd=$PM_STORE (covers pre-done, cmd, orient). dispatch/cmd left alone: it runs in the caller's store and `pm get` routes by prefix.
6. emit accepts only [a-z0-9_-]+(\.[a-z0-9_-]+)+.
7. `pm help` plugins: line leaves out plugins named like a verb or alias.
8. plugins.with_file returns paths only (one find per plugin); name_of(path) gives the name where needed.
Files: pm/tools/plugins.py, pm/tools/store.py, pm/tools/verbs/emit.py, pm/cli/pm, pm/plugins/pilot/pilot.py.

EVIDENCE
Gate 1: passed 5, pending 0, failed 0 (-k 15 17 22 23 24).
Gate 2 (--allow-pending): passed 22, pending 2, failed 0 (hook, import unbuilt).
By hand (.tmp/prove.py, .tmp/proof/):
- Item 1: a pre-new hook appended a racing `new a-1` to the log; `pm new "mine"` printed "pm: the store changed while pm was checking. Run the command again." exit 1; `pm ls all` showed only `a-1 racer`; the rerun gave a-2.
- Item 4 post: broken post-note printed "pm: warning: plugin bad could not run post-note: Exec format error.", then "a-1 noted", exit 0; the note is in `pm show a-1`.
- Item 4 orient: bare `pm` printed "pm: warning: plugin bad could not run orient: Exec format error." and the ready list, exit 0.
- Item 5: pilot linked; in store c, `pm done b-1 -m ok` (b-1 labelled pilot with measured:/ruling: notes in store b) printed "b-1 done", exit 0; `pm get b-1 status` gave done.

COMMITS
"pm plugins: review fixes" on branch fc-a731f4 (this report included).

NOT DONE
- Review test-gap items beyond transcript 24 (cmd path containment, cross-store done transcript) have no new transcript; I may not edit pm/tests/t/.
- pre-done has an unused `import subprocess` (not mine; left).

BLOCKED ON OPERATOR
None.

ARTIFACTS
/Users/matthias/projects/frontier-clean/.worktrees/fc-a731f4/.tmp/prove.py
