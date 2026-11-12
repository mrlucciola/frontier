from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sqlite3
import sys
from pathlib import Path

from . import VERSION
from .common import Fault, DOMAINS, EXIT, result, read_json, write_json, scope_info, digest
from .config import settings
from .state import State
from . import installer, operations
from .discovery import discover, safe_read, ignored

ROOT=Path(__file__).resolve().parent.parent
MANAGEMENT={"doctor","install","upgrade","rollback","uninstall","enable","disable","state","version","validate"}


def doctor(home,codex_home):
    p=installer.paths(home,codex_home); rec=installer.receipt(p)
    checks=[]
    if rec:
        for c in rec["changes"]:
            current=installer.snapshot(c["path"])
            valid=current==c["after"]
            if not valid and c["kind"]=="guidance" and current["kind"]=="file":
                import base64
                valid=installer.marker_body(base64.b64decode(current["data"]).decode())==installer.marker_body(base64.b64decode(c["after"]["data"]).decode())
            checks.append({"target":c["path"],"intact":valid})
        try:
            installer.verify_bundle(p["base"]/"current")
            checks.append({"target":"release_integrity","intact":True})
        except (Fault,OSError): checks.append({"target":"release_integrity","intact":False})
    return {"framework_version":VERSION,"python":platform.python_version(),"os":platform.system(),
            "machine":platform.machine(),"git_available":bool(shutil.which("git")),
            "codex_executable_available":bool(shutil.which("codex")),"installation":rec.get("status") if rec else "not_installed",
            "checks":checks,"live_skill_visibility":"NOT_TESTED","cli_behavior":"NOT_TESTED",
            "ide_behavior":"NOT_TESTED","macos_qualification":"NOT_TESTED",
            "effective_agents":str(installer.effective_agents(p))}


def dispatch(command,action,req,home,codex_home,ephemeral):
    if command=="version": return result({"version":VERSION}),0
    if command=="doctor": return result(doctor(home,codex_home)),0
    if command=="validate":
        from .contracts import SCHEMAS,validate
        if req.get("contract") not in SCHEMAS: raise Fault("Unknown contract")
        validate(req["record"],SCHEMAS[req["contract"]]); return result({"valid":True}),0
    if command in ("install","upgrade"):
        if action=="plan": return result(installer.plan(home,req.get("bundle",str(ROOT)),codex_home,req.get("guidance",True))),0
        if action=="apply":
            plan=read_json(req["plan_file"])
            if "data" in plan: plan=plan["data"]
            return result(installer.apply(plan,home,codex_home)),0
        if action=="recover": return result(installer.recover(home,codex_home)),0
        raise Fault("Use install/upgrade plan, apply, or recover")
    if command in ("rollback","uninstall"):
        return result(installer.revert(home,codex_home,rollback=command=="rollback")),0
    if command in ("enable","disable"):
        return result(installer.toggle(home,codex_home,command=="enable",req.get("domain"))),0
    global_config=settings(home)
    if command!="state" and global_config["mode"]=="off": return result(status="skipped",reason="framework_off"),0
    if "scope" not in req or not isinstance(req["scope"],str): raise Fault("Explicit scope directory required")
    root=Path(req["scope"]).expanduser().resolve()
    if not root.is_dir(): raise Fault("Scope directory unavailable","blocked")
    config=settings(home,root,req.get("limits"))
    if command!="state" and config["mode"]=="off": return result(status="skipped",reason="scope_off"),0
    domain=req.get("domain")
    if command in ("discover","inspect-source"):
        if domain not in DOMAINS: raise Fault("Explicit relevant domain required")
        if domain not in config["domains"]: return result(status="skipped",reason="domain_disabled"),0
    if command=="discover":
        packet=discover(home,req,config,ephemeral)
        return result(packet,"partial" if packet["status"]=="partial" else "ok"),5 if packet["status"]=="partial" else 0
    if command=="inspect-source":
        info=scope_info(root); path=req["path"]
        if path in ignored(root,[path],bool(info["git_root"])): raise Fault("Git-ignored source excluded","blocked")
        raw,text=safe_read(root,path,config)
        start=req.get("line",1); count=req.get("lines",40)
        if not isinstance(start,int) or not isinstance(count,int) or start<1 or not 1<=count<=200: raise Fault("Invalid line bounds")
        excerpt="\n".join(text.splitlines()[start-1:start-1+count])
        clipped=excerpt.encode()[:config["limits"]["packet_bytes"]].decode(errors="ignore")
        return result({"source_ref":path,"content_hash":digest(raw),"line":start,"excerpt":clipped,
                       "truncated":clipped!=excerpt}),0
    if command in ("checkpoint","observe"):
        if ephemeral: raise Fault("Durable record cannot be written in ephemeral mode","blocked")
        fn=operations.checkpoint if command=="checkpoint" else operations.observation
        return result(fn(home,req,config)),0
    if command=="resume":
        r=operations.resume(home,req,config)
        return result(r,"ok" if r["ready_to_resume"] else "partial"),0 if r["ready_to_resume"] else 5
    if command=="batch" and action=="validate": return result(operations.batch_validate(req["batch"])),0
    if command=="check":
        r=operations.run_checks(req,config)
        if not r["required_passed"]: return result(r,"blocked", "required_check_failed"),4
        return result(r),0
    if command=="worktree":
        if ephemeral: raise Fault("Worktree ownership needs durable state","blocked")
        return result(operations.worktree(home,action,req)),0
    if command=="state":
        with State(home) as state:
            if action=="inspect":
                records=state.records(str(root))
                for r in records:
                    if r["kind"]=="observation":
                        r["source_validation"]=operations.revalidate_sources(root,r["record"]["sources"],config)
                return result({"records":records}),0
            if action=="export":
                records=state.records(str(root))
                # Do not export source text, identifiers, paths, or arbitrary task content.
                from collections import Counter
                return result({"counts":dict(Counter(r["kind"] for r in records)),"framework_version":VERSION,
                               "source_content_included":False}),0
            if action=="prune": return result(state.prune(str(root),config["cache_days"],config["observation_days"])),0
            if action=="purge":
                if req.get("confirm_scope")!=str(root): raise Fault("Explicit canonical confirm_scope required")
                return result(state.purge(str(root))),0
        raise Fault("Unknown state operation")
    raise Fault("Unknown command/action")


