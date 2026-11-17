# swe-kb

**Tabled 2026-11-16.** A software design knowledge base, stored here as one
transport file and not extracted, deployed or used by any component. Whether it
should be is open on ticket fc-2e9c44.

## What is here

| File | What it is |
| --- | --- |
| [swe-kb-portable.md](/swe-kb/swe-kb-portable.md) | Single-file transport of the knowledge base: 204 concepts (architectural, design and Gang of Four patterns, implementation techniques, integration patterns, design principles), TSV catalog and aliases, generated indexes, a read-only lookup CLI, an index builder and tests. Its own text calls the content unverified seed data. |
| [Assessment prompt](/swe-kb/swe-kb-portable-integration-assessment-prompt.md) | Launchable prompt for the assessment on fc-2e9c44. |
| [AGENTS.md](/swe-kb/AGENTS.md) | What to do, and not do, while it is tabled. |

## Where it came from

It sat untracked inside `cwf/` and is not part of cwf. It was moved here on
2026-11-16 so that cwf holds only cwf files. Its path references were corrected
from `~/frontier/swe-kb` to this directory; nothing else in it was changed.

## If it is ever extracted

The extractor in the transport writes into `swe-kb/kb/`, one directory below the
transport file, which is the layout it expects. Read the transport's
"Installation" section first. Extraction is not authorized while the component is
tabled.

The extracted bundle conflicts with this repository's standards in known ways:

- It generates its own `AGENTS.md`.
- Its extractor refuses to overwrite a file whose bytes differ.
- Its tests run from the knowledge-base root, not the repository root.

The assessment decides how to resolve each.

## How other components may refer to it

Only by role, for example "a design-knowledge lookup, when available", and only
after the assessment adopts it. Today no component may depend on it.
