"""C2 integration checks: separate prose ownership and reversible skill-only use."""
import json
import subprocess

from test_cwf import Environment, ROOT
from cwf import installer
from cwf.common import DOMAINS, Fault, write_json


class PilotTests(Environment):
    def setUp(self):
        super().setUp()
        self.base_agents = self.home / '.config/opencode/AGENTS.md'
        self.base_agents.parent.mkdir(parents=True)
        self.base_agents.write_text('Original global rules\n')
        self.entry_file = self.base_agents.with_name('global-entry.md')
        self.entry = (ROOT / 'config/global-entry.md').read_bytes()
        self.entry_file.write_bytes(self.entry)
        self.personal = self.home / '.config/opencode/opencode.json'
        self.personal.write_text('{"model":"existing/model"}\n')

    def install(self):
        plan = installer.plan(self.home, ROOT, guidance=False)
        self.assertFalse(plan['guidance'])
        self.assertEqual(len(plan['changes']), 9)
        self.assertFalse(any(c['kind'] == 'guidance' for c in plan['changes']))
        installer.apply(plan, self.home)
        return plan

    def test_skill_only_cycle_preserves_independent_prose_and_personal_config(self):
        self.install()
        self.base_agents.write_text('Simulated newer base deployment\n')
        preserved = {p: installer.snapshot(p) for p in (self.base_agents, self.entry_file, self.personal)}
        for enabled in (False, True, False):
            installer.toggle(self.home, None, enabled)
            for domain in DOMAINS:
                self.assertEqual((self.home / '.agents/skills' / ('cwf-' + domain)).is_symlink(), enabled)
            self.assertEqual({p: installer.snapshot(p) for p in preserved}, preserved)
        # disable alone must not be mistaken for full pilot rollback.
        self.assertEqual(self.entry_file.read_bytes(), self.entry)
        installer.revert(self.home)
        self.assertEqual({p: installer.snapshot(p) for p in preserved}, preserved)
        self.assertFalse((self.home / '.local/bin/cwf').exists())
        self.assertTrue((self.home / '.local/share/cwf/releases/0.1.0').is_dir())

    def test_rollback_does_not_remove_separately_owned_entry(self):
        self.install()
        installer.revert(self.home, rollback=True)
        self.assertEqual(self.entry_file.read_bytes(), self.entry)
        self.assertEqual(self.base_agents.read_text(), 'Original global rules\n')
        self.assertFalse((self.home / '.agents/skills/cwf-build').exists())

    def test_hand_edited_owned_target_does_not_block_uninstall(self):
        self.install()
        launcher = self.home / '.local/bin/cwf'
        launcher.write_text('Later hand edit\n')
        installer.revert(self.home)
        self.assertFalse(launcher.exists())
        self.assertFalse((self.home / '.agents/skills/cwf-build').exists())
        self.assertEqual(self.entry_file.read_bytes(), self.entry)
        self.assertEqual(self.base_agents.read_text(), 'Original global rules\n')

    def test_interrupted_skill_only_install_recovers_without_prose_write(self):
        plan = installer.plan(self.home, ROOT, guidance=False)
        p = installer.paths(self.home)
        tx = {'id': 'c2-interrupted', 'status': 'applying', 'plan': plan, 'previous_receipt': None}
        write_json(p['state'] / 'transactions/c2-interrupted.json', tx)
        installer.restore(plan['changes'][1]['path'], plan['changes'][1]['after'])
        with self.assertRaises(Fault):
            installer.plan(self.home, ROOT, guidance=False)
        self.assertEqual(installer.recover(self.home)['recovered'], ['c2-interrupted'])
        self.assertEqual(self.entry_file.read_bytes(), self.entry)
        self.assertEqual(self.base_agents.read_text(), 'Original global rules\n')
        self.assertFalse(p['launcher'].exists())

    def test_installed_tool_works_without_git_pm_or_workspace_initialization(self):
        self.install()
        self.put('source.txt', 'widget behavior\n')
        launcher = self.home / '.local/bin/cwf'
        result = subprocess.run([str(launcher), '--ephemeral', 'discover', '--input', '-'],
                                input=json.dumps(self.request(files=['source.txt'])),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('widget behavior', result.stdout)
        self.assertEqual([p.name for p in self.repo.iterdir()], ['source.txt'])
        self.assertFalse((self.home / '.local/state/cwf/state.sqlite3').exists())
