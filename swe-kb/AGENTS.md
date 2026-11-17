# swe-kb maintenance

This component owns a tabled software design knowledge base, kept as one
transport file. Nothing is extracted, deployed, or consumed by another component.

| Change | Read |
| --- | --- |
| Whether to keep, extract or adopt it | [README](/swe-kb/README.md), then the [assessment prompt](/swe-kb/swe-kb-portable-integration-assessment-prompt.md) |
| The knowledge base content | [Transport file](/swe-kb/swe-kb-portable.md); edit only after the assessment adopts it |

Do not extract the transport, add a deploy script, or reference this component
from another one until the assessment on the ticket store is ruled on. The
transport begins with a `docfmt: ignore` marker because its file sections are
extracted byte for byte; keep it.

Run the swe-kb checks from the repository root.

```sh
python3 -B docs/check_structure.py
```
