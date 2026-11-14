Edge cases the readability review found.

`ls --json` prints only objects, so an empty result prints nothing.

  $ pm init t >/dev/null
  $ pm ls --json

The pilot plugin adds nothing to a store without pilot tickets.

  $ ln -s "$PLUGINS/pilot" "$PM_PLUGINS/pilot"
  $ pm new "write the lexer" >/dev/null
  $ pm
  ready:
    t-1  P2  open  write the lexer
  $ pm pilot

A store path may contain spaces.

  $ mkdir "../my lib" && cd "../my lib" && pm init u >/dev/null && pm new "ship the library" >/dev/null && cd ../work
  $ pm stores
  t  $T/work
  u  $T/my lib
  $ pm show u-1
  u-1  P2  open  ship the library

`new --blocks` naming a ticket in another store would write the link into the wrong
log, so it refuses before filing.

  $ pm new "use the library" --blocks u-1
  pm: u-1 is in another store. File without --blocks, then: pm link <new id> blocks u-1
  [1]
  $ pm ls
  t-1  P2  open  write the lexer

`log` reads the ticket's own store.

  $ pm log u-1
  {"ts":"2026-01-01T00:00:00Z","by":"ada#e8bc163c","op":"new","id":"u-1","title":"ship the library"}

Import writes history, so plugin hooks do not run for its events.

  $ mkdir "$PM_PLUGINS/guard" && printf '#!/bin/sh\necho "guard refuses"\nexit 1\n' > "$PM_PLUGINS/guard/pre-done" && chmod +x "$PM_PLUGINS/guard/pre-done"
  $ mkdir ../old && cd ../old && mkdir .pm && cp "$FIXTURES"/v2/* .pm/ && pm import
  imported 4 tickets: 1 open, 1 taken, 1 parked, 1 done
