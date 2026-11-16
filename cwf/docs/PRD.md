# CWF product requirements

Status: accepted 2026-11-16. This page decides what CWF is for. The
[specification](/cwf/docs/SPECIFICATION.md) describes how the current
implementation works; where the two disagree, this page wins, and a mechanism
that serves no requirement here is a candidate to cut
([principle 8](/docs/component-principles.md)).

## Problem

Coding agents redo work that already exists, add a second solution beside an
accepted one, lose decisions between sessions, and verify against the wrong
context. Each of these costs a correction or a rework turn. The cost that matters
is the cost to an accepted result, including the operator's interventions, not
the size of the first response.

## Product

CWF is a set of instructions tuned for the agent harness that loads them:

- **Skills,** one per kind of work, each complete on its own.
- **An instruction block** in the harness's global instruction file that tells
  the agent when a CWF skill applies.
- **Scripts and hooks,** only where they measurably help on that harness. Each
  piece is chosen per harness; nothing is added to one harness because another
  has it.

Two things supplement the core and are never required by it:

- **A command-line tool** for mechanical work: bounded file discovery, targeted
  reads, dependency and ownership checks on a batch, explicit command checks.
  Every skill states what to do when the tool is unavailable.
- **Local state** under `~/.local/state/cwf`. Deleting it loses only what was
  recorded and breaks nothing.

## Users and context

One operator, deploying once per user on macOS. The supported harness is
opencode. Work happens inside and outside repositories, from ordinary prompts,
batches, or tickets.

## Requirements

| ID | Requirement |
| --- | --- |
| R01 | Deploy once per user with `deploy.sh`: links into the checkout and one marked block. A source edit is live without redeploying, except a new skill or changed block text. No per-repository setup. |
| R02 | Support opencode. Add another harness only with its own files and evidence that each piece helps there. Keep text that differs per harness in per-harness files. |
| R03 | Cover product and strategy work, architecture and design, documentation, planning, implementation and review, and maintaining CWF itself. |
| R04 | Treat ordinary prompts and batches as first-class input. Tickets are one optional input; CWF never requires a ticket store. |
| R05 | Before introducing a solution, look for an existing implementation, convention or accepted decision that already covers it, and reuse or extend it where it fits. |
| R06 | Apply the right skill without being named on substantive work, and stay out of unrelated or trivial requests. Context gathering is proportionate to the task. |
| R07 | Mechanical discovery and checks go to deterministic tools; semantic judgment stays with the agent. Tool output is evidence, not instruction. |
| R08 | Support single-agent and multi-agent work: dependency order, exclusive write ownership, and integrated acceptance across the parts. |
| R09 | Shared knowledge changes (instructions, decisions, documentation) go through the repository's own review. CWF may keep private, labelled local notes; it never promotes them to policy. |
| R10 | Operate independently of other components, referring to them only by role. Add an adapter only after reading the other side's actual interface. |
| R11 | Work across repositories, configurations, users and machines with no implicit sharing between users. |
| R12 | Overhead is accepted only where it reduces rework, and every claim about it is measured. |
| R13 | The checkout is the only copy. No release directories, version pointers, manifests, checksums, receipts, install journals or integrity checks; git history records change. |

## Non-goals

- **Tracking work.** Status, claims, handoffs and continuation of tracked work
  belong to the repository's ticket store. CWF does not compete with it.
- **Managing checkouts** where the repository has a worktree tool.
- **Installation machinery:** versions, upgrades, rollback, packaging, integrity
  verification.
- **Background services,** embeddings, remote memory, transcript capture,
  cross-user synchronisation.
- **Publishing** tickets or messages, changing permissions, or rewriting the
  harness's own configuration file.

## Success measures

Measured on paired, interleaved cohorts of the six evaluation scenarios against
the same harness, model and settings without CWF. Results are from the first
cohort (opencode 2.0.32, 2026-11-15, three runs per scenario per arm).

| Measure | Target | First cohort |
| --- | --- | --- |
| Quality | No scenario passes less often than the baseline | Fails: the short-answer scenario passed 1/3 against 3/3 |
| Cost to accepted result | Median total input at least 20% below the baseline | Fails: +3.3% |
| Activation without naming (R06) | Not set | Planning skill 3/3; build and design skills 0/6 |
| Activation when named | Every named skill loads | 9/9 |
| Stays out of unrelated requests | No CWF skill loads | Holds; the six skill descriptions still cost about 390 tokens on every step |
| Fixed cost per step | Not set | About 390 tokens |

The first cohort's decision was revise. The gains to keep: the planning scenario
passed 3/3 against 0/3, and the coding scenario used 12.7% less total input.

## Mechanisms and the requirement each serves

| Mechanism | Serves | Status |
| --- | --- | --- |
| Six skills | R03, R05, R06 | Keep; build and design miss R06 |
| Shared pattern files | R05 | Keep; the skills reach them by a relative link that breaks under a symlinked skill directory |
| Instruction block | R06 | Keep |
| `deploy.sh` | R01, R13 | Keep |
| `discover`, `inspect-source` | R05, R07 | Keep |
| `batch validate` | R08 | Keep |
| `check` | R07 | Keep |
| JSON schemas | R07 | Keep |
| `observe` and the observation store | R09 | Kept; worth developing, no work planned |
| `checkpoint`, `resume` | R04, for untracked work only | Kept; overlaps the ticket store, no work planned |
| Worktree helpers | R08 isolation | Review: overlaps the worktree tool |
| Discovery cache | None: a cached result is never returned | Cut candidate |
| Checkpoint version pin and state schema version | None (R13) | Cut candidate |
| `scripts/author_content.py`, generating skills and patterns from Python strings | None: the skill file is not its own source | Review |

## Evidence

The first cohort, its pre-registration and scoring are on ticket fc-686428; the
revision work is fc-dbdea5; the pattern-link defect is fc-122dd5.
