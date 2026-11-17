post-take hints wt start only in a repository that uses worktrees.

  $ pm init t >/dev/null
  $ ln -s "$FIXTURES/../../../wt/pm-plugin" "$PM_PLUGINS/wt"
  $ pm new "one" --take
  t-1
  $ mkdir -p .wt
  $ pm new "two" --take
  t-2
  next: wt start t-2
  $ WT_CALLER=1 pm new "three" --take
  t-3
