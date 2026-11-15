from __future__ import annotations

import base64
import contextlib
import fcntl
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

from . import VERSION
from .common import Fault, DOMAINS, digest, canonical, read_json, write_json, atomic_write, private_dir, now

START="<!-- CWF:BEGIN -->"
END="<!-- CWF:END -->"
GUIDANCE=("For substantive product, architecture, documentation, planning, or code work, use the relevant available cwf-* skill when useful. "
          "Investigate existing solutions, conventions, and accepted decisions before adding competing behavior or artifacts. "
          "Keep discovery bounded and proportionate. For batches, establish dependencies, ownership, and integrated acceptance. "
          "Unrelated everyday questions bypass CWF. Follow existing scope and permissions; no ticketing system or repository initialization is required.")
BLOCK="\n"+START+"\n"+GUIDANCE+"\n"+END+"\n"


def paths(home,config_root=None):
    home=Path(home).resolve()
    return {"home":home,"base":home/".local/share/cwf","skills":home/".agents/skills",
            "launcher":home/".local/bin/cwf","config":home/".config/cwf/config.json",
            "state":home/".local/state/cwf","client":Path(config_root or home/".config/opencode").absolute()}


def snapshot(path):
    path=Path(path)
    if path.is_symlink(): return {"kind":"link","target":os.readlink(path)}
    if path.is_file():
        if path.stat().st_size>2*1024*1024: raise Fault("Managed target unexpectedly large","blocked")
        return {"kind":"file","data":base64.b64encode(path.read_bytes()).decode(),"mode":path.stat().st_mode&0o777}
    if path.exists(): return {"kind":"directory"}
    return {"kind":"absent"}


def check_parents(path):
    for p in Path(path).parents:
        if p.is_symlink(): raise Fault(f"Symlink in installation destination: {p}","blocked")


def restore(path,snap):
    path=Path(path); check_parents(path)
    private_dir(path.parent)
    current=snapshot(path)
    if current["kind"]=="directory": raise Fault("Refusing to replace directory","blocked")
    if snap["kind"]=="absent":
        if path.exists() or path.is_symlink(): path.unlink()
    elif snap["kind"]=="file":
        if path.is_symlink(): path.unlink()
        atomic_write(path,base64.b64decode(snap["data"]),snap["mode"])
    elif snap["kind"]=="link":
        temp=path.with_name(".cwf-link-"+uuid.uuid4().hex)
        try:
            temp.symlink_to(snap["target"])
            os.replace(temp,path)
        finally:
            if temp.is_symlink(): temp.unlink()
    else: raise Fault("Unsupported managed target kind","blocked")


def read_bundle(bundle):
    bundle=Path(bundle).resolve(); init=bundle/"cwf/__init__.py"
    found=re.search(r'(?m)^VERSION\s*=\s*"(\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?)"',init.read_text()) if init.is_file() else None
    if not found: raise Fault("Bundle has no valid release version")
    files={}
    for p in sorted(bundle.rglob("*")):
        if p.is_symlink(): raise Fault("Source release must contain only regular files/directories","blocked")
        if "__pycache__" in p.parts or p.suffix==".pyc" or not p.is_file(): continue
        files[p.relative_to(bundle).as_posix()]=digest(p.read_bytes())
    return {"version":found.group(1),"files":files}


def instruction_file(p):
    return p["client"]/"AGENTS.md"


def marker_body(text):
    if text.count(START)!=text.count(END) or text.count(START)>1:
        raise Fault("Malformed or duplicate CWF instruction markers","blocked")
    if START not in text: return None
    start=text.index(START); end=text.index(END)+len(END)
    if end<start: raise Fault("Reversed instruction markers","blocked")
    return text[start:end]


def without_block(text,body):
    # The installer appends exactly one leading/trailing newline with its block.
    # Remove those only while the complete owned framing is present.
    framed="\n"+body+"\n"
    return text.replace(framed,"",1) if framed in text else text.replace(body,"",1)


def launcher_text(p,python):
    # POSIX sh launcher uses repr-like shell quoting only for known installation paths.
    import shlex
    return "#!/bin/sh\n# CWF-owned launcher\nexec "+shlex.quote(python)+" -B "+shlex.quote(str(p["base"]/"current/cwf.py"))+" --home "+shlex.quote(str(p["home"]))+" --config-root "+shlex.quote(str(p["client"]))+' "$@"\n'


def file_snap(text,mode=0o600):
    return {"kind":"file","data":base64.b64encode(text.encode()).decode(),"mode":mode}


def receipt(p):
    f=p["state"]/"installation.json"
    return read_json(f) if f.exists() else None


