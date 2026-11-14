`take` with no id takes the top ready ticket and prints it, so no `show` is needed.

  $ pm init t >/dev/null
  $ pm new "write the lexer" -b "Tokens first." >/dev/null
  $ pm new "write the parser" >/dev/null
  $ pm take
  t-1  P2  taken  write the lexer  @ada

  Tokens first.

Taking a ticket you hold prints it again and appends nothing.

  $ pm take t-1
  t-1  P2  taken  write the lexer  @ada

  Tokens first.
  $ pm log t-1 -n 1
  {"ts":"2026-01-01T00:00:00Z","by":"ada#e8bc163c","op":"take","id":"t-1"}

Another session cannot take it, and takes the next ready one instead.

  $ export PM_ACTOR=bob PM_SESSION_ID=s2
  $ pm take t-1
  pm: t-1 is taken by ada. Pick another: pm ls ready
  [1]
  $ pm take
  t-2  P2  taken  write the parser  @bob
  $ pm take
  pm: nothing is ready. Everything open: pm ls open
  [1]
  $ pm take t-9
  pm: no ticket t-9. Search: pm ls all <words>
  [1]

`--force` is the operator's override. It records who held the ticket before.

  $ pm take t-1 --force
  t-1  P2  taken  write the lexer  @bob

  Tokens first.

  notes:
    2026-01-01 bob [took over from ada]

`drop` gives a ticket back. Only its holder drops it.

  $ pm drop t-1
  t-1 open
  $ pm drop t-1
  pm: t-1 is open, not taken. Nothing to drop.
  [1]
  $ export PM_ACTOR=ada PM_SESSION_ID=s1
  $ pm drop t-2
  pm: t-2 is taken by bob. Only bob drops it, or the operator with --force.
  [1]
  $ pm drop t-2 --force -m "bob's session ended"
  t-2 open

`--as` names a worker. The ticket still belongs to the session that took it.

  $ pm take t-2 --as worker-1
  t-2  P2  taken  write the parser  @worker-1

  notes:
    2026-01-01 ada [dropped]: bob's session ended
  $ pm ls mine
  t-2  P2  taken  write the parser  @worker-1
