# Cases the sandboxed suite cannot run

One entry per case: why it cannot run sandboxed, and the operator-terminal command
that covers it. Run from an ordinary terminal (not the agent sandbox) in the checkout.

## Deferred teardown (finish)

`git worktree remove` failing with `Operation not permitted` on `.git/worktrees/<id>`
while the tree is gone is the sandbox denying deletion of a path under `.git`. A
throwaway repo under the test root has no such deny, and the test cannot add one without
faking git. The happy-path finish tests accept the deferred `OK:` tail. The forced case
is covered by the old wt's own selftest (cases 37, 40, 41), which fakes git's reply:

```sh
/Users/matthias/frontier/runtime-tools/wt/cli/wt selftest
```

Expect every case line to pass and the last line to report no failures.

## `.vscode` refusal (finish)

Not uncovered when this was written: `.vscode` could be created under the test root, so
`test_vscode_dir_refuses_before_merge` runs. In a sandbox that denies a `.vscode` path
segment it skips itself (`skipped 1` fails the gate); run it unsandboxed there:

```sh
/usr/bin/python3 -B /Users/matthias/projects/frontier-clean/.worktrees/fc-30c060/wt/tests/run_wt.py --cli /Users/matthias/frontier/runtime-tools/wt/cli/wt --pm old -k test_vscode_dir_refuses_before_merge -v
```

Expect `ok` (not `skipped`) and `failed 0`.
