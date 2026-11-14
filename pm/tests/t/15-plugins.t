A plugin is a directory of executables. pm finds them by name and knows nothing else.

  $ pm init t >/dev/null
  $ mkdir -p "$PM_PLUGINS/guard" "$PM_PLUGINS/hello"
  $ printf '#!/bin/sh\necho "hello from $PM_STORE: $*"\n' > "$PM_PLUGINS/hello/cmd"
  $ printf '#!/bin/sh\necho "next: guard saw $PM_BY take $PM_ID"\n' > "$PM_PLUGINS/guard/post-take"
  $ printf '#!/bin/sh\n[ -f "$PM_STORE/merged" ] && exit 0\necho "guard: $PM_ID is not merged. Merge it, then: pm done $PM_ID"\nexit 1\n' > "$PM_PLUGINS/guard/pre-done"
  $ printf '#!/bin/sh\necho "guard: 1 worktree has uncommitted work"\n' > "$PM_PLUGINS/guard/orient"
  $ chmod +x "$PM_PLUGINS"/*/*

`cmd` is a subcommand.

  $ pm hello a b
  hello from $T/work: a b

`post-<op>` adds lines after the verb's output. `orient` adds lines to bare `pm`.

  $ pm new "write the lexer" --take
  t-1
  next: guard saw ada#e8bc163c take t-1
  $ pm
  yours:
    t-1  P2  taken  write the lexer  @ada
  guard: 1 worktree has uncommitted work

`pre-<op>` can refuse. Its output is the refusal, and nothing is appended.

  $ pm done -m "merged"
  guard: t-1 is not merged. Merge it, then: pm done t-1
  [1]
  $ pm get t-1 status
  taken
  $ touch merged && pm done -m "merged"
  t-1 done
  $ pm help | tail -1
  plugins: guard, hello

Removing the directory removes the plugin.

  $ rm -r "$PM_PLUGINS/guard"
  $ pm new "write the parser" --take
  t-2
  $ pm done -m "no guard now"
  t-2 done
