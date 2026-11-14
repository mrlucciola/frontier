"""pm ticket close: close ticket(s), or park them done-unmerged."""
import os
import subprocess
import sys

import gitcommit
import store as st
from store import TicketError, make_note, now

NO_FINDINGS_TEXT = ("no --findings: this close attests nothing about what was not done, not "
                    "proven, or found elsewhere; pass --findings none or the ids")
# Exit 4 lets `wt finish` tell "merged, deploy pending" from a real close failure.
EXIT_DEPLOY_PENDING = 4
DEPLOY_CHECK_LABEL = "tooling"
DEPLOY_CHECK_TIMEOUT = 300


def register(subparsers):
    sp = subparsers.add_parser("close", help="close ticket(s) (--unmerged: work done, "
                                             "merge gated)")
    sp.add_argument("id", nargs="+")
    sp.add_argument("--unmerged", action="store_true")
    sp.add_argument("--note", help="handoff note, e.g. worktree/branch location")
    sp.add_argument("--reason", help="alias for --note")
    sp.add_argument("--session", help="session id for closed_by attribution "
                    "(default: $PM_SESSION_ID, then $CLAUDE_CODE_SESSION_ID)")
    sp.add_argument("--findings", metavar="none|ID[,ID...]",
                    help="attest findings were routed: none, or ticket ids (this "
                         "store or another registered store, bare or <prefix>/<id>; "
                         "stored bare); stored as the `findings` list (absent = not attested)")
    sp.add_argument("--via", choices=("wt",),
                    help="wt's own close (wt park, wt finish's remove-failure path); an "
                         "agent's direct close is refused while .worktrees/<id> exists")
    sp.add_argument("--no-deploy-check", dest="no_deploy_check", metavar="REASON",
                    help="close a tooling ticket even though the repo's bin/deploy "
                         "close-check reports its packages not deployed current; the "
                         "reason is recorded as a note")
    group = sp.add_mutually_exclusive_group()
    group.add_argument("--detach", action="store_true",
                       help="on an epic with open children, reparent them to (none) "
                            "and close")
    group.add_argument("--force", action="store_true",
                       help="on an epic with open children, close anyway and leave "
                            "them parented")


def refuse_if_worktree(store, tid, via):
    """An agent's direct close while the ticket's worktree exists in the store's
    repo; `--via wt` is wt's own close."""
    if via == "wt":
        return
    path = os.path.join(os.path.dirname(os.path.abspath(store.root)), ".worktrees", tid)
    if os.path.isdir(path):
        raise TicketError(f"{tid} has a worktree at {path}; run `wt finish {tid}` to "
                          f"merge and close, or `wt park {tid} --waits-on <blocker>` "
                          "to park it")


def ticket_paths(repo, tid):
    """Repo-relative paths touched by commits whose subject starts `<tid>:`."""
    r = gitcommit.git(repo, "log", "--format=", "--name-only", f"--grep=^{tid}:",
                      timeout=60)
    if r.returncode != 0:
        return None
    return sorted({ln.strip() for ln in r.stdout.splitlines() if ln.strip()})


def deploy_check(args):
    """Before a close (not --unmerged) of a ticket labelled tooling, when the
    store's repo has an executable bin/deploy, ask `bin/deploy close-check` whether
    the packages owning the files of the ticket's `<id>:` commits are deployed
    current (exit 0 = current). Exits EXIT_DEPLOY_PENDING unless --no-deploy-check.
    Runs outside the store lock."""
    if args.unmerged:
        return
    store = st.open_store(args.repo)
    repo = os.path.dirname(os.path.abspath(store.root))
    tool = os.path.join(repo, "bin", "deploy")
    if not (os.path.isfile(tool) and os.access(tool, os.X_OK)):
        return
    reason = args.no_deploy_check
    if reason is not None and not reason.strip():
        raise TicketError("--no-deploy-check needs a non-empty reason")
    pending = []
    for tid in st.each_id(args):
        t = store.by_id.get(tid)
        if t is None or DEPLOY_CHECK_LABEL not in (t.get("labels") or []):
            continue
        paths = ticket_paths(repo, tid)
        if paths is None:
            pending.append((tid, f"git log for {tid}'s commits failed"))
            continue
        if not paths:
            continue
        try:
            r = subprocess.run([tool, "close-check", *paths], cwd=repo,
                               capture_output=True, text=True,
                               timeout=DEPLOY_CHECK_TIMEOUT)
            out, rc = (r.stdout + r.stderr).strip(), r.returncode
        except (OSError, subprocess.TimeoutExpired) as e:
            out, rc = f"{tool} close-check could not run: {e}", -1
        if rc != 0:
            pending.append((tid, out))
    if not pending or reason is not None:
        return
    for tid, out in pending:
        print(f"pm: {tid} is labelled {DEPLOY_CHECK_LABEL}; {repo}/bin/deploy "
              f"close-check says its deployed copy is not current:", file=sys.stderr)
        for line in out.splitlines():
            print(f"  {line}", file=sys.stderr)
    print("pm: nothing closed. Deploy (and verify) the packages above, then close "
          "again; or close anyway with --no-deploy-check '<reason>'", file=sys.stderr)
    sys.exit(EXIT_DEPLOY_PENDING)


def run(args):
    deploy_check(args)
    with st.locked_verb(args, "close") as store:
        ids = st.each_id(args)
        findings = None
        if args.findings is not None:
            findings = st.parse_findings(args.findings, store)
        required = store.config.get("findings_required") is True
        findings_absent = False
        if findings is None:
            if required:
                raise TicketError(NO_FINDINGS_TEXT)
            print(f"pm: {NO_FINDINGS_TEXT}", file=sys.stderr)
            findings_absent = True
        if findings == ["none"] and required:
            for tid in ids:
                if not (args.note or args.reason or "").strip() \
                        and not store.get(tid)["notes"]:
                    raise TicketError(f"--findings none on {tid} needs a non-empty "
                                      "--note or an existing note: 'none' is a "
                                      "statement, not a default")
        for tid in ids:
            st.refuse_if_closed(store.get(tid))
        for tid in ids:
            refuse_if_worktree(store, tid, args.via)
        for tid in ids:
            t = store.get(tid)
            for c in st.close_open_children(store, t, args.force, args.detach):
                c["parent"] = None
                c["updated"] = now()
                c["notes"].append(make_note(f"detached from {t['id']} on close",
                                            "edit-trail"))
        actor = st.acting_identity(args.session)
        for tid in ids:
            t = store.get(tid)
            t["status"] = "done-unmerged" if args.unmerged else "closed"
            t["assignee"] = None
            t.pop("hold", None)
            t.pop("released_by", None)
            if actor:
                t["closed_by"] = actor
            else:
                t.pop("closed_by", None)
            t["updated"] = now()
            if findings is not None:
                t["findings"] = list(findings)
            if findings_absent:
                t["findings_absent"] = True
            note = args.note or args.reason
            if note:
                t["notes"].append(make_note(note, "park" if args.unmerged
                                            else "worker-return"))
            if args.no_deploy_check is not None and not args.unmerged:
                t["notes"].append(make_note(
                    f"deploy check skipped: {args.no_deploy_check}", "finding"))
            print(f"{t['id']} -> {t['status']}")