def require_no_pending(p):
    if (p["state"]/"transactions").exists():
        for tx_file in (p["state"]/"transactions").glob("*.json"):
            if read_json(tx_file).get("status") in ("applying","recovery_required"):
                raise Fault("Interrupted installation transaction; run install recover first","blocked")


def plan(home,bundle,config_root=None,guidance=True):
    p=paths(home,config_root); source=read_bundle(bundle)
    previous=receipt(p)
    require_no_pending(p)
    if previous and previous.get("status") not in ("installed","disabled"):
        raise Fault("Installation recovery required before further changes","blocked")
    if previous and previous.get("config_root")!=str(p["client"]):
        raise Fault("Existing installation uses another client config root; uninstall or use that root","blocked")
    version=source["version"]; release=p["base"]/"releases"/version
    if release.exists() and read_bundle(release)!=source:
        raise Fault("Release version already exists with different bytes","blocked")
    changes=[]
    owned={c["path"]:c for c in previous.get("changes",[])} if previous else {}
    def add(path,after,kind="normal"):
        check_parents(path)
        before=snapshot(path)
        if str(path) in owned:
            expected=owned[str(path)]["after"]
            if kind=="guidance" and before["kind"]=="file" and expected["kind"]=="file":
                a=base64.b64decode(before["data"]).decode(); b=base64.b64decode(expected["data"]).decode()
                if marker_body(a)!=marker_body(b): raise Fault("Owned guidance was edited; preserve and reconcile manually","blocked")
            elif before!=expected:
                raise Fault(f"Owned target changed since installation: {path}","blocked")
        elif before["kind"]!="absent" and kind not in ("guidance","config"):
            raise Fault(f"Foreign installation target collision: {path}","blocked")
        changes.append({"path":str(path),"before":before,"after":after,"kind":kind})
    # Verify same-name metadata collisions even in differently named directories.
    if p["skills"].exists():
        for skill in p["skills"].glob("*/SKILL.md"):
            if str(skill.parent) in owned: continue
            try: text=skill.read_text()[:4096]
            except OSError: continue
            if re.search(r"(?m)^name:\s*['\"]?cwf-(?:"+"|".join(DOMAINS)+r")[ '\"\r]*$",text):
                raise Fault(f"Existing same-name skill: {skill.parent.name}","blocked")
    add(p["base"]/"current",{"kind":"link","target":str(release)})
    add(p["launcher"],file_snap(launcher_text(p,str(Path(sys.executable).resolve())),0o755))
    config={"schema_version":"cwf/v1","mode":"active","domains":DOMAINS}
    if p["config"].exists():
        from .contracts import CONFIG,validate
        config=validate(read_json(p["config"]),CONFIG)
    add(p["config"],file_snap(json.dumps(config,indent=2)+"\n"),"config")
    active=config.get("mode","active")!="off"
    domains=config.get("domains",DOMAINS)
    for d in DOMAINS:
        link=p["skills"]/("cwf-"+d)
        after={"kind":"link","target":str(p["base"]/"current/skills"/("cwf-"+d))} if active and d in domains else {"kind":"absent"}
        add(link,after)
    agents=instruction_file(p)
    if previous and not guidance and any(c["kind"]=="guidance" for c in previous["changes"]):
        raise Fault("Existing guidance is owned; preserve it on upgrade or uninstall before switching to skill-only","blocked")
    if guidance:
        before=snapshot(agents)
        if before["kind"] not in ("file","absent"): raise Fault("Instruction target must be a regular file","blocked")
        text=base64.b64decode(before["data"]).decode() if before["kind"]=="file" else ""
        existing=marker_body(text)
        if existing and str(agents) not in owned: raise Fault("Unowned CWF marker collision","blocked")
        body=BLOCK.strip("\n")
        if existing: text=text.replace(existing,body,1) if active else without_block(text,existing)
        elif active: text+=BLOCK
        add(agents,file_snap(text,before.get("mode",0o600)),"guidance")
    output={"schema_version":"cwf-install/v1","home":str(p["home"]),"config_root":str(p["client"]),
            "bundle":str(Path(bundle).resolve()),"version":version,"bundle_digest":digest(source["files"]),
            "guidance":guidance,"changes":changes,"previous_receipt_digest":digest(previous)}
    output["fingerprint"]=digest(output)
    return output


@contextlib.contextmanager
def install_lock(p):
    private_dir(p["state"])
    lock=p["state"]/"install.lock"
    if lock.is_symlink(): raise Fault("Install lock symlink","blocked")
    with open(lock,"a") as f:
        try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc: raise Fault("Another installation operation is active","blocked") from exc
        try: yield
        finally: fcntl.flock(f,fcntl.LOCK_UN)


