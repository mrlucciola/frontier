"""Concurrent writers on one store, through the real CLI."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(os.path.dirname(HERE), "cli", "pm")
WORDS = ["amber", "basalt", "cobalt", "dune", "ember", "fjord", "garnet", "harbor",
         "iris", "jasper", "krill", "lagoon", "marble", "nectar", "onyx", "prism",
         "quartz", "ridge", "sorrel", "tundra"]


class Concurrency(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="pm-c-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for name in ("work", "home", "plugins"):
            os.mkdir(os.path.join(self.tmp, name))
        self.work = os.path.join(self.tmp, "work")
        self.env = {
            "PM_NOW": "2026-01-01T00:00:00Z", "PM_ACTOR": "ada", "LC_ALL": "C",
            "HOME": os.path.join(self.tmp, "home"), "PATH": "/usr/bin:/bin",
            "PM_STORES": os.path.join(self.tmp, "stores"),
            "PM_PLUGINS": os.path.join(self.tmp, "plugins"), "TMPDIR": self.tmp,
            "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
        }
        self.assertEqual(self.finish([self.spawn("init", "t", session="s0")])[0][0], 0)

    def spawn(self, *args, session):
        env = dict(self.env, PM_SESSION_ID=session)
        return subprocess.Popen(["/usr/bin/python3", "-B", CLI] + list(args),
                                cwd=self.work, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)

    def finish(self, procs):
        results = []
        for proc in procs:
            out, err = proc.communicate(timeout=120)
            results.append((proc.returncode, out, err))
        return results

    def test_twenty_new_at_once(self):
        procs = [self.spawn("new", "%s %s %s" % (w, w[::-1], w.upper()), "--new",
                            session="s%d" % i) for i, w in enumerate(WORDS)]
        results = self.finish(procs)
        for code, out, err in results:
            self.assertEqual(code, 0, err)
        ids = [out.strip() for _, out, _ in results]
        self.assertEqual(len(set(ids)), 20, "ids: %s" % sorted(ids))

        with open(os.path.join(self.work, ".pm", "log.jsonl")) as f:
            lines = f.read().split("\n")
        self.assertEqual(lines[-1], "")
        events = []
        for line in lines[:-1]:
            event = json.loads(line)
            for key in ("ts", "by", "op", "id"):
                self.assertIn(key, event, line)
            events.append(event)
        news = [e for e in events if e["op"] == "new"]
        self.assertEqual(len(news), 20)
        self.assertEqual(sorted(e["id"] for e in news), sorted(ids))

    def test_two_takes_one_winner(self):
        made = self.finish([self.spawn("new", "contested ticket", session="s0")])
        self.assertEqual(made[0][0], 0, made[0][2])
        procs = [self.spawn("take", "t-1", session="s1"),
                 self.spawn("take", "t-1", "--as", "bob", session="s2")]
        codes = sorted(code for code, _, _ in self.finish(procs))
        self.assertEqual(codes, [0, 1], "exit codes %s" % codes)


if __name__ == "__main__":
    unittest.main()
