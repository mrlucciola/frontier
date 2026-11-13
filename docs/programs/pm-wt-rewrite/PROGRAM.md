# Program: pm and wt rewrite

Design, rulings and gates: [PLAN.md](/docs/programs/pm-wt-rewrite/PLAN.md).
Each initiative is one epic and one overseer session, launched from its seed.
Launch them in order; rule on each before launching the next.

| # | Initiative | Epic | Seed | Launch when |
| --- | --- | --- | --- | --- |
| 01 | pm | fc-c3514f | [seed](/docs/programs/pm-wt-rewrite/initiatives/01-pm/seed.md) | now |
| 02 | wt | fc-262fa8 | [seed](/docs/programs/pm-wt-rewrite/initiatives/02-wt/seed.md) | fc-c3514f closed and accepted |
| 03 | delivery | fc-ccecda | [seed](/docs/programs/pm-wt-rewrite/initiatives/03-delivery/seed.md) | fc-262fa8 closed and accepted |

State lives in the ticket store: `pm ticket tree <epic id>`. Each initiative's
ledger is the `INITIATIVE.md` beside its seed.

The cutover is operator-run from the runbook that initiative 03 writes. It is
not launched from here.
