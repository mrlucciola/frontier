#!/usr/bin/python3
"""Run the wt characterization suite against one wt executable.

    /usr/bin/python3 -B wt/tests/run_wt.py --cli <wt> --pm old|new [-k NAME ...]
                                          [--allow-pending] [-v]

Sets WT_CLI_UNDER_TEST, WT_PM_SIDE and WT_UNBUILT_LOG, runs tests/test_wt_cli.py with
unittest, and prints these two last lines:

    cli under test: <path> (pm <side>)
    wt suite: passed N, pending P, skipped S, failed F

A test is pending when the wt under test answered a call with exit 70 after appending
a line to WT_UNBUILT_LOG (the pending rule); the suite helper raises Pending then.
Exit 0 only when failed is 0 and, without --allow-pending, pending is 0.
-k keeps tests whose id contains any NAME (a class name, a test name, a substring).
"""
import argparse
import importlib.util
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending = []
        self.passed = 0

    def addSuccess(self, test):
        self.passed += 1
        super().addSuccess(test)

    def addError(self, test, err):
        if err[0].__name__ == "Pending":
            self.pending.append((test, str(err[1])))
            if self.dots:
                self.stream.write("p")
            elif self.showAll:
                self.stream.writeln("pending")
            return
        super().addError(test, err)


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cli", required=True, help="the wt executable to test")
    parser.add_argument("--pm", required=True, choices=("old", "new"), dest="side")
    parser.add_argument("-k", dest="names", action="append", default=[])
    parser.add_argument("--allow-pending", action="store_true")
    parser.add_argument("-v", dest="verbose", action="store_true")
    args = parser.parse_args()

    cli = os.path.abspath(args.cli)
    if not os.path.isfile(cli):
        sys.exit("run_wt: no file at %s" % cli)
    handle, log = tempfile.mkstemp(prefix="wt-unbuilt-")
    os.close(handle)
    os.environ["WT_CLI_UNDER_TEST"] = cli
    os.environ["WT_PM_SIDE"] = args.side
    os.environ["WT_UNBUILT_LOG"] = log

    spec = importlib.util.spec_from_file_location(
        "test_wt_cli", os.path.join(HERE, "test_wt_cli.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["test_wt_cli"] = module
    spec.loader.exec_module(module)

    tests = [t for t in flatten(unittest.defaultTestLoader.loadTestsFromModule(module))
            if not args.names or any(k in t.id() for k in args.names)]
    if not tests:
        sys.exit("run_wt: no test matches")
    suite = unittest.TestSuite(tests)
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2 if args.verbose else 1,
                                     resultclass=Result)
    result = runner.run(suite)

    for test, reason in result.skipped:
        print("skipped: %s: %s" % (test.id(), reason))
    for test, step in result.pending:
        print("pending: %s: first unbuilt step `%s`" % (test.id(), step))
    failed = len(result.failures) + len(result.errors) + len(result.unexpectedSuccesses)
    pending = len(result.pending)
    print("cli under test: %s (pm %s)" % (cli, args.side))
    print("wt suite: passed %d, pending %d, skipped %d, failed %d"
          % (result.passed, pending, len(result.skipped), failed))
    sys.stdout.flush()
    os.unlink(log)
    return 0 if failed == 0 and (pending == 0 or args.allow_pending) else 1


if __name__ == "__main__":
    sys.exit(main())
