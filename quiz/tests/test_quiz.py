"""Quiz tests use isolated temporary homes; no user data or network.
Adapted from the learn-skills 0.2.0 drop; the kg.py cross-checks became direct
assertions on the identity contract (concept keys are valid feynman card slugs).
Run: python3 quiz/tests/test_quiz.py
"""
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
QUIZ_PATH = COMPONENT / 'skills/adaptive-quiz/scripts/quiz.py'
CATALOG = COMPONENT / 'skills/adaptive-quiz/catalog.json'
spec = importlib.util.spec_from_file_location('quiz', QUIZ_PATH)
quiz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quiz)

# cg.py's slugify maps any text into [a-z0-9-]; a catalog key already in that
# alphabet IS its own card slug, which is the whole identity contract.
CARD_SLUG = re.compile(r'[a-z0-9][a-z0-9-]*\Z')


class QuizTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.home = self.base / 'knowledge'
        self.q = quiz.Quiz(self.home, CATALOG)

    def tearDown(self):
        self.temp.cleanup()

    def key(self, session):
        with sqlite3.connect(self.home / quiz.DB_NAME) as db:
            return json.loads(db.execute('SELECT items FROM sessions WHERE id=?', (session,)).fetchone()[0])

    def run_all(self, **start):
        session = self.q.start(**start)['session']
        return session, [self.q.answer(session, q['id'], q['answer']) for q in self.key(session)]

    def test_catalog_keys_are_feynman_card_slugs(self):
        data = quiz.load_catalog(CATALOG)
        self.assertEqual(len(data['questions']), 24)
        for c in data['concepts']:
            self.assertTrue(CARD_SLUG.fullmatch(c['key']), c['key'])

    def test_profile_names_the_feynman_card(self):
        card = next(c['feynman_card'] for c in self.q.profile()['concepts'] if c['key'] == 'idempotency')
        self.assertEqual(card, 'idempotency')

    def test_doctor_without_database_creates_nothing(self):
        self.assertFalse(self.q.doctor()['database_exists'])
        self.assertEqual(self.q.profile()['concepts'][0]['distinct_items'], 0)
        self.assertFalse(self.home.exists())

    def test_start_has_no_keys_and_distinct_concepts(self):
        result = self.q.start(5)
        self.assertEqual(len(result['questions']), 5)
        self.assertEqual(len({q['concept'] for q in result['questions']}), 5)
        for q in result['questions']:
            self.assertNotIn('answer', q)
            self.assertNotIn('explanation', q)
        self.assertEqual(oct(self.home.stat().st_mode & 0o777), '0o700')
        self.assertEqual(oct((self.home / quiz.DB_NAME).stat().st_mode & 0o777), '0o600')

    def test_grade_replay_and_conflict(self):
        session = self.q.start(1)['session']
        item = self.key(session)[0]
        first = self.q.answer(session, item['id'], item['answer'])
        self.assertTrue(first['correct'])
        self.assertEqual(first, self.q.answer(session, item['id'], item['answer']))
        wrong = next(x for x in 'ABCD' if x != item['answer'])
        with self.assertRaisesRegex(quiz.Error, 'already recorded'):
            self.q.answer(session, item['id'], wrong)
        self.assertEqual(self.q.doctor()['counts']['answers'], 1)
        with self.assertRaises(quiz.Error):
            self.q.answer('nope', item['id'], 'A')

    def test_assisted_excluded_and_repeats_do_not_inflate(self):
        session = self.q.start(1, domain='rust')['session']
        item = self.key(session)[0]
        self.q.answer(session, item['id'], item['answer'], assisted=True)
        concept = next(c for c in self.q.profile()['concepts'] if c['key'] == item['concept'])
        self.assertEqual(concept['distinct_items'], 0)
        for _ in range(2):
            self.run_all(count=20, domain='rust')
        total = sum(c['distinct_items'] for c in self.q.profile()['concepts'])
        self.assertEqual(total, 6)

    def test_weak_items_return_and_unseen_preferred(self):
        session = self.q.start(2, concepts=['idempotency'])['session']
        items = self.key(session)
        wrong = next(x for x in 'ABCD' if x != items[0]['answer'])
        self.q.answer(session, items[0]['id'], wrong)
        again = self.q.start(2, concepts=['idempotency'])['questions']
        reasons = {q['id']: q['selection_reason'] for q in again}
        self.assertEqual(reasons[items[0]['id']], 'weak')
        self.assertEqual(reasons[items[1]['id']], 'unseen')

    def test_concept_and_domain_filters(self):
        result = self.q.start(5, concepts=['backpressure', 'ts-unknown'])
        self.assertEqual({q['concept'] for q in result['questions']}, {'backpressure', 'ts-unknown'})
        with self.assertRaisesRegex(quiz.Error, 'unknown concepts'):
            self.q.start(1, concepts=['nope'])
        with self.assertRaisesRegex(quiz.Error, 'domains'):
            self.q.start(1, domain='cobol')

    def test_scopes_are_separate_and_forgettable(self):
        self.run_all(count=1, scope='repo:a')
        self.run_all(count=1)
        self.assertEqual(sum(c['distinct_items'] for c in self.q.profile('repo:a')['concepts']), 1)
        self.assertEqual(sum(c['distinct_items'] for c in self.q.profile('global')['concepts']), 1)
        self.q.forget_scope('repo:a')
        self.assertEqual(sum(c['distinct_items'] for c in self.q.profile('repo:a')['concepts']), 0)
        export = self.q.export()
        self.assertEqual((len(export['sessions']), len(export['answers'])), (1, 1))

    def test_scope_here_is_stable_per_repo(self):
        repo = self.base / 'repo'
        repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        scope = quiz.resolve_scope('here', repo)
        self.assertTrue(scope.startswith('repo:'), scope)
        self.assertEqual(scope, quiz.resolve_scope('here', repo))
        nested = repo / 'sub'
        nested.mkdir()
        self.assertEqual(scope, quiz.resolve_scope('here', nested))
        self.assertTrue(quiz.resolve_scope('here', self.base).startswith('dir:'))
        with self.assertRaises(quiz.Error):
            quiz.resolve_scope('../etc', repo)

    def test_snapshot_survives_catalog_edits(self):
        session = self.q.start(1)['session']
        item = self.key(session)[0]
        self.q.questions[item['id']]['answer'] = 'X'
        self.assertTrue(self.q.answer(session, item['id'], item['answer'])['correct'])

    def test_unknown_schema_is_not_modified(self):
        self.q.start(1)
        with sqlite3.connect(self.home / quiz.DB_NAME) as db:
            db.execute('PRAGMA user_version=99')
        with self.assertRaisesRegex(quiz.Error, 'unsupported'):
            self.q.profile()
        with sqlite3.connect(self.home / quiz.DB_NAME) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 99)

    def test_cli_and_parallel_starts(self):
        env = dict(os.environ, KNOWLEDGE_HOME=str(self.home))

        def run(i):
            return subprocess.run([sys.executable, str(QUIZ_PATH), 'start', '--count', '1'],
                                  capture_output=True, text=True, env=env)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(run, range(8)))
        self.assertTrue(all(r.returncode == 0 for r in results), '\n'.join(r.stderr for r in results))
        doctor = subprocess.run([sys.executable, str(QUIZ_PATH), 'doctor'], capture_output=True, text=True, env=env)
        self.assertEqual(json.loads(doctor.stdout)['counts']['sessions'], 8)
        self.assertEqual(json.loads(doctor.stdout)['integrity'], 'ok')

    def test_default_data_dir_is_kiro_knowledge(self):
        old = os.environ.pop('KNOWLEDGE_HOME', None)
        try:
            self.assertEqual(quiz.data_dir(), (Path.home() / '.kiro' / 'knowledge').resolve())
        finally:
            if old is not None:
                os.environ['KNOWLEDGE_HOME'] = old


if __name__ == '__main__':
    result = unittest.main(exit=False).result
    sys.exit(0 if result.wasSuccessful() else 1)
