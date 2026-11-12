from __future__ import annotations

import fnmatch
import heapq
import os
import re
import stat
import subprocess
import time
from collections import Counter
from pathlib import Path

from . import VERSION
from .common import Fault, digest, now, scope_info, within, canonical
from .contracts import PACKET, validate
from .state import State

EXCLUDED_DIRS={".git",".hg",".svn","node_modules","vendor","target","dist","build",
               ".next",".cache","__pycache__",".venv","venv",".ssh",".aws",".local"}
SECRET_NAMES={"credentials","credentials.json","auth.json","id_rsa","id_ed25519",".npmrc",".pypirc",".netrc"}
TEXT_SUFFIXES={".md",".mdx",".txt",".rst",".ts",".tsx",".js",".jsx",".mjs",".cjs",".rs",
               ".py",".go",".java",".kt",".sql",".json",".toml",".yaml",".yml",".html",".css",
               ".scss",".sh",".rb",".c",".h",".cpp",".swift",".proto",".graphql"}
SPECIAL={"AGENTS.md","AGENTS.override.md","README","Makefile","Dockerfile","LICENSE"}


def excluded(relative, config):
    p=Path(relative)
    if any(x.casefold() in EXCLUDED_DIRS for x in p.parts): return "excluded_directory"
    if p.name.casefold() in SECRET_NAMES or p.name.casefold().startswith(".env") or p.suffix.casefold() in {".pem",".key",".p12",".pfx"}:
        return "sensitive_path"
    if any(fnmatch.fnmatch(relative,x) or fnmatch.fnmatch(p.name,x) for x in config["exclusions"]):
        return "configured_exclusion"
    return None


def ignored(root, paths, is_git):
    if not is_git or not paths: return set()
    from .common import git
    # Bounded batches, no huge git ls-files output allocation.
    try:
        p=subprocess.run(["git","-C",str(root),"check-ignore","--stdin","-z"],
                         input=b"\0".join(os.fsencode(x) for x in paths)+b"\0",
                         capture_output=True,timeout=2,env=dict(os.environ,GIT_OPTIONAL_LOCKS="0"))
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise Fault("Ignore rules could not be checked", "partial") from exc
    if p.returncode not in (0,1): raise Fault("Ignore rules unavailable", "partial")
    return {os.fsdecode(x) for x in p.stdout.split(b"\0") if x}


def enumerate_files(root, config, info, deadline):
    limits=config["limits"]; reasons=Counter(); hits=[]; paths=[]; entries=0
    def bounded_walk():
        nonlocal entries
        stack=[Path(root)]
        while stack:
            folder=stack.pop(); names=[]
            try:
                with os.scandir(folder) as iterator:
                    for entry in iterator:
                        if time.monotonic()>deadline:
                            hits.append("time"); return
                        entries+=1
                        if entries>min(limits["max_files"]*10,100000):
                            hits.append("enumeration_entries"); return
                        names.append((entry.name,entry.is_dir(follow_symlinks=False)))
            except OSError:
                reasons["enumeration_error"]+=1; continue
            dirs=[n for n,d in names if d]; files=[n for n,d in names if not d]
            yield folder,dirs,files
            stack.extend(folder/d for d in reversed(dirs))
    for folder,dirs,files in bounded_walk():
        if time.monotonic()>deadline:
            hits.append("time"); break
        dirs.sort(); files.sort()
        kept=[]
        for d in dirs:
            p=Path(folder)/d; rel=p.relative_to(root).as_posix()
            why=excluded(rel,config)
            if p.is_symlink(): why="symlink"
            if (p/".git").exists(): why="nested_repository"
            if why: reasons[why]+=1
            else: kept.append(d)
        dirs[:]=kept
        candidate=[]
        for name in files:
            p=Path(folder)/name; rel=p.relative_to(root).as_posix()
            why=excluded(rel,config)
            if p.is_symlink(): why="symlink"
            if config["source_roots"] and not any(x=="." or rel==x or rel.startswith(x.rstrip("/")+"/") for x in config["source_roots"]):
                # Always include root instructions and configuration.
                if rel not in ("AGENTS.md","AGENTS.override.md",".cwf.json"): why="outside_source_roots"
            if why: reasons[why]+=1; continue
            if p.suffix.lower() not in TEXT_SUFFIXES and name not in SPECIAL:
                reasons["unsupported_format"]+=1; continue
            candidate.append(rel)
        ignored_set=ignored(root,candidate,info["git_root"] is not None)
        for rel in candidate:
            if rel in ignored_set: reasons["git_ignored"]+=1; continue
            if len(paths)>=limits["max_files"]:
                hits.append("files"); return paths,reasons,hits
            paths.append(rel)
    return sorted(paths),reasons,hits


