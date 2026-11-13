#!/usr/bin/python3
"""Run the CLI parity suite against one implementation of the ticket CLI.

    /usr/bin/python3 -B pm/tests/run_parity.py --cli <path to ticket CLI> [-k NAME ...] [--allow-pending]

The CLI under test takes verbs directly (`<cli> create "title"`), as
`pm ticket <verb>` does after the dispatcher. `-k` narrows the run to a class
name, a test name, or a substring of either.

While the rewrite is in progress some verbs are not built. The CLI reports each
call to one by appending the verb's name to the file named in $PM_UNBUILT_LOG
(and exiting 70). A test that fails after touching an unbuilt verb counts as
"pending", not "failed". The run exits 0 only when nothing failed and, unless
--allow-pending is given, nothing is pending.
"""
import argparse
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


class ParityResult(unittest.TextTestResult):
    """A TextTestResult that files unbuilt-verb failures under `pending`."""

    unbuilt_log = None  # set by main() before the run

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending = []  # (test id, sorted verb names)

    def startTest(self, test):
        open(self.unbuilt_log, "w").close()
        super().startTest(test)

    def _unbuilt_verbs(self):
        with open(self.unbuilt_log) as f:
            return sorted(set(f.read().split()))

    def _record_pending(self, test, verbs):
        if any(test.id() == seen for seen, _ in self.pending):
            return  # a second failing subTest of a test already counted
        self.pending.append((test.id(), verbs))
        if self.showAll:
            self.stream.writeln("pending (%s)" % ", ".join(verbs))
        elif self.dots:
            self.stream.write("p")
        self.stream.flush()

    def addFailure(self, test, err):
        verbs = self._unbuilt_verbs()
        if verbs:
            self._record_pending(test, verbs)
        else:
            super().addFailure(test, err)

    def addError(self, test, err):
        verbs = self._unbuilt_verbs()
        if verbs:
            self._record_pending(test, verbs)
        else:
            super().addError(test, err)

    def addSubTest(self, test, subtest, err):
        verbs = self._unbuilt_verbs() if err is not None else []
        if verbs:
            self._record_pending(test, verbs)
        else:
            super().addSubTest(test, subtest, err)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cli", required=True, help="path to the ticket CLI to test")
    parser.add_argument("-k", dest="patterns", action="append", default=[],
                        help="only run tests whose name contains this")
    parser.add_argument("--allow-pending", action="store_true",
                        help="exit 0 even when tests are pending on unbuilt verbs")
    parser.add_argument("-v", dest="verbose", action="store_true")
    args = parser.parse_args()

    cli = os.path.abspath(args.cli)
    if not os.path.isfile(cli):
        sys.exit("run_parity: no file at %s" % cli)
    # test_cli_parity.py reads this at import time.
    os.environ["PM_CLI_UNDER_TEST"] = cli

    log = tempfile.NamedTemporaryFile(prefix="pm-unbuilt-", suffix=".log", delete=False)
    log.close()
    os.environ["PM_UNBUILT_LOG"] = log.name
    ParityResult.unbuilt_log = log.name

    loader = unittest.TestLoader()
    if args.patterns:
        loader.testNamePatterns = ["*%s*" % p for p in args.patterns]
    suite = loader.discover(HERE, pattern="test_cli_parity.py", top_level_dir=HERE)
    runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1,
                                     resultclass=ParityResult)
    result = runner.run(suite)
    os.remove(log.name)

    failed = len(result.failures) + len(result.errors)
    pending = len(result.pending)
    passed = result.testsRun - failed - pending - len(result.skipped)
    for test_id, verbs in result.pending:
        print("pending: %s (%s)" % (test_id, ", ".join(verbs)))
    waiting_on = sorted({verb for _, verbs in result.pending for verb in verbs})
    print("cli under test: %s" % cli)
    print("parity: passed %d, pending %d, failed %d, skipped %d"
          % (passed, pending, failed, len(result.skipped)))
    if waiting_on:
        print("unbuilt verbs still needed: %s" % ", ".join(waiting_on))

    if failed:
        return 1
    if pending and not args.allow_pending:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
