`doctor` checks the store. A line that is not an event is skipped by every verb.

  $ pm init t >/dev/null
  $ pm new "write the lexer" >/dev/null
  $ pm doctor
  ok: t, 1 ticket, 1 event
  $ printf 'not json\n' >> .pm/log.jsonl
  $ pm doctor
  line 2 is not an event; pm skips it. Delete the line by hand.
  [1]
  $ pm ls
  t-1  P2  open  write the lexer
  $ pm new "write the parser"
  t-2
