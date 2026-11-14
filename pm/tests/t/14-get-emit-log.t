`get` prints one value per line. It is how a shell script reads a ticket.

  $ pm init t >/dev/null
  $ pm new "write the lexer" -l lang --take
  t-1
  $ pm get t-1 status holder pri kind labels store
  taken
  ada#e8bc163c
  2
  task
  lang
  $T/work
  $ pm get t-1 colour
  pm: no field colour. Fields: status holder title pri kind under labels blocked-by blocks store body, or a plugin's ns.key
  usage: pm get id field [field ...]
  [2]

`emit` appends a plugin's event. pm stores it and gives it no meaning.

  $ pm emit t-1 wt.start branch=t-1 path=.worktrees/t-1
  $ pm emit t-1 wt.park sha=abc123
  $ pm get t-1 wt.branch wt.sha
  t-1
  abc123
  $ pm emit t-1 start x=1
  pm: emit takes a namespaced name such as wt.start. Plain names belong to pm.
  [1]
  $ pm show t-1
  t-1  P2  taken  write the lexer  @ada
  labels: lang

`log` prints the stored lines.

  $ pm log t-1
  {"ts":"2026-01-01T00:00:00Z","by":"ada#e8bc163c","op":"new","id":"t-1","labels":["lang"],"title":"write the lexer"}
  {"ts":"2026-01-01T00:00:00Z","by":"ada#e8bc163c","op":"take","id":"t-1"}
  {"ts":"2026-01-01T00:00:00Z","by":"ada#e8bc163c","op":"wt.start","id":"t-1","branch":"t-1","path":".worktrees/t-1"}
  {"ts":"2026-01-01T00:00:00Z","by":"ada#e8bc163c","op":"wt.park","id":"t-1","sha":"abc123"}
