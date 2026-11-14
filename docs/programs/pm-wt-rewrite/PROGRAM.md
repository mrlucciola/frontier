# Program: pm and wt rewrite

Design, rulings and gates: [PLAN.md](/docs/programs/pm-wt-rewrite/PLAN.md).
Each initiative is one epic and one overseer session, launched from its seed.
Launch them in the order of the last column; rule on each before the next.

| # | Initiative | Epic | Seed | Launch when |
| --- | --- | --- | --- | --- |
| 01 | pm port | fc-c3514f | closed 2026-11-14; initiative directory last tracked at `205a255` (`git show 205a255:docs/programs/pm-wt-rewrite/initiatives/01-pm/INITIATIVE.md`) | done |
| 04 | pm redesign | fc-2a6562 | [seed](/docs/programs/pm-wt-rewrite/initiatives/04-pm-log/seed.md) | now |
| 02 | wt | fc-262fa8 | [seed](/docs/programs/pm-wt-rewrite/initiatives/02-wt/seed.md) | fc-2a6562 closed and accepted |
| 03 | delivery | fc-ccecda | [seed](/docs/programs/pm-wt-rewrite/initiatives/03-delivery/seed.md) | fc-262fa8 closed and accepted |

State lives in the ticket store: `pm ticket tree <epic id>`. Each initiative's
ledger is the `INITIATIVE.md` beside its seed.

The cutover is operator-run from the runbook that initiative 03 writes. It is
not launched from here.
