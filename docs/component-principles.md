# Component principles

This is the review yardstick for component code, finalized 2026-11-14 from the
pm and wt rewrites. The [behavioral contract](/README.md#behavioral-contract)
says how a component behaves; the [contribution standards](/docs/contributing.md)
say where its files go. This page says how to write the code inside it.

## The test for every file

Could this file be the answer to a blog post or a Stack Overflow question titled
"how do I do X"? A reader who has never seen the component should be able to
open one file, read it top to bottom, and copy the approach. If understanding
it means opening three other files first, it is not done.

## Rules

1. **One file per action.** Each verb or subcommand is one file named for it,
   holding its arguments and its logic. The dispatcher only finds that file and
   runs it. A verb never imports another verb. One defined as another verb plus
   something runs it through the command line.
2. **One shared module per concern, and few of them.** A helper earns a shared
   module when three verbs need it, or when two verbs must give the same answer
   and separate copies would drift: a refusal both enforce, or two verbs of one
   family. Until then it lives in the verb that uses it. Each two-verb helper is
   recorded in the component's `AGENTS.md`. Shared modules are named for what
   they own (`store`, `routing`), never `utils` or `common`.
3. **Shell for orchestration, Python for data.** A tool whose work is running
   other programs in order is zsh. A tool that parses, validates or rewrites
   structured data is standard-library Python at `/usr/bin/python3`. JSON is
   never parsed in shell.
4. **No dependency you would have to install.** zsh, git and the system Python
   are the whole runtime.
5. **The command line is the contract.** Behavior is pinned by transcripts and
   black-box tests that run the real executable and read its output and exit
   code. Write the transcript, the exact command and output, before the code. A
   defect found in review gets a transcript before its fix. Tests that import
   internals do not survive a rewrite.
6. **Say it once, plainly.** Straight-line code over indirection. No class where
   a function does. No option nobody passes. No abstraction with one caller.
   Refusals follow the contract's output rule.
7. **Comments say why.** A comment explains a constraint the code cannot show.
   Ticket ids and history belong in the ticket store and git, not in source.
8. **Cut before you port.** A feature with no current user is dropped or
   deferred by an explicit ruling recorded in the component's docs, never
   carried along and never lost silently. The same holds before anything is
   built: every mechanism in a design names the requirement it serves, and one
   that serves none is cut.
9. **Decoupled by default.** A component works alone. It reaches another
   component only through that component's command line, and only where the
   coupling removes real work. An extension point is a file the host finds by
   name, never a name the host knows: a directory of executables, installed by a
   symlink and removed by deleting it.
10. **Measure before claiming.** A statement about context cost, hook overhead
    or speed carries the command and the number that back it. Text an agent
    reads (help, refusals, injected context) has a byte ceiling held in a test.

## Reviewing against this page

A reviewer reads one verb file cold and answers three questions. Can I say what
it does without opening another file? Is there a line I could delete without a
test failing? Does every refusal tell me what to run next? Three yeses pass.

## Rulings and evidence

Paths are in the tree. `523ae74:` and `bd6a9c5:` name retired review reports; read
them with `git show <sha>:<path>`. `pm-review` is
`be4de0b:docs/programs/pm-wt-rewrite/initiatives/01-pm/reports/04-review.md`, `pm-e`
is `523ae74:docs/programs/pm-wt-rewrite/initiatives/04-pm-log/reports/04-integration-e-review.md`,
`wt-1` is `bd6a9c5:docs/programs/pm-wt-rewrite/initiatives/02-wt/reports/01-review.md`.

| Rule | Ruling | Evidence |
| --- | --- | --- |
| 1 | Kept; no-import sentence added | `pm-e` "Rule 1: every verb file holds its own arguments, logic and help"; `pm-review` close.py:9 imports release, failed the cold read; `wt/tools/verbs/finish.zsh:171-176` runs park through the dispatcher |
| 1 proposal: a verb that is another verb plus X may import it (pm `lint`, `validate`) | Declined | Both verbs are gone (`pm/docs/design.md:337`, replaced by `doctor`); no file in `pm/` or `wt/` imports a verb (`cli/pm:91` only loads the dispatched one); `wt` already solves the case by subprocess |
| 2 | Changed: the identical-rule and one-family cases added; the record is required | `pm-review` store.py pairs (verb and its `where --mutate` preflight, claim and `create --claim-as`) ruled "copying them would let a verb and its preflight drift"; `wt-1` finding 13; `wt/AGENTS.md:33-38` |
| 2 proposal: two verbs that must enforce the identical rule | Accepted | In the current pm: `store.backup_blob` (`doctor.py:73`, `restore.py:26`) and `store.locate_dir` (`import.py:158`, `restore.py:20`) |
| 2 proposal: two verbs of one family (wt finish and park) | Accepted | `wt_findings_required` (`finish.zsh:194`, `park.zsh:100`); `wt_merged_route` (`finish.zsh:85`, `park.zsh:73`); `wt_refuse_undeletable`, `wt_stop_remove_failed`, `wt_deferred_line` in `wt/tools/lib/teardown.zsh`, called from both verbs |
| 3 | Kept | `wt-1` "No JSON is parsed in zsh; findings_required.py and the pairs logic in crossrepo.py"; `wt/tools/lib/findings_required.py`, `crossrepo.py` |
| 4 | Kept | Imports under `pm/tools`, `pm/cli`, `wt/tools/lib/*.py` are standard library only (checked with `rg "^(import\|from) \w+"`) |
| 5 | Changed: transcripts first, a review defect gets a transcript | `pm/docs/design.md:1-5`, `pm/tests/t/` (25 files), `pm/tests/run_transcripts.py`; `pm-review` test_gitcommit.py:20,99,121 used private names and broke the rule; `pm-e` pilot with no pilots, import with a `pre` plugin and `new --blocks` across stores were untested, then pinned in `pm/tests/t/25-review-edges.t` |
| 5 proposal: transcripts as the contract | Folded into rule 5 | As above; `wt/AGENTS.md:13` reuses pm's runner for `wt/tests/t` |
| 6 | Kept; the refusal sentence moved to the contract | `pm-e` `_rank` has one caller (orient.py:13), `_new(by=)` no caller passes `by` (import.py:56); `pm-e` lists refusals with no next command (park.py:28, hold.py:28, reopen.py:24) |
| 7 | Kept | `pm-review` ticket ids in comments (`ticket:49`, `init.py:12`), none left: `rg "\b(fc\|cl\|fr)-[0-9a-f]{6}\b"` over `pm/` and `wt/` source prints nothing; `pm-e` store.py:422 and :403 lacked a why |
| 8 | Kept | `pm/docs/design.md:330-346` "Not carried over", one ruling per dropped feature; `wt/cli/wt:22` drops `pending` with its replacement named |
| 8 | Changed 2026-11-15: extended from ports to designs | `73f99fa:cwf/cwf/installer.py` (363 lines) and about 640 lines of tests and docs written for it served none of R01-R12 in `cwf/docs/SPECIFICATION.md`; a 35-line `cwf/deploy.sh` replaced them |
| 9 | Changed: plugins by file presence added | `pm/docs/design.md:246-272`; `rg "\bwt\b\|worktree" pm/tools pm/cli` prints nothing; `wt/pm-plugin/{orient,post-take,pre-done}`; `wt/tools/lib/pm.zsh:7` reaches pm only by its command line |
| 9 proposal: plugins by file presence | Folded into rule 9 | As above |
| 10 | Kept; byte ceilings added | `pm-e` replay O(n^2) "measure on the largest real store before claiming this is fine"; `pm/tests/test_budgets.py:16`, `pm/docs/design.md:234-244` |
| 10 proposal: size budgets as tests | Folded into rule 10 | As above |
