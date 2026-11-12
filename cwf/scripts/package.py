#!/usr/bin/env python3
"""Build checksum manifest and a deterministic ZIP; never include local state."""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from cwf import VERSION


def manifest(root=ROOT,version=VERSION):
    files={}
    for p in sorted(root.rglob('*')):
        if '__pycache__' in p.parts or p.suffix=='.pyc': continue
        if p.is_symlink(): raise ValueError(f'Symlink in source package: {p}')
        if not p.is_file(): continue
        rel=p.relative_to(root).as_posix()
        if rel in ('MANIFEST.json','CHECKSUMS.sha256'): continue
        files[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    payload={'schema_version':'cwf-release/v1','version':version,'files':files}
    (root/'MANIFEST.json').write_text(json.dumps(payload,indent=2)+'\n')
    checks=dict(files)
    checks['MANIFEST.json']=hashlib.sha256((root/'MANIFEST.json').read_bytes()).hexdigest()
    (root/'CHECKSUMS.sha256').write_text(''.join(f'{h}  {name}\n' for name,h in sorted(checks.items())))
    return payload


def package(destination):
    m=manifest()
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel in sorted([*m['files'],'MANIFEST.json','CHECKSUMS.sha256']):
            info=zipfile.ZipInfo(f'cwf-{VERSION}/{rel}',date_time=(2026,1,1,0,0,0))
            info.create_system=3; info.external_attr=0o100644<<16
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,(ROOT/rel).read_bytes())
    return hashlib.sha256(Path(destination).read_bytes()).hexdigest()


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output'); a=p.parse_args()
    print(package(a.output) if a.output else json.dumps({'files':len(manifest()['files'])}))
