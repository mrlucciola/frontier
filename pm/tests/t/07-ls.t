`ls` takes words. Status words pick statuses; the rest narrow.

  $ pm init t >/dev/null
  $ pm new "write the lexer" -l lang >/dev/null
  $ pm new "write the parser" -l lang -p 1 >/dev/null
  $ pm new "draft release notes" -b "Mention the lexer rewrite." >/dev/null
  $ pm new "release 1.0" --epic >/dev/null
  $ pm edit t-3 --under t-4
  t-3 edited: under
  $ pm link t-1 blocks t-2
  t-1 blocks t-2
  $ pm take t-1 >/dev/null

With no words: everything not done.

  $ pm ls
  t-2  P1  open  write the parser  blocked by t-1
  t-1  P2  taken  write the lexer  @ada
  t-3  P2  open  draft release notes
  t-4  P2  open  release 1.0 [epic]
  $ pm ls ready
  t-3  P2  open  draft release notes
  $ pm ls mine
  t-1  P2  taken  write the lexer  @ada
  $ pm ls label:lang open
  t-2  P1  open  write the parser  blocked by t-1
  $ pm ls under:t-4
  t-3  P2  open  draft release notes
  $ pm ls epics
  t-4  P2  open  release 1.0 [epic]

Any other word is searched for in titles and bodies.

  $ pm ls lexer
  t-1  P2  taken  write the lexer  @ada
  t-3  P2  open  draft release notes
  $ pm ls done
  nothing matches.

  $ pm done t-1 -m "merged" >/dev/null
  $ pm ls
  t-2  P1  open  write the parser
  t-3  P2  open  draft release notes
  t-4  P2  open  release 1.0 [epic]

A capped list ends with how to see the rest.

  $ pm ls all -n 2
  t-2  P1  open  write the parser
  t-1  P2  done  write the lexer
  +2 more: add -n 0
