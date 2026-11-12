"""Read-only source adapter protocol. No remote adapters are bundled in v0.1."""
from typing import Protocol
from dataclasses import dataclass
from pathlib import Path
from .common import digest, Fault, within, scope_info
from .discovery import safe_read, ignored

@dataclass(frozen=True)
class Source:
    uri: str
    revision: str
    text: str
    freshness: str

class SourceAdapter(Protocol):
    def capabilities(self) -> dict: ...
    def resolve(self, reference: str) -> str: ...
    def read(self, reference: str) -> Source: ...
    def freshness(self, reference: str, revision: str) -> str: ...

class LocalTextAdapter:
    def __init__(self,root,config):
        self.root=Path(root).resolve(); self.config=config
    def capabilities(self):
        return {'read':True,'write':False,'freshness':'sha256','network':False}
    def resolve(self,reference):
        within(self.root,reference)
        return reference
    def read(self,reference):
        self.resolve(reference)
        if reference in ignored(self.root,[reference],bool(scope_info(self.root)['git_root'])):
            raise Fault('Ignored source excluded','blocked')
        raw,text=safe_read(self.root,reference,self.config)
        return Source(reference,digest(raw),text,'verified')
    def freshness(self,reference,revision):
        try: return 'verified' if self.read(reference).revision==revision else 'stale'
        except (Fault,OSError): return 'unknown'
