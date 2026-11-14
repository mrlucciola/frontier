A verb with `[id]` left out acts on the one ticket this session holds.

  $ pm init t >/dev/null
  $ pm note "x"
  pm: you hold no ticket. Name one, or take one: pm take
  [1]
  $ pm new "one" --take >/dev/null; pm new "two" --take >/dev/null
  $ pm note "x"
  pm: you hold t-1, t-2. Name one.
  [1]
  $ pm note t-2 "x"
  t-2 noted
  $ pm drop t-2
  t-2 open
  $ pm note "now there is one"
  t-1 noted
  $ pm show
  t-1  P2  taken  one  @ada

  notes:
    2026-01-01 ada: now there is one

A first word that is a number or an id is the ticket, not the text.

  $ pm note 2 "bare numbers work in this store"
  t-2 noted
  $ pm get t-2 status
  open
