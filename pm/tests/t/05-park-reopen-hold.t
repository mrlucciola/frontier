`park` stops work that is not finished and says what it waits on.

  $ pm init t >/dev/null
  $ pm new "port the tests" --take
  t-1
  $ pm park
  pm: park needs -m "what it waits on".
  usage: pm park [id] -m "text"
  [2]
  $ pm park -m "waits on the operator's ruling about fixtures"
  t-1 parked
  $ pm
  parked:
    t-1  P2  parked  port the tests
  $ pm show t-1
  t-1  P2  parked  port the tests

  notes:
    2026-01-01 ada [parked]: waits on the operator's ruling about fixtures

Taking a parked ticket resumes it. Bare `take` never picks a parked one.

  $ pm take
  pm: nothing is ready. Everything open: pm ls open
  [1]
  $ pm take t-1
  t-1  P2  taken  port the tests  @ada

  notes:
    2026-01-01 ada [parked]: waits on the operator's ruling about fixtures

`reopen` makes a done or parked ticket open.

  $ pm done -m "ported"
  t-1 done
  $ pm reopen t-1
  t-1 open
  $ pm reopen t-1
  pm: t-1 is open already.
  [1]

`hold` keeps a taken ticket across a pause.

  $ pm hold t-1 -m "x"
  pm: t-1 is open, not yours. Take it first: pm take t-1
  [1]
  $ pm take t-1 >/dev/null
  $ pm hold -m "CI run 4512 is still going"
  t-1 held: CI run 4512 is still going
  $ pm show t-1
  t-1  P2  taken  port the tests  @ada
  hold: CI run 4512 is still going

  notes:
    2026-01-01 ada [parked]: waits on the operator's ruling about fixtures
    2026-01-01 ada [done]: ported

  $ pm new "other" >/dev/null
  $ pm park t-2 -m "x"
  pm: t-2 is open, not yours. Take it first: pm take t-2
  [1]
