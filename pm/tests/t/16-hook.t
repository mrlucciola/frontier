`pm hook` is what a harness runs. It reads the harness's JSON on stdin and prints text.

Outside a store, session start prints nothing.

  $ printf '{"cwd":"%s","session_id":"s1"}' "$PWD" | pm hook session-start
  $ pm init t >/dev/null
  $ pm new "write the lexer" --take >/dev/null
  $ pm new "write the parser" >/dev/null
  $ printf '{"cwd":"%s","session_id":"s1"}' "$PWD" | pm hook session-start
  pm tickets in this repo:
  yours:
    t-1  P2  taken  write the lexer  @ada
  ready:
    t-2  P2  open  write the parser
  All verbs: pm help

A prompt that names existing tickets gets one line for each, at most three.

  $ printf '{"cwd":"%s","prompt":"is t-2 done yet? also utf-8 and t-99"}' "$PWD" | pm hook prompt
  mentioned:
    t-2  P2  open  write the parser
  $ printf '{"cwd":"%s","prompt":"nothing here"}' "$PWD" | pm hook prompt

Stopping while holding a ticket is blocked once, with the four ways out.

  $ printf '{"cwd":"%s","session_id":"s1"}' "$PWD" | pm hook stop
  You still hold t-1 (write the lexer). Before you stop, run one of:
    pm done t-1 -m "<what landed>"
    pm park t-1 -m "<what it waits on>"
    pm drop t-1
    pm hold t-1 -m "<why it stays yours>"
  [2]
  $ printf '{"cwd":"%s","session_id":"s1","stop_hook_active":true}' "$PWD" | pm hook stop

The session id in the JSON wins over the environment: session s2 holds nothing.

  $ printf '{"cwd":"%s","session_id":"s2"}' "$PWD" | pm hook stop

A held ticket does not block.

  $ pm hold -m "CI still running"
  t-1 held: CI still running
  $ printf '{"cwd":"%s","session_id":"s1"}' "$PWD" | pm hook stop
