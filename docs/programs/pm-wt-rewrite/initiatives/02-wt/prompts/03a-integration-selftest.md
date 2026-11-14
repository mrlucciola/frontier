# pm-wt-rewrite/02/03a wt integration: selftest, drop the unbuilt path fc-262fa8:fc-8c1f62

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/03a-integration-selftest.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste.

---

# pm-wt-rewrite/02/03a wt integration: selftest, drop the unbuilt path fc-262fa8:fc-8c1f62

`docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/03a-integration-selftest.md`

You are a worker on ticket fc-8c1f62, part 1 of 2. You start with zero context. Your
worktree is `/Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62` on branch
`fc-8c1f62`; the overseer created it. Every verb except `selftest` is built and merged:
the suite on the new side is `passed 122, pending 1 (selftest), skipped 2, failed 0`.

First read `/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/prompts/02-common.md`:
its binding rules, code rules and report section bind you, with these changes: you may
edit `wt/cli/wt` (one change, below); `wt/tools/lib/` stays read-only.

## Deliver

1. **`wt/tools/verbs/selftest.zsh`**: the full lifecycle in a throwaway repo, driving the
   real `wt/cli/wt` (resolve it from `$WT_COMPONENT`) and the new pm: the sibling
   component `${WT_COMPONENT:h}/pm/cli/pm` when it exists, else the `pm` on `PATH`, put
   first on `PATH` through a private bin dir in the scratch with a `pm` symlink, as the
   old selftest did (in this checkout the operator's `PATH` has the old pm, which the
   new wt cannot drive). Read the
   suite's `test_selftest_exits_zero` (it pins the output) and, for which cases matter,
   the old `cmd_selftest` in `/Users/matthias/frontier/runtime-tools/wt/src/wt_core.py`
   (read-only; do not port all its cases: a short lifecycle is the job). Cases, each
   printing `ok: <case>` or `FAIL: <case>: <why>`: start; finish (merged, worktree and
   branch gone, ticket `done`); start then park (ticket `parked`, branch kept); start
   again resumes it, finish merges it; zero-delta park releases; land keeps the ticket
   taken; prune with nothing to do. Last line `SELFTEST PASSED` and exit 0, or
   `SELFTEST FAILED: <n> case(s)` and exit 1.
   Isolation, so the selftest never touches a real repo, registry or report: scratch from
   `mktemp -d "${TMPDIR:-/tmp}/wt-selftest-XXXXXX"`; inside it a private `PM_STORES`
   file, `PM_PLUGINS` dir, `WT_FAULT_REPORT_DIR`, a fixed git identity
   (`GIT_AUTHOR_NAME` etc.), `GIT_CONFIG_GLOBAL=/dev/null`, a fixed `PM_SESSION_ID`; the
   repo made with `git init -b main` inside the scratch. If `git init` fails, print
   `SELFTEST FAILED: git init refused in <dir>` and exit 1 at once, before any other git
   call. **Scratch removal (overseer ruling):** at the end the selftest removes its scratch
   with `rm -r -- "$scratch"` on the exact path `mktemp -d` returned, never `rm -rf`,
   never any other path; this is the one recorded exception to "wt never runs `rm -rf`",
   and the docs part records it.
2. **`wt/cli/wt`**: remove the not-built path (the `$WT_UNBUILT_LOG` append and exit 70).
   A verb in the table always has its file now; a missing file is an install error: one
   `wt:` line naming the missing path and "reinstall wt", exit 1. Keep everything else.

## Gate

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/tests/run_wt.py --cli /Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/cli/wt --pm new
/bin/zsh /Users/matthias/projects/frontier-clean/.worktrees/fc-8c1f62/wt/cli/wt selftest
```

The first, **without** `--allow-pending`: exit 0, `pending 0, failed 0`, skipped 2. The
second: last line `SELFTEST PASSED`, exit 0. `/bin/zsh -n` on `wt/cli/wt` and
`selftest.zsh`, one call each. After the second command, `ls -d` the scratch path it
used must print `No such file or directory`. Paste all of it in EVIDENCE.

## Report

`/Users/matthias/projects/frontier-clean/docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/03a-integration-selftest.md`