def main(argv=None):
    parser=argparse.ArgumentParser(description="CWF local tools. Requests are JSON; no model/network calls.")
    parser.add_argument("command",choices=["discover","inspect-source","checkpoint","resume","observe","batch","check","worktree","state","doctor","validate","install","upgrade","rollback","uninstall","enable","disable","version"])
    parser.add_argument("action",nargs="?")
    parser.add_argument("--input",help="JSON file or - for stdin")
    parser.add_argument("--output",help="Write JSON result to this explicit file")
    parser.add_argument("--home",help="Target user home; temporary homes supported")
    parser.add_argument("--codex-home",help="Override Codex config root")
    parser.add_argument("--ephemeral",action="store_true")
    parser.add_argument("--format",choices=["json","text"],default="json")
    args=parser.parse_args(argv)
    home=Path(args.home).expanduser().resolve() if args.home else Path.home().resolve()
    codex_home=Path(args.codex_home or (str(home/".codex") if args.home else os.environ.get("CODEX_HOME",str(home/".codex")))).expanduser().absolute()
    os.umask(0o077)
    try:
        if sys.version_info<(3,11): raise Fault("Python 3.11+ required","blocked")
        req={}
        if args.input=="-":
            data=sys.stdin.buffer.read(1_048_577)
            if len(data)>1_048_576: raise Fault("Request too large")
            req=json.loads(data)
        elif args.input: req=read_json(args.input)
        if not isinstance(req,dict): raise Fault("Request must be an object")
        out,code=dispatch(args.command,args.action,req,home,codex_home,args.ephemeral)
    except Fault as exc:
        status=exc.code if exc.code in ("blocked","partial","skipped") else "error"
        out=result({"message":str(exc),"details":exc.details},status,exc.code); code=EXIT[exc.code]
    except (KeyError,TypeError,ValueError) as exc:
        out=result({"message":"Invalid or missing request field","details":str(exc)[:200]},"error","invalid"); code=2
    except (OSError,sqlite3.Error) as exc:
        out=result({"message":"Local operation failed; no success asserted","details":type(exc).__name__},"error","local_io"); code=6
    if args.output:
        try: write_json(Path(args.output).expanduser().absolute(),out)
        except (OSError,Fault) as exc:
            print(json.dumps(result({"message":str(exc)},"error","output_failed"))); return 6
    if args.format=="text":
        print(f"{out['status']}: {out['reason']}")
        print(json.dumps(out["data"],indent=2,ensure_ascii=False))
    else: print(json.dumps(out,ensure_ascii=False,sort_keys=True))
    return code
