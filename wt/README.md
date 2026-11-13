# wt

Worktree lifecycle for ticketed work: one worktree per ticket at
`<repo>/.worktrees/<ticket-id>`, entered and left only through `wt`.

Status: being rewritten into this component as zsh. The installed `wt` is still
the one in `~/frontier/runtime-tools/wt` until cutover. Nothing here is on
`PATH`.

| Document | Read when |
| --- | --- |
| [Behavior contract](/wt/docs/contract.md) | Porting a verb or reading a `wt` output line. It is the old wt README, copied verbatim |
| [Maintenance](/wt/AGENTS.md) | Changing code or tests here |
| [Setup](/wt/INSTALL.md) | Installing, verifying or removing |

wt depends on [pm](/pm/README.md) through its command line only:
`pm ticket where`, `claim`, `close`, `release` and `show --json`.
