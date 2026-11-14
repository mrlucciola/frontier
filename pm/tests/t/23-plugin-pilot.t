The `pilot` plugin holds tickets labelled `pilot` to their contract: an open one has a
`review_by: YYYY-MM-DD` line that is not past, and one is finished only with a note
starting `measured:` and a note starting `ruling:`. The clock here is 2026-01-01.

  $ pm init t >/dev/null
  $ ln -s "$PLUGINS/pilot" "$PM_PLUGINS/pilot"
  $ pm new "try batched snapshots" -l pilot -b "review_by: 2025-12-15" >/dev/null
  $ pm new "try short ids" -l pilot -b "review_by: 2026-02-01" >/dev/null
  $ pm new "try nothing" -l pilot >/dev/null

Its `orient` file adds the overdue ones to bare `pm`.

  $ pm
  ready:
    t-1  P2  open  try batched snapshots
    t-2  P2  open  try short ids
    t-3  P2  open  try nothing
  pilots overdue: t-1
  $ pm pilot
  t-1: review_by 2025-12-15 is past
  t-3: has no review_by: line
  [1]

Its `pre-done` file refuses to finish a pilot that was not measured and ruled on.

  $ pm done t-1 -m "kept"
  pilot: t-1 needs a note starting "measured:" and one starting "ruling:" before it is done.
  [1]
  $ pm note t-1 "measured: 40% fewer commits" >/dev/null && pm note t-1 "ruling: keep" >/dev/null
  $ pm done t-1 -m "kept"
  t-1 done
  $ pm
  ready:
    t-2  P2  open  try short ids
    t-3  P2  open  try nothing
  $ pm pilot
  t-3: has no review_by: line
  [1]
