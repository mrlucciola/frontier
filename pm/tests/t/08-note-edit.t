`note` adds a note to the held ticket or the one named.

  $ pm init t >/dev/null
  $ pm new "write the lexer" --take
  t-1
  $ pm note "tabs count as one column"
  t-1 noted
  $ pm note t-1 "use a table-driven scanner" -k decision
  t-1 noted
  $ pm note -k verdict "x"
  pm: a note kind is one of: decision, finding, measurement.
  usage: pm note [id] "text" [-k decision|finding|measurement]
  [2]
  $ pm show t-1
  t-1  P2  taken  write the lexer  @ada

  notes:
    2026-01-01 ada: tabs count as one column
    2026-01-01 ada [decision]: use a table-driven scanner

`show` prints the last five notes and says how to see the rest.

  $ for n in 1 2 3 4 5; do pm note "step $n" >/dev/null; done
  $ pm note "first line
  > second line"
  t-1 noted
  $ pm show t-1
  t-1  P2  taken  write the lexer  @ada

  notes (last 5 of 8; all: pm show t-1 --notes):
    2026-01-01 ada: step 2
    2026-01-01 ada: step 3
    2026-01-01 ada: step 4
    2026-01-01 ada: step 5
    2026-01-01 ada: first line
      second line

`edit` changes fields and says which.

  $ pm edit t-1 --title "write the scanner" -p 1 -l lang
  t-1 edited: title, pri, labels
  $ pm edit t-1 --body "Table-driven."
  t-1 edited: body
  $ pm edit t-1 --unlabel lang -l front
  t-1 edited: labels
  $ pm get t-1 title pri labels body
  write the scanner
  1
  front
  Table-driven.
  $ pm edit t-1
  pm: edit needs something to change.
  usage: pm edit id [--title text] [--body text] [-p 0-4] [-l label] [--unlabel label] [--under id|none]
  [2]
