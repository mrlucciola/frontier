# pm

Ticket store for agent work: one JSONL file per repository under `.pm/`, plain files
that live in each repo.

The installed `pm` stays the frontier one in `~/frontier/runtime-tools/pm` until the
operator's cutover. This component is built and at parity with it; it is not on
`PATH` until then.

## Entry points

`pm/cli/pm` dispatches two families to `pm/tools/ticket`:

- `pm ticket <verb>`: the ledger and its lifecycle verbs.
- `pm view board|overview`: read-only renderers over the same store.

Exit codes and refusal texts are those of the frontier CLI. A verb takes `--store
<repo root>` to pick a store other than the working directory's; an id written
`<prefix>/<id>` is routed to the store that owns that prefix.

## Verbs

| Verb | Does |
| --- | --- |
| `init` | Create a store in a repo root (`--prefix`) |
| `create` | File a ticket; prints its id |
| `show`, `list`, `ready`, `tree`, `summary` | Read a ticket, filter the ledger, list unblocked work, show impact around a ticket, brief a session start |
| `claim`, `hold`, `release` | Take a ticket, mark the claim in flight, give it back |
| `close`, `reopen` | Finish tickets (`--unmerged` when the merge is gated) or reopen them |
| `note`, `edit` | Append a timestamped note; change title, priority or body |
| `dep`, `unlink`, `reparent` | Add or remove `blocks`/`related` edges; move a ticket under another epic |
| `where` | Print the repo that owns an id; `--mutate` preflights a close or release |
| `stores` | List the registry; `--check` reports problems |
| `history` | Keep history on `refs/heads/pm-store` (`status\|enable\|disable\|sync\|restore`) |
| `validate`, `lint` | Check stores and ticket bodies |
| `archive` | Move closed rows to `archive/tickets-<yyyy>.jsonl` |
| `board`, `overview` | The view renderers, also reachable as `pm view` |

Anything the [cut list](/pm/docs/cut-list.md) removes is not here; the frontier `pm`
remains the tool for those until cutover.

## Store registry

Cross-store routing reads a JSON registry at `~/.config/pm/stores.json`. Set
`PM_STORES_FILE` to read another file. `pm ticket stores --check` reports a bad
registry.

## Routes

| Document | Read when |
| --- | --- |
| [Cut list](/pm/docs/cut-list.md) | Deciding whether a verb, flag or config key belongs in this component |
| [Store format, spec v2](/pm/docs/spec/v2/SPEC.md) | Reading or writing `.pm/` files; the format is frozen |
| [Maintenance](/pm/AGENTS.md) | Changing code or tests here |
| [Setup](/pm/INSTALL.md) | Installing, verifying, disabling or removing |

Supported providers are recorded here once the instruction-delivery work lands.
