`--json` prints one object per line: sorted keys, compact, every key always present.

  $ pm init t >/dev/null
  $ pm new "write the lexer" -l lang --take >/dev/null
  $ pm note "tabs count as one column" -k finding
  t-1 noted
  $ pm show t-1 --json
  {"blocked_by":[],"blocks":[],"body":"","created":"2026-01-01T00:00:00Z","findings":null,"from":null,"hold":null,"holder":"ada#e8bc163c","id":"t-1","kind":"task","labels":["lang"],"notes":[{"by":"ada#e8bc163c","kind":"finding","text":"tabs count as one column","ts":"2026-01-01T00:00:00Z"}],"pri":2,"reason":null,"related":[],"status":"taken","title":"write the lexer","under":null,"updated":"2026-01-01T00:00:00Z"}
  $ pm new "write the parser" --blocked-by t-1 >/dev/null
  $ pm ls open --json
  {"blocked_by":["t-1"],"blocks":[],"body":"","created":"2026-01-01T00:00:00Z","findings":null,"from":null,"hold":null,"holder":null,"id":"t-2","kind":"task","labels":[],"notes":[],"pri":2,"reason":null,"related":[],"status":"open","title":"write the parser","under":null,"updated":"2026-01-01T00:00:00Z"}