def apply(plan_data,home,config_root=None):
    p=paths(home,config_root)
    if plan_data.get("home")!=str(p["home"]) or plan_data.get("config_root")!=str(p["client"]):
        raise Fault("Plan belongs to a different target home","blocked")
    with install_lock(p):
        fresh=plan(home,plan_data["bundle"],config_root,plan_data["guidance"])
        if fresh!=plan_data: raise Fault("Plan is stale or altered; regenerate and review","blocked")
        old=receipt(p)
        release=p["base"]/"releases"/fresh["version"]
        if not release.exists():
            private_dir(release.parent)
            staging=Path(tempfile.mkdtemp(prefix=".stage-",dir=release.parent))
            try:
                for rel in read_bundle(fresh["bundle"])["files"]:
                    dest=staging/rel; dest.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(Path(fresh["bundle"])/rel,dest)
                if digest(read_bundle(staging)["files"])!=fresh["bundle_digest"]:
                    raise Fault("Bundle changed during apply; regenerate and review","blocked")
                os.replace(staging,release)
            finally:
                if staging.exists(): shutil.rmtree(staging)
        tx={"id":uuid.uuid4().hex,"started_at":now(),"plan":fresh,"previous_receipt":old,"status":"applying"}
        history=p["state"]/"transactions"/(tx["id"]+".json")
        write_json(history,tx)
        applied=[]
        try:
            for change in fresh["changes"]:
                if snapshot(change["path"])!=change["before"]: raise Fault("Target changed during apply","blocked")
                restore(change["path"],change["after"]); applied.append(change)
            changes=[]
            prior={c["path"]:c for c in old.get("changes",[])} if old else {}
            for c in fresh["changes"]:
                c=dict(c); c["original"]=prior.get(c["path"],{}).get("original",c["before"])
                changes.append(c)
            rec={"schema_version":"cwf-install/v1","status":"installed","version":fresh["version"],
                 "config_root":str(p["client"]),"changes":changes,"transaction":tx["id"],"installed_at":now()}
            write_json(p["state"]/"installation.json",rec)
            tx["status"]="complete"; write_json(history,tx)
            return {"version":rec["version"],"receipt":str(p["state"]/"installation.json"),"transaction":tx["id"]}
        except BaseException:
            conflicts=[]
            for c in reversed(applied):
                try:
                    if snapshot(c["path"])==c["after"]: restore(c["path"],c["before"])
                    else: conflicts.append(c["path"])
                except Exception: conflicts.append(c["path"])
            if not conflicts:
                try:
                    if old: write_json(p["state"]/"installation.json",old)
                    elif (p["state"]/"installation.json").exists(): (p["state"]/"installation.json").unlink()
                except Exception: conflicts.append("installation_receipt")
            tx["status"]="recovery_required" if conflicts else "recovered"
            tx["conflicts"]=conflicts; write_json(history,tx)
            raise


def guidance_target(path,after,before):
    current=snapshot(path)
    if current["kind"]!="file" or after["kind"]!="file": raise Fault("Instruction target changed","blocked")
    text=base64.b64decode(current["data"]).decode()
    expected=marker_body(base64.b64decode(after["data"]).decode())
    if marker_body(text)!=expected: raise Fault("Owned instruction block changed; manual reconciliation needed","blocked")
    old=marker_body(base64.b64decode(before["data"]).decode()) if before["kind"]=="file" else None
    if expected: text=text.replace(expected,old,1) if old else without_block(text,expected)
    elif old: text+="\n"+old+"\n"
    if not text and before["kind"]=="absent": return {"kind":"absent"}
    return file_snap(text,current["mode"])


def management_transaction(p,changes,new_receipt):
    """Journal toggles/removal/rollback so interruption has the same recovery path."""
    old=receipt(p)
    tx={"id":uuid.uuid4().hex,"started_at":now(),"status":"applying",
        "plan":{"changes":changes},"previous_receipt":old,"kind":"management"}
    history=p["state"]/"transactions"/(tx["id"]+".json")
    write_json(history,tx); done=[]
    try:
        for c in changes:
            if snapshot(c["path"])!=c["before"]: raise Fault("Target changed during operation","blocked")
            restore(c["path"],c["after"]); done.append(c)
        if new_receipt: write_json(p["state"]/"installation.json",new_receipt)
        elif (p["state"]/"installation.json").exists(): (p["state"]/"installation.json").unlink()
        tx["status"]="complete"; write_json(history,tx)
    except BaseException:
        conflicts=[]
        for c in reversed(done):
            try:
                if snapshot(c["path"])==c["after"]: restore(c["path"],c["before"])
                else: conflicts.append(c["path"])
            except Exception: conflicts.append(c["path"])
        if not conflicts:
            if old: write_json(p["state"]/"installation.json",old)
            elif (p["state"]/"installation.json").exists(): (p["state"]/"installation.json").unlink()
        tx["status"]="recovery_required" if conflicts else "recovered"
        tx["conflicts"]=conflicts; write_json(history,tx)
        raise


