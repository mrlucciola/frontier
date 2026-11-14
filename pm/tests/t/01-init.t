A store starts with `pm init <prefix>`. Before that, a verb says how to start one.

  $ pm new "too early"
  pm: no store here. Start one: pm init <prefix>
  [1]
  $ pm init t
  ready: t ($T/work/.pm)
  For agents without hooks, add to AGENTS.md: Tickets live in .pm/. Run `pm`.
  $ cat .pm/config.json
  {"prefix":"t"}
  $ pm stores
  t  $T/work

The store is found from any directory below it.

  $ mkdir -p deep/er && cd deep/er && pm new "filed from below"
  t-1
  $ cd ../..

A prefix is taken once, and a directory holds one store.

  $ mkdir ../other && cd ../other
  $ pm init T1
  pm: a prefix is 1 to 8 lowercase letters or digits, starting with a letter.
  usage: pm init prefix
  [2]
  $ pm init t
  pm: prefix t belongs to $T/work. Choose another.
  [1]
  $ cd ../work && pm init x
  pm: this directory already has a store, prefix t.
  [1]
