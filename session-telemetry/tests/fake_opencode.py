"""Fixture stand-in for the opencode CLI: fake_opencode.py STATE_FILE <real argv...>.

The JSON state file is the whole world: `sessions` (id -> {info, messages}), the scripted
`next_turn` that `run` applies, and the `calls` / `runs` this process recorded.

next_turn keys (all optional):
  messages      scripted messages appended after the user message that echoes the prompt
  echo_prompt   false drops that user message
  add_tokens    schema-shaped TokenUsage added to the session's cumulative tokens
  add_cost      number added to the session's cumulative cost
  set_info      shallow-merged onto Session.Info last (outcome, absolute totals, ...)
  skip_create   true leaves the session uncreated
  stdout        raw lines printed on stdout (a dict is printed as one JSON line)
  exit_code     process exit code
  sleep         seconds to sleep after the state is saved, before any output
Other state keys: page_size (server page cap), endless (message list never ends),
permissions (session.permission.list data), api_override ({operation: {stdout, code}}).
"""
import json
import os
import sys
import time

KINDS = ("input", "output", "reasoning")


def save(path, state):
    with open(path + ".part", "w") as handle:
        json.dump(state, handle)
    os.replace(path + ".part", path)


def params_of(args):
    found = {}
    for index, arg in enumerate(args):
        if arg == "--param":
            key, _, value = args[index + 1].partition("=")
            found[key] = value
    return found


def not_found(session_id):
    print(json.dumps({"_tag": "SessionNotFoundError", "sessionID": session_id,
                      "message": f"Session not found: {session_id}"}))
    sys.stderr.write("HTTP 404 Not Found\n")
    sys.exit(1)


def api(state, args):
    operation, params = args[2], params_of(args[3:])
    override = state.get("api_override", {}).get(operation)
    if override:
        sys.stdout.write(override["stdout"])
        sys.exit(override.get("code", 0))
    session = state["sessions"].get(params.get("sessionID"))
    if session is None:
        not_found(params.get("sessionID"))
    if operation == "session.get":
        print(json.dumps({"data": session["info"]}))
    elif operation == "session.permission.list":
        print(json.dumps({"data": state.get("permissions", [])}))
    elif operation == "session.message.list":
        messages = session["messages"]
        limit = int(params["limit"])
        size = min(limit, state.get("page_size") or limit)
        start = int(params.get("cursor", 0))
        end = start + size
        following = str(end) if end < len(messages) or state.get("endless") else None
        print(json.dumps({"data": messages[start:end], "cursor": {"previous": None, "next": following}}))
    else:
        sys.stderr.write(f"unknown operation {operation}\n")
        sys.exit(2)


def new_session(session_id, model, agent):
    ref = {"id": "fixture-model", "providerID": "fixture"}
    if model:
        provider, _, rest = model.partition("/")
        name, _, variant = rest.partition("#")
        ref = {"id": name, "providerID": provider, **({"variant": variant} if variant else {})}
    zero = {"input": 0, "output": 0, "reasoning": 0, "cache": {"read": 0, "write": 0}}
    return {"info": {"id": session_id, "projectID": "prj_fixture", "agent": agent or "build",
                     "model": ref, "cost": 0, "tokens": zero, "time": {"created": 1, "updated": 1},
                     "location": {"directory": "/fixture/work"}},
            "messages": []}


def run(state, args, path):
    rest, flags, prompt = args[1:], {}, None
    index = 0
    while index < len(rest):
        if rest[index] == "--standalone":
            index += 1
        elif rest[index] in ("--format", "--session", "--model", "--agent"):
            flags[rest[index]] = rest[index + 1]
            index += 2
        else:
            prompt = rest[index]
            index += 1
    turn = state.get("next_turn", {})
    state.setdefault("runs", []).append({"argv": args, "pid": os.getpid()})
    session_id = flags["--session"]
    if not turn.get("skip_create"):
        session = state["sessions"].setdefault(session_id, new_session(session_id, flags.get("--model"), flags.get("--agent")))
        info = session["info"]
        if turn.get("echo_prompt", True):
            session["messages"].append({"id": f"msg_user_{len(session['messages']):03d}",
                                        "type": "user", "time": {"created": 1}, "text": prompt})
        session["messages"].extend(turn.get("messages", []))
        extra = turn.get("add_tokens", {})
        for kind in KINDS:
            info["tokens"][kind] += extra.get(kind, 0)
        for kind in ("read", "write"):
            info["tokens"]["cache"][kind] += extra.get("cache", {}).get(kind, 0)
        info["cost"] += turn.get("add_cost", 0)
        info.update(turn.get("set_info", {}))
    save(path, state)
    if turn.get("sleep"):
        time.sleep(turn["sleep"])
    for line in turn.get("stdout", []):
        print(json.dumps(line) if isinstance(line, dict) else line)
    sys.stderr.write("fixture stderr\n")
    sys.exit(turn.get("exit_code", 0))


def main():
    path, args = sys.argv[1], sys.argv[2:]
    with open(path) as handle:
        state = json.load(handle)
    state.setdefault("calls", []).append(args)
    save(path, state)
    if args[:1] == ["--version"]:
        print("opencode v0.0.0-fixture")
    elif args[:2] == ["debug", "paths"]:
        for key in ("home", "data", "cache", "config", "state", "db"):
            print(f"{key:<10} /fixture/{key}")
    elif args[:2] == ["debug", "config"]:
        print("config-sources: fixture")
    elif args[:2] == ["api", "--standalone"]:
        api(state, args)
    elif args[:1] == ["run"]:
        run(state, args, path)
    else:
        sys.stderr.write(f"unsupported: {args}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
