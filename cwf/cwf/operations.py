from __future__ import annotations

import fnmatch
import json
import os
import selectors
import signal
import subprocess
import time
from pathlib import Path

from . import VERSION
from .common import Fault, digest, scope_info, within, git, valid_id, result
from .contracts import validate, TASK, OBSERVATION, BATCH, CHECK
from .discovery import safe_read, ignored
from .state import State


def revalidate_sources(root,sources,config):
    findings=[]
    info=scope_info(root)
    for source in sources:
        try:
            if source["path"] in ignored(root,[source["path"]],bool(info["git_root"])):
                raise Fault("Git ignored source","blocked")
            raw,_=safe_read(root,source["path"],config)
            status="verified" if digest(raw)==source["content_hash"] else "stale"
        except (OSError,Fault): status="unavailable"
        findings.append({"path":source["path"],"status":status})
    return findings


def observation(home,req,config):
    root=str(Path(req["scope"]).resolve()); record=validate(req["record"],OBSERVATION)
    if not record["sources"]: raise Fault("Observation needs provenance")
    if record["claim_status"]=="accepted" and not (record.get("accepted_by") and record.get("acceptance_source")):
        raise Fault("Accepted claim requires acceptance attribution and source")
    if record["claim_status"]=="accepted" and record["acceptance_source"].split("#",1)[0] not in {s["path"] for s in record["sources"]}:
        raise Fault("Acceptance source must be among the verified source references")
    checked=revalidate_sources(root,record["sources"],config)
    if any(x["status"]!="verified" for x in checked): raise Fault("Observation sources are not current","blocked",checked)
    with State(home) as state:
        return state.put("observation",root,record["id"],record,req.get("expected_revision",0))


def checkpoint(home,req,config):
    root=str(Path(req["scope"]).resolve()); record=validate(req["record"],TASK)
    if Path(record["scope_root"]).resolve()!=Path(root): raise Fault("Task root does not match scope")
    if record.get("framework_version",VERSION)!=VERSION: raise Fault("Task pinned to another release","blocked")
    record=dict(record,framework_version=VERSION)
    if record["status"]=="complete":
        covered={x["criterion"] for x in record.get("evidence",[])+record.get("waivers",[])}
        if not record["acceptance"] or not set(record["acceptance"])<=covered:
            raise Fault("Completion requires evidence or attributed waiver for every criterion","blocked")
        if record.get("blockers"): raise Fault("Cannot complete with unresolved blockers","blocked")
        checks=revalidate_sources(root,record.get("sources",[]),config)
        if any(x["status"]!="verified" for x in checks): raise Fault("Completion sources changed","blocked",checks)
    with State(home) as state:
        expected=req.get("expected_revision",0)
        if expected:
            old=state.get("task",root,record["id"])["record"]
            if old.get("framework_version")!=VERSION: raise Fault("Use the task's pinned release; migration not implicit","blocked")
        return state.put("task",root,record["id"],record,expected)


def resume(home,req,config):
    root=str(Path(req["scope"]).resolve())
    with State(home) as state:
        saved=state.get("task",root,valid_id(req["id"]))
    version=saved["record"].get("framework_version")
    if version!=VERSION: raise Fault("Resume using the retained task release","blocked",{"required_version":version})
    saved["source_validation"]=revalidate_sources(root,saved["record"].get("sources",[]),config)
    saved["ready_to_resume"]=all(x["status"]=="verified" for x in saved["source_validation"])
    return saved


def overlaps(a,b):
    a=Path(a).as_posix().rstrip("/").casefold(); b=Path(b).as_posix().rstrip("/").casefold()
    return a=="." or b=="." or a==b or a.startswith(b+"/") or b.startswith(a+"/")


def batch_validate(data):
    validate(data,BATCH)
    if not data["items"] or not data["acceptance"]: raise Fault("Batch needs items and integrated acceptance")
    ids=[x["id"] for x in data["items"]]
    if len(ids)!=len(set(ids)): raise Fault("Duplicate batch item IDs")
    byid={x["id"]:x for x in data["items"]}
    for item in data["items"]:
        if not item["acceptance"]: raise Fault(f"Missing acceptance: {item['id']}")
        if set(item["depends_on"])-set(ids): raise Fault(f"Unknown dependency: {item['id']}")
        for path in item["writes"]:
            if Path(path).is_absolute() or ".." in Path(path).parts: raise Fault("Batch write paths must be relative")
            if not path or any(c in path for c in "*?["):
                raise Fault("Use concrete batch write paths or directory prefixes, not globs")
    pending=set(ids); done=set(); waves=[]
    while pending:
        wave=sorted(i for i in pending if set(byid[i]["depends_on"])<=done)
        if not wave: raise Fault("Dependency cycle","blocked",{"items":sorted(pending)})
        for n,a in enumerate(wave):
            for b in wave[n+1:]:
                common=[(x,y) for x in byid[a]["writes"] for y in byid[b]["writes"] if overlaps(x,y)]
                resources=set(byid[a].get("resources",[]))&set(byid[b].get("resources",[]))
                if common or resources:
                    raise Fault("Concurrent declared surfaces conflict; add sequencing or split ownership","blocked",
                                {"items":[a,b],"writes":common,"resources":sorted(resources)})
        waves.append(wave); pending-=set(wave); done.update(wave)
    return {"waves":waves,"integration_owner":data["integration_owner"],"semantic_independence":"agent_must_verify",
            "cross_machine_locking":False}


