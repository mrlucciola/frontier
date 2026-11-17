# wt

Worktree lifecycle for ticketed work: one worktree per ticket at
`<repo>/.wt/<ticket-id>` on branch `<ticket-id>`, entered and left only through
`wt`. A zsh command, one file per verb under `wt/tools/verbs/`.

| Verb | Does |
| --- | --- |
| `start <id>` | Take the ticket (or adopt your own claim) and add or resume its worktree |
| `finish <id>` | Run the gate, rebase, merge fast-forward only, tear down, finish the ticket |
| `land <id>` | `finish --keep-open`: merge and tear down, the ticket stays taken |
| `park <id>` | Commit WIP, park the ticket, tear down; the branch stays |
| `status` | Worktrees joined against their tickets |
| `prune` | Clear deferred-teardown registrations and their merged branches |
| `selftest` | Run the whole lifecycle in a throwaway repo; prints `SELFTEST PASSED` |

Parked tickets are listed by `pm ls parked`; wt has no `pending` verb.

## pm

wt reaches [pm](/pm/README.md) only through its command line. It reads with `pm get`
and changes tickets with `pm take`, `pm done`, `pm park` and `pm drop`. Its own facts
are recorded with `pm emit <id> wt.<name> key=value`. Each call carries `WT_CALLER=1`
so the plugin's guards let wt's own `pm done` and `pm take` through.

## Files in the target repo

Everything wt keeps in a repo is under `.wt/`: the worktrees, plus two committed
files. Gitignore `.wt/*` with `!.wt/gate` and `!.wt/known-red`.

- `.wt/gate`: an executable run in the worktree by `finish` and `land`; non-zero
  refuses the merge. Not executable also refuses. No file, no gate.
- `.wt/known-red`: one `<ticket id> <text>` per line, excusing an owned failure of the
  gate.

## Plugin

`wt/pm-plugin/` is a pm plugin: `pre-done` refuses `pm done` on a ticket that still has
a worktree, `post-take` prints `next: wt start <id>`, and `orient` lists worktrees
whose ticket is done or has no holder. Link it as in [Setup](/wt/INSTALL.md).

## Routes

| Document | Read when |
| --- | --- |
| [Contract](/wt/docs/contract.md) | Reading a `wt` output line, a refusal, or what a verb does |
| [Maintenance](/wt/AGENTS.md) | Changing code or tests here |
| [Setup](/wt/INSTALL.md) | Installing, verifying, configuring or removing |
