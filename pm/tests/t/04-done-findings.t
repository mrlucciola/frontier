`done` finishes the ticket this session holds, or the ones named.

  $ pm init t >/dev/null
  $ pm new "write the lexer" --take
  t-1
  $ pm done -m "merged"
  t-1 done
  $ pm show t-1
  t-1  P2  done  write the lexer

  notes:
    2026-01-01 ada [done]: merged
  $ pm done t-1
  pm: t-1 is already done.
  [1]

An open ticket can be finished without taking it, with a reason other than done.

  $ pm new "obsolete idea"
  t-2
  $ pm done t-2 --reason wont-fix -m "the lexer covers it"
  t-2 done
  $ pm show t-2
  t-2  P2  done  obsolete idea
  reason: wont-fix

  notes:
    2026-01-01 ada [done]: the lexer covers it

Several ids are all or nothing.

  $ pm new "a" >/dev/null; pm new "b" >/dev/null
  $ pm done t-3 t-4 t-9
  pm: no ticket t-9. Search: pm ls all <words>
  [1]
  $ pm ls
  t-3  P2  open  a
  t-4  P2  open  b
  $ pm done t-3 t-4
  t-3 done
  t-4 done

With `findings_required`, finishing needs an attestation.

  $ printf '{"prefix":"t","findings_required":true}\n' > .pm/config.json
  $ pm new "tune the scanner" --take
  t-5
  $ pm done
  pm: t-5 needs --findings: none, or the ids of the tickets that took the findings.
  Repeat: pm done t-5 --findings none -m "<what you checked>"
  [1]
  $ pm done --findings none
  pm: --findings none needs a reason. Add -m "<what you checked>"
  [1]
  $ pm done --findings t-9
  pm: no ticket t-9. Search: pm ls all <words>
  [1]
  $ pm new "scanner misreads tabs" --from t-5
  t-6
  $ pm done --findings t-6
  t-5 done
  $ pm show t-5
  t-5  P2  done  tune the scanner
  findings: t-6
  $ pm show t-6
  t-6  P2  open  scanner misreads tabs
  from: t-5

`--dry-run` checks and appends nothing.

  $ pm new "last one" --take
  t-7
  $ pm done --dry-run
  pm: t-7 needs --findings: none, or the ids of the tickets that took the findings.
  Repeat: pm done t-7 --findings none -m "<what you checked>"
  [1]
  $ pm done --dry-run --findings none -m "nothing found"
  ok: t-7 can be done
  $ pm get t-7 status
  taken

Only the holder finishes a taken ticket.

  $ export PM_ACTOR=bob PM_SESSION_ID=s2
  $ pm done t-7 --findings none -m "x"
  pm: t-7 is taken by ada. Only ada finishes it, or the operator with --force.
  [1]