def safe_read(root, rel, config, verify_ignored=True):
    rel=Path(rel).as_posix()
    why=excluded(rel,config)
    if why: raise Fault(f"Source excluded: {why}","blocked")
    path=within(root,rel)
    for parent in path.parents:
        if parent==Path(root).resolve(): break
        if (parent/".git").exists() or (parent/".git").is_symlink():
            raise Fault("Nested repository requires a separate selected scope","blocked")
    if config["source_roots"] and rel not in ("AGENTS.md","AGENTS.override.md",".cwf.json"):
        if not any(x=="." or rel==Path(x).as_posix() or rel.startswith(Path(x).as_posix().rstrip("/")+"/") for x in config["source_roots"]):
            raise Fault("Source outside configured source roots","blocked")
    if verify_ignored:
        info=scope_info(root)
        if rel in ignored(root,[rel],bool(info["git_root"])):
            raise Fault("Git-ignored source excluded","blocked")
    if not path.is_file(): raise Fault("Source is not a regular file","blocked")
    limit=config["limits"]["file_bytes"]
    if path.stat().st_size>limit: raise Fault("Source exceeds individual-file limit","partial")
    # O_NOFOLLOW protects the final component; parent checks above reject static links.
    # Open each path component without following links, including parent races.
    dirfd=os.open(Path(root).resolve(),os.O_RDONLY|os.O_DIRECTORY)
    try:
        parts=Path(rel).parts
        for part in parts[:-1]:
            nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=dirfd)
            os.close(dirfd); dirfd=nxt
        fd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=dirfd)
        with os.fdopen(fd,"rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode): raise Fault("Source is not a regular file","blocked")
            raw=stream.read(limit+1)
    finally:
        os.close(dirfd)
    if len(raw)>limit: raise Fault("Source grew past individual-file limit","partial")
    if b"\0" in raw: raise Fault("Binary source unsupported","partial")
    try: text=raw.decode("utf-8")
    except UnicodeError as exc: raise Fault("Non-UTF8 source unsupported","partial") from exc
    return raw,text


def scan(root,config,info,deadline,query,requested):
    paths,reasons,hits=enumerate_files(root,config,info,deadline)
    manifest={}; candidates=[]; used=0; failures=0
    terms=sorted(set(re.findall(r"[a-z0-9_]+",query.lower())))
    max_candidates=1000
    for rel in paths:
        if time.monotonic()>deadline: hits.append("time"); break
        try:
            size=(Path(root)/rel).stat().st_size
            if used+size>config["limits"]["max_bytes"]: hits.append("bytes"); break
            raw,text=safe_read(root,rel,config,verify_ignored=False)
            used+=len(raw); manifest[rel]=digest(raw)
        except (OSError,Fault) as exc:
            failures+=1; reasons["read_failed_or_oversized"]+=1; continue
        lower=text.lower()
        overlap=sum(lower.count(t) for t in terms)
        explicit=rel in requested
        instruction=Path(rel).name in {"AGENTS.md","AGENTS.override.md"}
        if not overlap and not explicit and not instruction: continue
        phrase=bool(query and query.lower() in lower)
        migration=bool(re.search(r"deprecat|supersed|migrat|accepted|decision",lower)) and overlap>0
        score=(int(explicit),int(instruction),int(phrase),int(migration),min(overlap,1000))
        lines=text.splitlines()
        indices=[i for i,line in enumerate(lines) if any(t in line.lower() for t in terms)]
        start=indices[0] if indices else 0
        excerpt="\n".join(lines[max(0,start-1):start+5])[:900]
        finding={"source_ref":rel,"locator":f"line {start+1}","content_hash":manifest[rel],
                 "kind":"instruction_source" if instruction else "migration_candidate" if migration else "lexical_candidate",
                 "claim_status":"observed","rank_reason":f"explicit={explicit}; phrase={phrase}; migration_terms={bool(migration)}; term_hits={overlap}",
                 "excerpt":excerpt}
        candidates.append((score,rel,finding))
        if len(candidates)>max_candidates:
            candidates.sort(key=lambda x:(tuple(-s for s in x[0]),x[1]))
            candidates.pop(); hits.append("candidate_pool")
    candidates.sort(key=lambda x:(tuple(-s for s in x[0]),x[1]))
    return manifest,candidates,used,failures,reasons,sorted(set(hits))


def discover(home,request,config,ephemeral=False):
    root=Path(request["scope"]).expanduser().resolve(); info=scope_info(root)
    if root==Path(home).resolve() or root==Path(root.anchor):
        raise Fault("Select a work directory, not home or filesystem root","blocked")
    query=request.get("query","")
    if not isinstance(query,str) or not query.strip() or len(query)>4000: raise Fault("A bounded nonempty query is required")
    requested=request.get("files",[])
    if not isinstance(requested,list) or not all(isinstance(x,str) for x in requested): raise Fault("files must be relative paths")
    for rel in requested: within(root,rel)
    deadline=time.monotonic()+config["limits"]["seconds"]
    manifest,candidates,used,failures,reasons,hits=scan(root,config,info,deadline,query,requested)
    # Second bounded hash pass detects changes, including additions/deletions.
    again,_,_,failures2,reasons2,hits2=scan(root,config,info,deadline,"",[])
    stable=manifest==again and not hits2 and failures2==0 and not reasons2.get("enumeration_error")
    if not stable: hits.append("snapshot_unverified_or_changed")
    observations=[]
    if not ephemeral:
        with State(home,fallback=True) as state:
            observations=state.records(str(root),"observation",201)
        if len(observations)>200:
            hits.append("observation_limit"); observations=observations[:200]
        terms=set(re.findall(r"[a-z0-9_]+",query.lower()))
        for row in observations:
            obs=row["record"]
            if not all(manifest.get(s["path"])==s["content_hash"] for s in obs["sources"]):
                reasons["stale_or_unread_observation"]+=1; continue
            if not any(t in obs["statement"].lower() for t in terms): continue
            source=obs["sources"][0]
            f={"source_ref":source["path"],"locator":"observation:"+row["id"],"content_hash":source["content_hash"],
               "kind":"local_observation","claim_status":obs["claim_status"],
               "rank_reason":"current source fingerprints; local recorded claim, not independently authenticated",
               "excerpt":obs["statement"][:900]}
            candidates.append(((0,0,0,1,0),source["path"]+row["id"],f))
        candidates.sort(key=lambda x:(tuple(-s for s in x[0]),x[1]))
    findings=[]; size=2
    for _,_,f in candidates:
        n=len(canonical(f).encode())+1
        if len(findings)>=config["limits"]["max_findings"] or size+n>config["limits"]["packet_bytes"]: break
        findings.append(f); size+=n
    omitted=len(candidates)-len(findings)
    missing=[f for f in requested if f not in manifest]
    if missing: hits.append("explicit_source_unread")
    partial=bool(hits or failures or omitted or reasons.get("enumeration_error"))
    status="partial" if partial else "complete_within_scope"
    snapshot=digest(manifest)
    cachekey=digest({"snapshot":snapshot,"observations":observations,"config":config,"query":query,"requested":requested,"version":VERSION,"domain":request["domain"]})
    with State(home,ephemeral=ephemeral,fallback=True) as state:
        sid,wid=state.ids(info)
        packet={"schema_version":"cwf/v1","packet_id":cachekey[:24],"scope_id":sid,"worktree_id":wid,
                "domain":request["domain"],"query":query,"generated_at":now(),"tool_version":VERSION,
                "config_digest":digest(config),"snapshot_digest":snapshot,"findings":findings,
                "conflicts":["semantic_conflicts_not_automatically_determined"],
                "coverage":{"root":str(root),"files":len(manifest),"bytes":used,
                 "excluded":sum(reasons.values()),"exclusion_reasons":dict(reasons),
                 "omitted_results":omitted,"limits_hit":sorted(set(hits)),"read_failures":failures,
                 "manifest_stable":stable,"semantic_completeness":False},
                "status":status,"persistence":"durable" if state.durable else "ephemeral",
                "cache":"fingerprint_match" if state.cached(str(root),cachekey) else "miss"}
        while len(canonical(packet).encode())>config["limits"]["packet_bytes"]+2000 and packet["findings"]:
            packet["findings"].pop()
            packet["coverage"]["omitted_results"]+=1
            packet["status"]="partial"
        if len(canonical(packet).encode())>config["limits"]["packet_bytes"]+2000:
            raise Fault("Packet budget cannot hold required metadata; narrow query or raise explicit budget","partial")
        validate(packet,PACKET)
        try: state.cache(str(root),cachekey,packet)
        except Exception:
            packet["persistence"]="cache_write_failed"
        return packet
