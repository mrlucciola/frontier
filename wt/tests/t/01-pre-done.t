wt's pre-done refuses a direct pm done while the ticket's worktree exists.

  $ pm init t >/dev/null
  $ ln -s "$FIXTURES/../../../wt/pm-plugin" "$PM_PLUGINS/wt"
  $ pm new "one" --take
  t-1
  $ mkdir -p .wt/t-1
  $ pm done -m "x"
  wt: t-1 has a worktree. Run: wt finish t-1 (merge and close) or wt park t-1 (set aside)
  [1]
  $ pm get t-1 status
  taken

wt itself passes with WT_CALLER=1.

  $ WT_CALLER=1 pm done t-1 -m "x"
  t-1 done

A ticket whose worktree is gone is not guarded.

  $ pm new "two" --take
  t-2
  next: wt start t-2
  $ mkdir -p .wt/t-2
  $ rmdir .wt/t-2
  $ pm done -m "x"
  t-2 done
