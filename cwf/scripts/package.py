#!/usr/bin/env python3
"""Build a deterministic ZIP; never include local state."""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from cwf import VERSION
from cwf.installer import read_bundle


def package(destination):
    files=sorted(read_bundle(ROOT)['files'])
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel in files:
            info=zipfile.ZipInfo(f'cwf-{VERSION}/{rel}',date_time=(2026,1,1,0,0,0))
            info.create_system=3; info.external_attr=0o100644<<16
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,(ROOT/rel).read_bytes())
    return hashlib.sha256(Path(destination).read_bytes()).hexdigest()


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); a=p.parse_args()
    print(package(a.output))
