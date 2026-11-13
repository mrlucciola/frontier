# ICM maintenance

This directory owns workspace detection, ICM runtime instructions, and the two
workspace skills. Read the route for the behavior being changed.

| Change | Read |
| --- | --- |
| Workspace detection or startup context | [Detection hook](hooks/icm-detect.sh) and [hook tests](tests/test_hook.py) |
| Stage execution, status, or setup | [ICM run skill](skills/icm-run/SKILL.md), then its relevant command reference |
| Workspace construction or upstream templates | [Vendoring contract](skills/icm-architect/VENDOR.md) |
| Provider activation | [Settings fragment](config/settings.icm.fragment.json) and [runtime instruction](instructions/icm.md) |

Keep workspace execution and review rules in the runtime skill and instruction
sources. Follow the vendoring contract for changes under `skills/icm-architect/`.

Run the detection check from the repository root when its behavior changes.

```sh
python3 -B icm/tests/test_hook.py
```

The [installer test](tests/test_install.py) refers to a removed `install.py`.
[INSTALL.md](INSTALL.md) records that former workflow. Validate replacement setup
against its actual documented commands when working on activation.
