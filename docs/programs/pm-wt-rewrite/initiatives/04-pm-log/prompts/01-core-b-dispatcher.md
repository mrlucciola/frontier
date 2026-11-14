# pm-wt-rewrite/04/01b pm log core: dispatcher, help, the unbuilt report fc-2a6562:fc-dac416

```
cd ~/projects/frontier-clean && claude --model claude-sonnet-5-5 --effort medium "$(cat docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-b-dispatcher.md)"
```

The launch line submits this file as the first message of a fresh session rooted at
`~/projects/frontier-clean`; nothing to paste. The overseer normally dispatches it
in-session as a subagent with the same model.

---

# pm-wt-rewrite/04/01b pm log core: dispatcher, help, the unbuilt report fc-2a6562:fc-dac416

`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/01-core-b-dispatcher.md`

Ticket **fc-dac416**, second of four serial workers on its branch. The port is already
under `pm/v2/` (report `reports/01-core-a-move.md` in the worktree). You write the new
`pm/cli/pm` and the first pieces of two shared modules. Read and obey
`docs/programs/pm-wt-rewrite/initiatives/04-pm-log/prompts/00-common.md` first,
especially "Module contract".

- Worktree: `/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416`.

## Read first

`pm/docs/design.md` sections "Verbs", "Output" and "Source tree";
`pm/tests/run_transcripts.py` (docstring); transcript `pm/tests/t/17-help.t`.
`pm/v2/cli/pm` shows how the port found its component through its own symlink.

## Deliver

1. `pm/cli/pm`, executable, `#!/usr/bin/python3`: finds its component through
   `os.path.realpath(__file__)`; the verb table as one list of (verb, short usage,
   summary) that `pm help` prints byte for byte as transcript 17 shows; the aliases
   `claim take`, `release drop`, `close done`, `create new`, `list ls`, `dep link`;
   `pm help <verb>` (aliases resolve) prints the verb file's docstring; an unknown
   word prints `pm: no verb "<word>". Closest: <name>. All verbs: pm help` (or
   without the `Closest:` sentence when nothing is close) and exits 2, where the
   candidates are verbs and aliases; no argument runs `verbs/orient.py`; a verb in the
   table with no file calls `store.unbuilt(verb)`; the exception guard from the
   contract. Load a verb file with `importlib.util.spec_from_file_location` and
   `sys.exit(module.run(argv))`.
2. `pm/tools/store.py` with `unbuilt(name)` only, as the contract says.
3. `pm/tools/render.py` with `refuse`, `usage_error` and `parser`, as the contract says.

No verb files: every verb reports itself unbuilt after your commit.

## Gate

Run from the worktree root:

```sh
/usr/bin/python3 -B pm/tests/run_transcripts.py -k 17-help -v
/usr/bin/python3 -B pm/tests/run_transcripts.py --allow-pending
```

The first must show `17-help.t: pending (take)`: `pm help` matches, and the first
wrong step is `pm help take`. The second must exit 0 with `failed 0`. Also prove by
hand, in `<worktree>/.tmp/`, that `pm clam`, `pm xyzzy`, `pm help clam` and
`pm help` each print what the design says with no traceback, and paste the output.

## Report

Commit message `pm log core: dispatcher, help and the unbuilt report`. Report path
`/Users/matthias/projects/frontier-clean/.worktrees/fc-dac416/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/01-core-b-dispatcher.md`.