def revert(home,config_root=None,rollback=False):
    p=paths(home,config_root)
    with install_lock(p):
        require_no_pending(p)
        rec=receipt(p)
        if not rec: return {"changed":False}
        if rollback:
            tx=read_json(p["state"]/"transactions"/(rec["transaction"]+".json"))
            current={c["path"]:c for c in rec["changes"]}
            changes=[dict(c,after=current[c["path"]]["after"]) for c in tx["plan"]["changes"]]
            previous=tx["previous_receipt"]
        else: changes=rec["changes"]; previous=None
        # Preflight all changes before mutating any target.
        for c in changes:
            if snapshot(c["path"])!=c["after"]:
                if c["kind"]!="guidance": raise Fault(f"Changed owned target; preserving it: {c['path']}","blocked")
                current=snapshot(c["path"])
                if current["kind"]!="file" or marker_body(base64.b64decode(current["data"]).decode())!=marker_body(base64.b64decode(c["after"]["data"]).decode()):
                    raise Fault("Owned guidance modified; preserving it","blocked")
        mutations=[]
        for c in reversed(changes):
            before=c["before"] if rollback else c["original"]
            target=guidance_target(c["path"],c["after"],before) if c["kind"]=="guidance" else before
            mutations.append({"path":c["path"],"before":snapshot(c["path"]),"after":target,"kind":c["kind"]})
        management_transaction(p,mutations,previous)
        return {"changed":True,"state_and_releases":"retained","rolled_back":rollback}


def toggle(home,config_root,enabled,domain=None):
    if domain is not None and domain not in DOMAINS: raise Fault("Unknown domain")
    p=paths(home,config_root)
    with install_lock(p):
        require_no_pending(p)
        rec=receipt(p)
        if not rec: raise Fault("No owned installation","blocked")
        for c in rec["changes"]:
            if c["kind"]!="guidance" and snapshot(c["path"])!=c["after"]:
                raise Fault("Owned target changed; reconcile before toggling","blocked",c["path"])
        config=read_json(p["config"])
        if domain:
            ds=set(config.get("domains",DOMAINS))
            ds.add(domain) if enabled else ds.discard(domain)
            config["domains"]=sorted(ds)
        else: config["mode"]="active" if enabled else "off"
        active=config.get("mode","active")!="off"
        pending=[]
        for c in rec["changes"]:
            path=Path(c["path"])
            if path==p["config"]: after=file_snap(json.dumps(config,indent=2)+"\n")
            elif path.parent==p["skills"]:
                d=path.name.removeprefix("cwf-")
                after={"kind":"link","target":str(p["base"]/"current/skills"/path.name)} if active and d in config.get("domains",DOMAINS) else {"kind":"absent"}
            elif c["kind"]=="guidance":
                cur=snapshot(path)
                if cur["kind"]!="file": raise Fault("Instruction file missing","blocked")
                text=base64.b64decode(cur["data"]).decode(); body=marker_body(text)
                expected=marker_body(base64.b64decode(c["after"]["data"]).decode())
                if body!=expected: raise Fault("Owned guidance changed","blocked")
                if body: text=text.replace(body,BLOCK.strip("\n"),1) if active else without_block(text,body)
                elif active: text+=BLOCK
                after=file_snap(text,cur["mode"])
            else: continue
            pending.append((c,path,snapshot(path),after))
        mutations=[]
        for c,path,before,after in pending:
            mutations.append({"path":str(path),"before":before,"after":after,"kind":c["kind"]})
            c["after"]=after
        rec["status"]="installed" if active else "disabled"
        management_transaction(p,mutations,rec)
        return {"mode":config.get("mode"),"domains":config.get("domains",DOMAINS),"loaded_context":"not_retracted"}


def recover(home,config_root=None):
    """Recover interrupted apply transactions using exact before/after states."""
    p=paths(home,config_root); recovered=[]
    with install_lock(p):
        for f in sorted((p["state"]/"transactions").glob("*.json")):
            tx=read_json(f)
            if tx["status"] not in ("applying","recovery_required"): continue
            changes=tx["plan"]["changes"]
            conflicts=[c["path"] for c in changes if snapshot(c["path"]) not in (c["before"],c["after"])]
            if conflicts: raise Fault("Recovery would overwrite changed targets","blocked",conflicts)
            for c in reversed(changes):
                if snapshot(c["path"])==c["after"]: restore(c["path"],c["before"])
            old=tx["previous_receipt"]
            if old: write_json(p["state"]/"installation.json",old)
            elif (p["state"]/"installation.json").exists(): (p["state"]/"installation.json").unlink()
            tx["status"]="recovered"; write_json(f,tx); recovered.append(tx["id"])
    return {"recovered":recovered}