def bounded_command(argv,cwd,timeout,cap=16384):
    """Run explicit argv, kill process group at timeout or output budget."""
    try:
        p=subprocess.Popen(argv,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    except OSError as exc: raise Fault("Check executable unavailable","blocked",type(exc).__name__) from exc
    sel=selectors.DefaultSelector(); sel.register(p.stdout,selectors.EVENT_READ); sel.register(p.stderr,selectors.EVENT_READ)
    output=bytearray(); deadline=time.monotonic()+timeout; limit=None
    try:
        while sel.get_map():
            remaining=deadline-time.monotonic()
            if remaining<=0: limit="timeout"; break
            for key,_ in sel.select(min(remaining,0.1)):
                chunk=os.read(key.fileobj.fileno(),4096)
                if not chunk: sel.unregister(key.fileobj); continue
                if len(output)+len(chunk)>cap: limit="output_limit"; break
                output.extend(chunk)
            if limit: break
        if limit:
            try: os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError: pass
        try: code=p.wait(timeout=max(0.1,deadline-time.monotonic()))
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL); code=p.wait(); limit="timeout"
    finally:
        if p.poll() is None:
            os.killpg(p.pid,signal.SIGKILL); p.wait()
        sel.close(); p.stdout.close(); p.stderr.close()
    return code,bytes(output),limit


def run_checks(req,config):
    root=Path(req["scope"]).resolve(); checks=req.get("checks",[])
    if not isinstance(checks,list) or not checks or len(checks)>50: raise Fault("Provide 1–50 checks")
    findings=[]
    for check in checks:
        validate(check,CHECK)
        if check["kind"]=="command":
            if not check.get("argv") or not check.get("authorization"):
                raise Fault("Command requires explicit argv and authorization reference","blocked")
            # Authorization is a recorded assertion, not a sandbox permission grant.
            code,out,limit=bounded_command(check["argv"],root,check.get("timeout",60))
            finding={"id":check["id"],"status":"unknown" if limit else "passed" if code==check.get("expected_exit",0) else "failed",
                     "exit_code":code,"limit":limit,"output_sha256":digest(out),"output_bytes":len(out),
                     "authorization":check["authorization"],"required":check["required"]}
            # No raw command output is retained/exported by default.
        else:
            if not check.get("paths") or not check.get("literal"): raise Fault("Literal check requires explicit paths and literal")
            matches=[]; unavailable=[]
            for path in check["paths"]:
                try:
                    raw,text=safe_read(root,path,config)
                    if check["literal"] in text: matches.append(path)
                except (OSError,Fault): unavailable.append(path)
            finding={"id":check["id"],"status":"failed" if matches else "unknown" if unavailable else "passed",
                     "matches":matches,"unavailable":unavailable,"required":check["required"]}
        findings.append(finding)
    failed=any(x["required"] and x["status"]!="passed" for x in findings)
    return {"checks":findings,"required_passed":not failed,"mode":config["mode"]}


def worktree(home,action,req):
    info=scope_info(req["scope"])
    if not info["git_root"]: raise Fault("Worktrees require Git","blocked")
    root=Path(info["git_root"])
    if action=="list":
        return {"porcelain":git(root,"worktree","list","--porcelain").stdout.decode()}
    target=Path(req["path"]).expanduser().resolve()
    record_id=digest(str(target))[:24]
    with State(home) as state:
        if action=="create":
            if target.exists(): raise Fault("Worktree destination already exists","blocked")
            if target.is_relative_to(root): raise Fault("Use a sibling worktree, not a nested destination","blocked")
            base=req.get("base","HEAD"); branch=req.get("branch")
            if not isinstance(base,str) or base.startswith("-"): raise Fault("Invalid base")
            commit=git(root,"rev-parse","--verify",base+"^{commit}").stdout.decode().strip()
            args=["worktree","add","--detach",str(target),commit]
            if branch:
                if not isinstance(branch,str) or branch.startswith("-"): raise Fault("Invalid branch")
                git(root,"check-ref-format","--branch",branch)
                args=["worktree","add","-b",branch,str(target),commit]
            try:
                previous=state.get("worktree",str(root),record_id)
                if previous["record"].get("active"): raise Fault("Worktree has an active ownership record","blocked")
                expected=previous["revision"]
            except Fault as exc:
                if str(exc)!="Record not found in selected scope": raise
                expected=0
            # Ownership is written only after successful creation. If state fails, keep worktree.
            git(root,*args,timeout=30)
            return state.put("worktree",str(root),record_id,{"path":str(target),"base":commit,"branch":branch,"active":True},expected)
        if action!="remove": raise Fault("Unknown worktree operation")
        owned=state.get("worktree",str(root),record_id)
        target_info=scope_info(target)
        if target_info["identity"]!=info["identity"] or Path(target_info["git_root"] or "")!=target:
            raise Fault("Target is not the owned worktree","blocked")
        if git(target,"status","--porcelain","--untracked-files=all").stdout:
            raise Fault("Dirty worktree; preserving work","blocked")
        if git(target,"ls-files","--others","--ignored","--exclude-standard").stdout:
            raise Fault("Ignored files remain in worktree; preserve or explicitly clean them first","blocked")
        active=[r["id"] for r in state.records(kind="task") if Path(r["root"]).is_relative_to(target) and r["record"]["status"] not in ("complete","abandoned")]
        if active: raise Fault("Active tasks reference worktree","blocked",active)
        head=git(target,"rev-parse","HEAD").stdout.decode().strip()
        branches=git(root,"for-each-ref","--format=%(refname)","--contains",head,"refs/heads/","refs/tags/").stdout
        if head!=owned["record"]["base"] and not branches:
            raise Fault("Detached commits are not preserved by a branch/tag","blocked")
        git(root,"worktree","remove",str(target))
        record=dict(owned["record"],active=False)
        return state.put("worktree",str(root),record_id,record,owned["revision"])
