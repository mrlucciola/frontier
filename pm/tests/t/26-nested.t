A store inside another store's directory is its own store, even before it has a log.

  $ pm init t >/dev/null
  $ pm new "outer ticket" >/dev/null
  $ mkdir -p inner/.pm && printf '{"prefix":"u"}\n' > inner/.pm/config.json
  $ cd inner && pm ls
  pm: this store's log is missing. Bring it back from its git backup: pm restore
  [1]
  $ pm new "must not land in the outer store"
  pm: this store's log is missing. Bring it back from its git backup: pm restore
  [1]
  $ cd .. && pm ls
  t-1  P2  open  outer ticket

A store that still holds a spec v2 tickets.jsonl says to import it, and the import
fills that store's own log.

  $ mkdir -p old/.pm && cp "$FIXTURES"/v2/* old/.pm/
  $ cd old && pm ls
  pm: this store has not been imported yet. Fill its log: pm import
  [1]
  $ pm import
  imported 4 tickets: 1 open, 1 taken, 1 parked, 1 done
  $ cd .. && pm ls
  t-1  P2  open  outer ticket
  $ pm stores
  t  $T/work
  ol  $T/work/old
