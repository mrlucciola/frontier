# vendor/omlx

Unknown. Before deploying here, confirm:

1. Which file omlx auto-loads as the entry instruction (AGENTS.md? a config key?).
   `general/instructions/icm.md` goes wherever that is.
2. Whether it discovers Agent Skills folders (SKILL.md) and from which path.
   If it does not, the icm-run skill content can be folded into the instruction for
   this vendor only, accepting the token cost, or omitted (the instruction alone keeps
   the gate and load discipline; it loses `status`/`setup` mechanics).
3. Whether it has hooks. Probably not; nothing depends on them.

Until confirmed, deploy the instruction only.
