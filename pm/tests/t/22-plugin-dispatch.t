The `dispatch` plugin says whether a ticket's body has the four headings a worker needs.
A heading is a line that starts with the name and a colon, in any case. Each has a
second accepted name: Done or Gate, Writes or Files, Read first or Inputs, Do not or
Not in scope.

  $ pm init t >/dev/null
  $ ln -s "$PLUGINS/dispatch" "$PM_PLUGINS/dispatch"
  $ pm new "port the tests" -b "Done: the suite passes
  > Writes: tests/" >/dev/null
  $ pm dispatch t-1
  missing: Read first
  missing: Do not
  [1]
  $ pm edit t-1 --body "Gate: the suite passes
  > Files: tests/
  > inputs: docs/design.md
  > Not in scope: the runner"
  t-1 edited: body
  $ pm dispatch t-1
  dispatchable
  $ pm dispatch t-9
  pm: no ticket t-9. Search: pm ls all <words>
  [1]
