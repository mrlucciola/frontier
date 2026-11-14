Bare `pm` is the first call of a session: what you hold, what is ready, what is parked.

  $ pm init t >/dev/null
  $ for n in 1 2 3 4 5 6 7; do pm new "task $n" >/dev/null; done
  $ pm new "urgent fix" -p 0 >/dev/null
  $ pm new "release" --epic >/dev/null
  $ pm new "task 10" >/dev/null
  $ pm take t-1 >/dev/null
  $ pm link t-2 blocks t-3
  t-2 blocks t-3
  $ pm take t-4 >/dev/null && pm park t-4 -m "needs a ruling"
  t-4 parked

A blocked ticket and an epic are not ready. Five are shown, then a count.

  $ pm
  yours:
    t-1  P2  taken  task 1  @ada
  ready:
    t-8  P0  open  urgent fix
    t-2  P2  open  task 2
    t-5  P2  open  task 5
    t-6  P2  open  task 6
    t-7  P2  open  task 7
    +1 more: pm ls ready
  parked:
    t-4  P2  parked  task 4

Another session has no `yours` section.

  $ export PM_ACTOR=bob PM_SESSION_ID=s2
  $ pm
  ready:
    t-8  P0  open  urgent fix
    t-2  P2  open  task 2
    t-5  P2  open  task 5
    t-6  P2  open  task 6
    t-7  P2  open  task 7
    +1 more: pm ls ready
  parked:
    t-4  P2  parked  task 4
