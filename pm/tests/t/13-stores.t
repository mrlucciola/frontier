An id is routed to its store by its prefix, from any directory.

  $ pm init t >/dev/null
  $ mkdir ../lib && cd ../lib && pm init u >/dev/null
  $ pm new "ship the library"
  u-1
  $ cd ../work
  $ pm stores
  t  $T/work
  u  $T/lib

A ticket can wait on one in another store.

  $ pm new "use the library" --blocked-by u-1
  t-1
  $ pm show u-1
  u-1  P2  open  ship the library
  blocks: t-1
  $ pm ls
  t-1  P2  open  use the library  blocked by u-1
  $ pm take u-1 >/dev/null && pm done u-1 -m "shipped"
  u-1 done
  $ pm ls ready
  t-1  P2  open  use the library
  $ pm get u-1 store
  $T/lib
  $ pm ls all --all-stores
  t-1  P2  open  use the library
  u-1  P2  done  ship the library

  $ pm show zz-1
  pm: no store has prefix zz. Known: t, u
  [1]

A store marked `ro` in the registry answers reads and refuses changes.

  $ printf 't %s\nu %s ro\n' "$T/work" "$T/lib" > "$PM_STORES"
  $ pm stores
  t  $T/work
  u  $T/lib  ro
  $ pm note u-1 "late thought"
  pm: store u is read-only ($T/lib).
  [1]
  $ pm show u-1
  u-1  P2  done  ship the library

  notes:
    2026-01-01 ada [done]: shipped
