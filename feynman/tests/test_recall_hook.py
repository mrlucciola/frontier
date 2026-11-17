"""Run tools/concept-graph/recall.sh against a temporary store.

Component-level test: it exercises the hook AND the component's hook fragment,
so it lives in feynman/tests/, not beside the tool (tool-only tests stay in
tools/concept-graph/tests/). Checks: silent exit 0 with no store, silent on a prompt
with no lexicon token and python is NOT started, a valid JSON envelope on a hit
(CONFIRM: the kiro v3 hook stdout contract), and the fragment registers the script.
Run: python3 feynman/tests/test_recall_hook.py
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

COMPONENT = pathlib.Path(__file__).resolve().parent.parent
TOOL = COMPONENT / "tools/concept-graph"
HOOK = TOOL / "recall.sh"
CG = TOOL / "cg.py"
FRAGMENT = COMPONENT / "config/kiro/hooks.json"
FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


def hook(store, payload, marker):
    env = dict(os.environ, CONCEPT_GRAPH_ROOT=str(store), CONCEPT_GRAPH_CG=str(CG),
               CONCEPT_GRAPH_PYTHON=str(marker))
    return subprocess.run(["bash", str(HOOK)], input=json.dumps(payload), capture_output=True,
                          text=True, env=env, cwd=str(store.parent))


def main():
    frag = json.loads(FRAGMENT.read_text())
    cmds = [h["command"] for grp in frag["hooks"].get("UserPromptSubmit", []) for h in grp["hooks"]]
    check(any("concept-graph/recall.sh" in c for c in cmds), "fragment registers recall.sh: %r" % cmds)
    check(".kiro/tools/concept-graph/recall.sh" in " ".join(cmds), "fragment names the kiro install path: %r" % cmds)
    check("permissions" not in frag, "permissions live in permissions.yaml, not here")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        store = tmp / "concepts"
        # a python wrapper that records it was started, then runs the real interpreter
        marker = tmp / "py.sh"
        touched = tmp / "started"
        marker.write_text('#!/usr/bin/env bash\ntouch "%s"\nexec "%s" "$@"\n' % (touched, sys.executable))
        marker.chmod(0o755)

        r = hook(store, {"session_id": "a", "cwd": str(tmp), "prompt": "hello"}, marker)
        check(r.returncode == 0 and r.stdout == "", "no store: silent exit 0 (%r)" % r.stdout)

        env = dict(os.environ, CONCEPT_GRAPH_ROOT=str(store))
        subprocess.run([sys.executable, str(CG), "add", "wal-mode", "--title", "SQLite WAL mode",
                        "--alias", "wal", "--explain", "e", "--analogy", "a", "--breaks", "b",
                        "--pitch", "p"], check=True, env=env, capture_output=True)

        r = hook(store, {"session_id": "a", "cwd": str(tmp), "prompt": "tell me a joke"}, marker)
        check(r.returncode == 0 and r.stdout == "", "miss: silent (%r)" % r.stdout)
        check(not touched.exists(), "miss: python never started")

        r = hook(store, {"session_id": "a", "cwd": str(tmp), "prompt": "How does WAL work?"}, marker)
        check(r.returncode == 0, "hit: exit 0")
        check(touched.exists(), "hit: python started")
        try:
            doc = json.loads(r.stdout)
            ctx = doc["hookSpecificOutput"]["additionalContext"]
            check(doc["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit", "event name")
            check(ctx.startswith("memory: 1 concept"), "block header: %r" % ctx[:50])
            check("SQLite WAL mode" in ctx, "card title in block")
        except (ValueError, KeyError) as ex:
            check(False, "hit: invalid output %r (%s)" % (r.stdout[:200], ex))

        r = hook(store, {"session_id": "a", "cwd": str(tmp), "prompt": "How does WAL work?"}, marker)
        check(r.stdout == "", "second hit in the same session is deduped (%r)" % r.stdout[:60])

        r = subprocess.run(["bash", str(HOOK)], input="", capture_output=True, text=True,
                           env=dict(os.environ, CONCEPT_GRAPH_ROOT=str(store), CONCEPT_GRAPH_CG=str(CG)))
        check(r.returncode == 0 and r.stdout == "", "empty stdin: silent")

    if FAILS:
        print("\n".join("FAIL " + f for f in FAILS))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
