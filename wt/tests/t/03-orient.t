orient lists worktrees whose ticket is done or unheld, and is silent otherwise.

  $ pm init t >/dev/null
  $ ln -s "$FIXTURES/../../../wt/pm-plugin" "$PM_PLUGINS/wt"
  $ pm new "held" --take
  t-1
  $ mkdir -p .worktrees/t-1
  $ pm | grep -c '^wt:'
  0
  [1]

An unheld ticket and a done ticket each get a line.

  $ pm new "unheld"
  t-2
  $ pm new "finished" --take
  t-3
  next: wt start t-3
  $ WT_CALLER=1 pm done t-3 -m x
  t-3 done
  $ mkdir -p .worktrees/t-2 .worktrees/t-3
  $ pm | grep '^wt:'
  wt: t-2 has a worktree and no holder. Run: wt start t-2 to resume it, or wt park t-2 to set it aside
  wt: t-3 is done but its worktree remains. Run: wt finish t-3
