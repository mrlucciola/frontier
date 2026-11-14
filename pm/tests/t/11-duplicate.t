`new` refuses a ticket that looks like one already filed, and says both ways out.

  $ pm init t >/dev/null
  $ pm new "scanner misreads tabs inside string literals"
  t-1
  $ pm new "scanner misreads tabs inside string literals again"
  pm: this looks like t-1  P2  open  scanner misreads tabs inside string literals
  Same work: pm note t-1 "seen again: <where>"
  Different work: repeat with --new
  [1]
  $ pm new "scanner misreads tabs inside string literals again" --new
  t-2
  $ pm new "write the changelog"
  t-3
