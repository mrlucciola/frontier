An epic groups tickets. It is finished after its children.

  $ pm init t >/dev/null
  $ pm new "release 1.0" --epic
  t-1
  $ pm new "write the changelog" --under t-1 >/dev/null
  $ pm new "tag the commit" --under t-1 >/dev/null
  $ pm new "stray" --under t-2
  pm: t-2 is not an epic. Make one: pm new "title" --epic
  [1]
  $ pm show t-1
  t-1  P2  open  release 1.0 [epic]
  children: 2 open
    t-2  P2  open  write the changelog
    t-3  P2  open  tag the commit
  $ pm show t-2
  t-2  P2  open  write the changelog
  under: t-1 release 1.0
  $ pm done t-1
  pm: t-1 has children not done: t-2, t-3. Finish them, or move one out: pm edit t-2 --under none
  [1]

Finishing the last child says what comes next.

  $ pm done t-2
  t-2 done
  $ pm done t-3
  t-3 done
  next: every child of t-1 is done. Finish the epic: pm done t-1
  $ pm show t-1
  t-1  P2  open  release 1.0 [epic]
  children: 2 done
  $ pm done t-1
  t-1 done
