# Platform assumptions: Kiro v3 surfaces

Official Kiro documentation describes the v3 era, and this branch targets it:
agents run only through `kiro-cli --v3`, per the
[branch policy](/docs/kiro-branch.md). No official documentation URL is cited
here; none has been verified from this checkout (CONFIRM during recon).

CWF uses these Kiro v3 surfaces, taken from the branch surface map. Each is
CONFIRM pending work-machine recon:

- Skills: `~/.kiro/skills/<name>` symlinks to the six `cwf-*` directories in
  the checkout. Whether symlinked skill directories are followed is
  unobserved; a fresh session is the only check.
- Global instructions: one marked block in `~/.kiro/steering/frontier.md`,
  one per component; every byte outside the markers is kept. How steering
  files combine with project instructions is unobserved.
- Skill loading: the session loads a skill through the `skill` tool by name;
  user mention syntax for skills is unobserved.

`deploy.sh` touches only these paths and writes no other file under
`~/.kiro/`; `permissions.yaml` is reviewed by hand and never written by a
deploy script. CWF does not depend on plugins, lifecycle hooks or special
APIs. Model selection of a skill remains probabilistic; a short steering
block is guidance, not enforcement. Live visibility is never inferred from
file existence. Recon observations replace these CONFIRM markers; do not
invent v3 behavior.
