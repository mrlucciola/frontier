A dry run runs `pre` hooks and no `post` hooks. A plugin that refuses without saying
why is still named. A plugin file that cannot run is reported, never a traceback.

  $ pm init t >/dev/null
  $ mkdir -p "$PM_PLUGINS/seen" "$PM_PLUGINS/mute"
  $ printf '#!/bin/sh\necho "pre-done saw $PM_ID" >> "$PM_STORE/seen.log"\n' > "$PM_PLUGINS/seen/pre-done"
  $ printf '#!/bin/sh\necho "post-done ran"\n' > "$PM_PLUGINS/seen/post-done"
  $ printf '#!/bin/sh\nexit 1\n' > "$PM_PLUGINS/mute/pre-drop"
  $ printf 'not a script\n' > "$PM_PLUGINS/mute/cmd"
  $ chmod +x "$PM_PLUGINS"/*/*
  $ pm new "write the lexer" --take >/dev/null
  $ pm done --dry-run -m "checked"
  ok: t-1 can be done
  $ cat seen.log
  pre-done saw t-1

  $ pm drop
  pm: plugin mute refused drop t-1.
  [1]
  $ pm get t-1 status
  taken

  $ pm mute
  pm: plugin mute could not run cmd: Exec format error.
  [1]

A plugin event name is a namespace and a name, letters, digits, `-` and `_` only.

  $ pm emit t-1 wt/x.y a=1
  pm: emit takes a namespaced name such as wt.start. Plain names belong to pm.
  [1]

The real change runs both hooks.

  $ pm done -m "merged"
  t-1 done
  post-done ran
  $ cat seen.log
  pre-done saw t-1
  pre-done saw t-1
