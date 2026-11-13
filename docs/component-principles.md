# Component principles

Status: draft, 2026-11-12. This is the review yardstick for the pm and wt
rewrites and is finalized from what those two builds teach. The
[behavioral contract](/README.md#behavioral-contract) says what a component
must be; the repository's contribution standards say where its files go. This
page says how to write the code inside it.

## The test for every file

Could this file be the answer to a blog post or a Stack Overflow question titled
"how do I do X"? A reader who has never seen the component should be able to
open one file, read it top to bottom, and copy the approach. If understanding
it means opening three other files first, it is not done.

## Rules

1. **One file per action.** Each verb or subcommand is one file named for it,
   holding its arguments and its logic. The dispatcher only finds that file and
   runs it.
2. **One shared module per concern, and few of them.** A helper earns a shared
   module when three verbs need it. Until then it lives in the verb that uses it.
   Shared modules are named for what they own (`store`, `routing`), never
   `utils` or `common`.
3. **Shell for orchestration, Python for data.** A tool whose work is running
   other programs in order is zsh. A tool that parses, validates or rewrites
   structured data is standard-library Python at `/usr/bin/python3`. JSON is
   never parsed in shell.
4. **No dependency you would have to install.** zsh, git and the system Python
   are the whole runtime.
5. **The command line is the contract.** Behavior is pinned by black-box tests
   that run the real executable and read its output and exit code. Those tests
   survive a rewrite; tests that import internals do not.
6. **Say it once, plainly.** Straight-line code over indirection. No class where
   a function does. No option nobody passes. No abstraction with one caller. An
   error message names what was refused and the next command to run.
7. **Comments say why.** A comment explains a constraint the code cannot show.
   Ticket ids and history belong in the ticket store and git, not in source.
8. **Cut before you port.** A feature with no current user is dropped or
   deferred by an explicit ruling recorded in the component's docs, never
   carried along and never lost silently.
9. **Decoupled by default.** A component works alone. It reaches another
   component only through that component's command line, and only where the
   coupling removes real work.
10. **Measure before claiming.** A statement about context cost, hook overhead
    or speed carries the command and the number that back it.

## Reviewing against this page

A reviewer reads one verb file cold and answers three questions. Can I say what
it does without opening another file? Is there a line I could delete without a
test failing? Does every refusal tell me what to run next? Three yeses pass.
