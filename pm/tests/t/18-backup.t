Inside a git checkout, every append is backed up as one blob at refs/pm/log.

  $ git init -q -b main . && pm init t
  ready: t ($T/work/.pm)
  For agents without hooks, add to AGENTS.md: Tickets live in .pm/. Run `pm`.
  $ cat .gitignore
  .pm/log.jsonl
  $ pm new "write the lexer" >/dev/null && pm new "write the parser" >/dev/null
  $ git cat-file -p refs/pm/log | wc -l | tr -d ' '
  2
  $ pm doctor
  ok: t, 2 tickets, 2 events
  backup: refs/pm/log is current

A lost log comes back with `restore`.

  $ rm .pm/log.jsonl
  $ pm ls
  pm: this store's log is missing. Bring it back from its git backup: pm restore
  [1]
  $ pm restore
  restored 2 events from refs/pm/log
  $ pm ls
  t-1  P2  open  write the lexer
  t-2  P2  open  write the parser
  $ pm restore
  pm: the log has 2 events and the backup has 2. Nothing to restore.
  [1]

A linked worktree uses the main checkout's store.

  $ git add .gitignore .pm/config.json && git commit -qm init
  $ git worktree add -q -b side ../side
  $ cd ../side && pm ls
  t-1  P2  open  write the lexer
  t-2  P2  open  write the parser
  $ pm new "found in the worktree"
  t-3
  $ cd ../work && pm ls
  t-1  P2  open  write the lexer
  t-2  P2  open  write the parser
  t-3  P2  open  found in the worktree
