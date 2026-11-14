`new` prints only the id. `show` prints the one-line form, then links, body and notes.

  $ pm init t >/dev/null
  $ pm new "write the lexer"
  t-1
  $ pm new "write the parser" -b "Recursive descent.
  > One function per rule." -p 1 -l lang -l parser
  t-2
  $ pm show t-1
  t-1  P2  open  write the lexer

A bare number names a ticket in this store.

  $ pm show 2
  t-2  P1  open  write the parser
  labels: lang, parser

  Recursive descent.
  One function per rule.

`--take` files and takes in one call. `--as` names the holder.

  $ pm new "write the printer" --take --as worker-1
  t-3
  $ pm show t-3
  t-3  P2  taken  write the printer  @worker-1

  $ pm new
  pm: new needs a title.
  usage: pm new "title" [-b body] [-p 0-4] [-l label] [--epic] [--under id] [--from id] [--blocks id] [--blocked-by id] [--take] [--as name] [--new]
  [2]
  $ pm show t-9
  pm: no ticket t-9. Search: pm ls all <words>
  [1]
