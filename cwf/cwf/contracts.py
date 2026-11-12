"""Published schemas and a deliberately small standard-library validator.

Only constructs used by these schemas are supported; tests cross-check jsonschema.
"""
from .common import Fault, DOMAINS


def obj(props, required=()):
    return {"type": "object", "properties": props, "required": list(required),
            "additionalProperties": False}


def arr(items, maximum=1000):
    return {"type": "array", "items": items, "maxItems": maximum}


S = {"type": "string", "maxLength": 8000}
SHORT = {"type": "string", "minLength": 1, "maxLength": 256}
ID = {"type": "string", "pattern": r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$"}
HASH = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
N = {"type": "integer", "minimum": 0}
B = {"type": "boolean"}
STRINGS = arr(S)
MODE = {"enum": ["active", "advisory", "off"]}
VER = {"const": "cwf/v1"}
SOURCE = obj({"path": SHORT, "content_hash": HASH, "locator": S,
              "revision": S, "freshness": {"enum": ["verified", "unknown", "stale"]}},
             ["path", "content_hash"])
LIMITS = obj({"max_files": {"type": "integer", "minimum": 1, "maximum": 100000},
              "max_bytes": {"type": "integer", "minimum": 100, "maximum": 1073741824},
              "file_bytes": {"type": "integer", "minimum": 100, "maximum": 10485760},
              "seconds": {"type": "number", "minimum": 0.01, "maximum": 120},
              "max_findings": {"type": "integer", "minimum": 1, "maximum": 40},
              "packet_bytes": {"type": "integer", "minimum": 1000, "maximum": 32000}})
CONFIG = obj({"schema_version": VER, "mode": MODE,
              "domains": arr({"enum": DOMAINS}, 6), "exclusions": STRINGS,
              "source_roots": STRINGS, "limits": LIMITS,
              "cache_days": N, "observation_days": N}, ["schema_version"])
TASK = obj({"schema_version": VER, "id": ID, "outcome": SHORT,
            "domains": arr({"enum": DOMAINS}, 6), "scope_root": SHORT,
            "status": {"enum": ["proposed", "ready", "running", "blocked", "verifying", "complete", "abandoned"]},
            "constraints": STRINGS, "acceptance": arr(SHORT),
            "sources": arr(SOURCE), "assumptions": STRINGS,
            "progress": STRINGS, "changed_paths": STRINGS,
            "blockers": STRINGS, "next_action": S,
            "evidence": arr(obj({"criterion": SHORT, "source": SHORT}, ["criterion", "source"])),
            "waivers": arr(obj({"criterion": SHORT, "accepted_by": SHORT, "source": SHORT},
                              ["criterion", "accepted_by", "source"])),
            "framework_version": SHORT}, ["schema_version", "id", "outcome", "scope_root", "status", "acceptance"])
OBSERVATION = obj({"schema_version": VER, "id": ID, "statement": S,
                   "claim_status": {"enum": ["observed", "inferred", "accepted"]},
                   "sources": arr(SOURCE, 30), "accepted_by": SHORT,
                   "acceptance_source": SHORT, "supersedes": ID},
                  ["schema_version", "id", "statement", "claim_status", "sources"])
ITEM = obj({"id": ID, "outcome": SHORT, "depends_on": arr(ID),
            "writes": STRINGS, "resources": STRINGS, "acceptance": arr(SHORT)},
           ["id", "outcome", "depends_on", "writes", "acceptance"])
BATCH = obj({"schema_version": VER, "id": ID, "integration_owner": ID,
             "items": arr(ITEM), "acceptance": arr(SHORT)},
            ["schema_version", "id", "integration_owner", "items", "acceptance"])
CHECK = obj({"id": ID, "kind": {"enum": ["absent_literal", "command"]},
             "paths": STRINGS, "literal": SHORT, "argv": arr(SHORT, 100),
             "timeout": {"type": "number", "minimum": 0.1, "maximum": 600},
             "expected_exit": {"type": "integer"}, "required": B,
             "authorization": SHORT}, ["id", "kind", "required"])
FINDING = obj({"source_ref": SHORT, "locator": S, "content_hash": HASH,
               "kind": SHORT, "claim_status": {"enum": ["observed", "inferred", "accepted"]},
               "rank_reason": S, "excerpt": S},
              ["source_ref", "locator", "content_hash", "kind", "claim_status", "rank_reason"])
PACKET = obj({"schema_version": VER, "packet_id": ID, "scope_id": SHORT,
              "worktree_id": SHORT, "domain": {"enum": DOMAINS}, "query": S,
              "generated_at": SHORT, "tool_version": SHORT,
              "config_digest": HASH, "snapshot_digest": HASH,
              "findings": arr(FINDING, 40), "conflicts": STRINGS,
              "coverage": obj({"root": S, "files": N, "bytes": N,
                 "excluded": N, "exclusion_reasons": {"type": "object"},
                 "omitted_results": N, "limits_hit": STRINGS, "read_failures": N,
                 "manifest_stable": B, "semantic_completeness": {"const": False}},
                 ["root", "files", "bytes", "excluded", "exclusion_reasons", "omitted_results",
                  "limits_hit", "read_failures", "manifest_stable", "semantic_completeness"]),
              "status": {"enum": ["complete_within_scope", "partial", "stale", "unavailable"]},
              "persistence": SHORT, "cache": SHORT},
             ["schema_version", "packet_id", "scope_id", "worktree_id", "domain", "query",
              "generated_at", "tool_version", "config_digest", "snapshot_digest", "findings",
              "conflicts", "coverage", "status", "persistence", "cache"])
SCHEMAS = {"config": CONFIG, "task": TASK, "observation": OBSERVATION,
           "batch": BATCH, "check": CHECK, "packet": PACKET}


def validate(value, schema, where="$"):
    import re
    if "const" in schema and value != schema["const"]:
        raise Fault(f"{where}: unexpected constant")
    if "enum" in schema and value not in schema["enum"]:
        raise Fault(f"{where}: unsupported value")
    t = schema.get("type")
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list),
             "string": isinstance(value, str), "boolean": isinstance(value, bool),
             "integer": isinstance(value, int) and not isinstance(value, bool),
             "number": isinstance(value, (int, float)) and not isinstance(value, bool)}
    if t and not valid[t]:
        raise Fault(f"{where}: expected {t}")
    if t == "object":
        for k in schema.get("required", []):
            if k not in value:
                raise Fault(f"{where}: missing {k}")
        props = schema.get("properties", {})
        for k, v in value.items():
            if k not in props and schema.get("additionalProperties") is False:
                raise Fault(f"{where}: unknown field {k}")
            if k in props:
                validate(v, props[k], f"{where}.{k}")
    elif t == "array":
        if len(value) > schema.get("maxItems", 100000):
            raise Fault(f"{where}: too many items")
        for i, v in enumerate(value):
            validate(v, schema["items"], f"{where}[{i}]")
    elif t == "string":
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 1000000):
            raise Fault(f"{where}: invalid length")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise Fault(f"{where}: invalid format")
    elif t in ("integer", "number"):
        import math
        if not math.isfinite(value) or not schema.get("minimum", -float("inf")) <= value <= schema.get("maximum", float("inf")):
            raise Fault(f"{where}: out of range")
    return value
