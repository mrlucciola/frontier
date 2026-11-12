from pathlib import Path
from .common import read_json, Fault, DOMAINS
from .contracts import CONFIG, validate

DEFAULTS={"schema_version":"cwf/v1","mode":"active","domains":DOMAINS[:],
          "exclusions":[],"source_roots":[],"cache_days":30,"observation_days":90,
          "limits":{"max_files":10000,"max_bytes":100*1024*1024,"file_bytes":1024*1024,
                    "seconds":10,"max_findings":8,"packet_bytes":8000}}


def settings(home, root=None, override=None):
    import copy
    config=copy.deepcopy(DEFAULTS)
    layers=[Path(home)/".config/cwf/config.json"]
    if root:
        layers.append(Path(root)/".cwf.json")
    for i,path in enumerate(layers):
        if i and config["mode"]=="off":
            break
        if not path.exists() and not path.is_symlink():
            continue
        data=validate(read_json(path),CONFIG)
        if i and config["mode"]=="off":
            continue
        for key,value in data.items():
            if key=="limits":
                for k,v in value.items():
                    config[key][k]=min(config[key][k],v) if i else v
            elif key=="source_roots":
                from .common import within
                normalized=[]
                for source in value:
                    if not source or Path(source).is_absolute() or ".." in Path(source).parts:
                        raise Fault("Source roots must be relative to selected scope","blocked")
                    normalized.append(Path(source).as_posix())
                prior=config[key]
                if i and prior and normalized:
                    common=[]
                    for a in prior:
                        for b in normalized:
                            if a==b or a=="." or b.startswith(a+"/"): common.append(b)
                            elif b=="." or a.startswith(b+"/"): common.append(a)
                    if not common: raise Fault("Scope source roots do not intersect personal allowed roots","blocked")
                    config[key]=sorted(set(common))
                elif normalized: config[key]=sorted(set(normalized))
            elif key=="exclusions":
                config[key]=sorted(set(config[key]+value))
            elif key=="domains" and i:
                config[key]=[v for v in config[key] if v in value]
            elif key=="mode" and i and config[key]=="advisory" and value=="active":
                pass
            else:
                config[key]=value
    if override:
        # Explicit invocation can lower scan limits, not enlarge source permissions.
        from .contracts import LIMITS
        validate(override,LIMITS)
        config["limits"].update(override)
    for source in config["source_roots"]:
        if Path(source).is_absolute() or ".." in Path(source).parts:
            raise Fault("Configured source roots must stay relative to selected scope", "blocked")
    return config
