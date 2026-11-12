#!/usr/bin/env python3
"""Opt-in installed-client probe. No model turns, live install, or auth reads."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from cwf import installer
from cwf.common import DOMAINS

DISABLED = ('design-pattern-language', 'architecture-review', 'implementation-planning',
            'dependency-decision', 'validation-gate', 'failure-retro', 'docs-sync',
            'repo-onboarding', 'session-continuity')


def toml_rows(rows):
    # The synthetic entries below contain only string selectors and booleans.
    return '[' + ','.join('{' + ','.join(k + '=' + (
        str(v).lower() if isinstance(v, bool) else json.dumps(v))
        for k, v in row.items()) + '}' for row in rows) + ']'


def inspect_client(codex_home, cwd, extra_rows=None, *, start_thread=True):
    env = dict(os.environ, CODEX_HOME=str(codex_home))  # HOME is untouched.
    argv = ['codex']
    if extra_rows is not None:
        argv += ['-c', 'skills.config=' + toml_rows(extra_rows)]
    argv += ['app-server']
    events = queue.Queue()
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, bufsize=1)

    def reader():
        for line in process.stdout:
            try:
                events.put(json.loads(line))
            except json.JSONDecodeError:
                events.put({'probe_error': 'non-JSON protocol output'})
        events.put({'probe_error': 'app-server closed stdout'})

    worker = threading.Thread(target=reader, daemon=True)
    worker.start()

    def rpc(i, method, params):
        process.stdin.write(json.dumps({'id': i, 'method': method, 'params': params}) + '\n')
        process.stdin.flush()
        deadline = time.monotonic() + 20
        while True:
            item = events.get(timeout=max(0, deadline - time.monotonic()))
            if 'probe_error' in item:
                raise RuntimeError(item['probe_error'])
            if item.get('id') == i:
                if 'error' in item:
                    raise RuntimeError(method + ': ' + json.dumps(item['error']))
                return item['result']

    try:
        rpc(0, 'initialize', {'clientInfo': {'name': 'cwf_c2_probe', 'version': '1'}})
        process.stdin.write('{"method":"initialized","params":{}}\n')
        process.stdin.flush()
        config = rpc(1, 'config/read', {'cwd': str(cwd), 'includeLayers': True})
        groups = rpc(2, 'skills/list', {'cwds': [str(cwd)], 'forceReload': True})['data']
        assert len(groups) == 1 and not groups[0]['errors'], 'skill discovery errors'
        sources = rpc(3, 'thread/start', {'cwd': str(cwd), 'ephemeral': True})['instructionSources'] if start_thread else []
        return (config['config'].get('skills') or {}).get('config', []), groups[0]['skills'], sources
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        worker.join(timeout=5)
        process.stdout.close()


def selected(sources, expected, forbidden):
    paths = {str(Path(p).resolve()) for p in sources}
    assert str(expected.resolve()) in paths, ('expected instruction source absent', sources)
    assert str(forbidden.resolve()) not in paths, ('competing source loaded', sources)


def catalog(skills):
    return {(s['name'], s['path']): s['enabled'] for s in skills}


def main(catalog_only=False):
    version = subprocess.check_output(['codex', '--version'], text=True).strip()
    with tempfile.TemporaryDirectory(prefix='cwf-client-') as tmp:
        base = Path(tmp).resolve()
        home, config_root, workspace = (base / p for p in ('home', 'codex', 'workspace'))
        for p in (home, config_root, workspace):
            p.mkdir()
        agents = config_root / 'AGENTS.md'
        agents.write_text('Synthetic baseline guidance.\n')
        override = config_root / 'AGENTS.override.md'
        skill_root = workspace / '.agents/skills'
        skill_root.mkdir(parents=True)
        # Two exact-name copies prove that a name exclusion covers every copy.
        for directory, name in [('copy-a', DISABLED[0]), ('copy-b', DISABLED[0]),
                                ('untouched', 'c2-untouched')]:
            p = skill_root / directory
            p.mkdir()
            (p / 'SKILL.md').write_text('---\nname: ' + name + '\ndescription: Synthetic C2 fixture only.\n---\nFixture.\n')
        existing = [{'name': 'c2-untouched', 'enabled': False}, {'name': 'c2-no-match', 'enabled': True}]
        config = config_root / 'config.toml'
        config.write_text('skills.config=' + toml_rows(existing) + '\n')
        config_bytes = config.read_bytes()
        rows, skills, sources = inspect_client(config_root, workspace, start_thread=not catalog_only)
        assert rows == existing, ('baseline effective settings differ', rows)
        if not catalog_only:
            selected(sources, agents, override)
        before = catalog(skills)
        copies = [s for s in skills if s['name'] == DISABLED[0]]
        assert len(copies) >= 2 and all(s['enabled'] for s in copies), 'duplicate-name fixture not discovered'
        assert not any(s['enabled'] for s in skills if s['name'] == 'c2-untouched')
        print(json.dumps({'phase': 'baseline', 'skills': len(skills), 'duplicate_copies': len(copies), 'sources': sources}), flush=True)

        plan = installer.plan(home, ROOT, config_root, guidance=False)
        installer.apply(plan, home, config_root)
        override.write_bytes((ROOT / 'config/AGENTS.override.md').read_bytes())
        # The client's real user home remains untouched. Expose disposable installed
        # links through this disposable project's supported skill discovery root.
        for d in DOMAINS:
            (skill_root / ('cwf-' + d)).symlink_to(home / '.agents/skills' / ('cwf-' + d))
        combined = existing + [{'name': n, 'enabled': False} for n in DISABLED]
        for phase in ('pilot', 'base-replaced'):
            if phase == 'base-replaced':
                agents.write_text('Simulated independent deployment changed the base.\n')
            rows, skills, sources = inspect_client(config_root, workspace, combined, start_thread=not catalog_only)
            assert rows == combined, 'existing skill entries/order changed'
            if not catalog_only:
                selected(sources, override, agents)
            assert override.read_bytes() == (ROOT / 'config/AGENTS.override.md').read_bytes()
            for s in skills:
                if s['name'] in DISABLED:
                    assert not s['enabled'], ('legacy copy enabled', s['name'], s['path'])
                elif (s['name'], s['path']) in before:
                    assert s['enabled'] == before[s['name'], s['path']], ('unrelated skill changed', s['name'])
            enabled = {s['name'] for s in skills if s['enabled']}
            assert {'cwf-' + d for d in DOMAINS} <= enabled, 'six installed skills not discovered'
            print(json.dumps({'phase': phase, 'sources': sources,
                              'disabled_copies': sum(s['name'] in DISABLED for s in skills),
                              'cwf_enabled': sorted(n for n in enabled if n.startswith('cwf-'))}), flush=True)

        fallback = agents.read_bytes()
        entry_hash = hashlib.sha256(override.read_bytes()).hexdigest()
        installer.toggle(home, config_root, False)
        assert hashlib.sha256(override.read_bytes()).hexdigest() == entry_hash
        # Disposable project links are test exposure, not live installer targets.
        for d in DOMAINS:
            (skill_root / ('cwf-' + d)).unlink()
        assert agents.read_bytes() == fallback
        override.unlink()
        rows, skills, sources = inspect_client(config_root, workspace, start_thread=not catalog_only)
        if not catalog_only:
            selected(sources, agents, override)
        assert rows == existing and catalog(skills) == before, 'fresh catalog rollback mismatch'
        installer.revert(home, config_root)
        assert config.read_bytes() == config_bytes and agents.read_bytes() == fallback
        print(json.dumps({'phase': 'rollback', 'sources': sources,
                          'catalog_restored': True, 'settings_preserved': True,
                          'instruction_selection': 'NOT_TESTED' if catalog_only else 'passed',
                          'client': version, 'model_turns': 0, 'semantic_activation': 'NOT_TESTED'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog-only', action='store_true',
                        help='Skip thread/start; cannot qualify instruction selection.')
    args = parser.parse_args()
    try:
        main(args.catalog_only)
    except (AssertionError, OSError, RuntimeError, queue.Empty) as exc:
        print(json.dumps({'status': 'unproved', 'error': str(exc), 'model_turns': 0}), flush=True)
        sys.exit(1)
