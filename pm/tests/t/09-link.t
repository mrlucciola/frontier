`link a blocks b` orders tickets. A blocked ticket is not ready and cannot be taken.

  $ pm init t >/dev/null
  $ pm new "write the lexer" >/dev/null
  $ pm new "write the parser" >/dev/null
  $ pm new "write the printer" >/dev/null
  $ pm link t-1 blocks t-2 t-3
  t-1 blocks t-2
  t-1 blocks t-3
  $ pm show t-2
  t-2  P2  open  write the parser  blocked by t-1
  $ pm show t-1
  t-1  P2  open  write the lexer
  blocks: t-2, t-3
  $ pm take t-2
  pm: t-2 is blocked by t-1. Pick another: pm ls ready
  [1]
  $ pm take t-2 --force >/dev/null && pm drop t-2
  t-2 open

A cycle is refused. Adding a link that exists changes nothing.

  $ pm link t-2 blocks t-1
  pm: t-1 already blocks t-2. That would be a cycle.
  [1]
  $ pm link t-1 blocks t-2
  t-1 blocks t-2
  $ pm log t-2 -n 1
  {"ts":"2026-01-01T00:00:00Z","by":"ada#e8bc163c","op":"drop","id":"t-2"}

`related` shows on both tickets and gates nothing.

  $ pm link t-1 related t-3
  t-1 related t-3
  $ pm show t-3
  t-3  P2  open  write the printer  blocked by t-1
  related: t-1

A done blocker stops blocking.

  $ pm done t-1 -m "merged"
  t-1 done
  $ pm ls ready
  t-2  P2  open  write the parser
  t-3  P2  open  write the printer

`unlink` removes every link between two tickets.

  $ pm unlink t-1 t-3
  t-1 and t-3 unlinked
  $ pm unlink t-1 t-3
  pm: no link between t-1 and t-3.
  [1]

`new` can link as it files.

  $ pm new "write the docs" --blocked-by t-2 --blocks t-3
  t-4
  $ pm ls
  t-2  P2  open  write the parser
  t-3  P2  open  write the printer  blocked by t-4
  t-4  P2  open  write the docs  blocked by t-2
