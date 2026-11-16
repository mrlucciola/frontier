# Kiro

Provider adapter for Kiro CLI 2.x (the "v2 harness") on locked-down work
machines: a version-gated `deploy.sh`, a copy-paste sync transport for
firewalled transfer, a recon probe (`cli/kiro-probe`), and the durable plan
for running the frontier-clean core components there. Code never runs kiro on
the dev machine; kiro behavior is verified at work by probe reports pasted
back and logged under `kiro/docs/probe-log/`.

Supported provider: Kiro CLI 2.x only. Kiro 3.x surfaces (markdown agents,
`permissions.yaml`, standalone hook JSON, PascalCase triggers) are forbidden
here, and `kiro/deploy.sh` refuses to run against a CLI that is not 2.x.

Before changing this component read the
[maintenance routes](/kiro/AGENTS.md); setup, removal, and the paste-only
work-machine procedure are in [INSTALL](/kiro/INSTALL.md).
