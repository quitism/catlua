import json
import sys
import random
import string
from pathlib import Path

_schema_path = Path(__file__).parent / "schema.json"
with open(_schema_path, "r", encoding="utf-8") as _f:
    _schema_data = json.load(_f)

SCHEMA = _schema_data["actions"]
EVENT_SCHEMA = _schema_data["events"]

CWIR_VERSION = "1.0"

BLOCK_OPENERS = {
    "IF_EQ", "IF_NEQ", "IF_GT", "IF_GTE", "IF_LT", "IF_LTE",
    "IF_CONTAINS", "IF_NOT_CONTAINS", "IF_EXISTS", "IF_NOT_EXISTS",
    "IF_AND", "IF_OR", "IF_NOR", "IF_XOR",
    "IF_DARK_THEME", "IF_MOUSE_LEFT", "IF_MOUSE_MIDDLE", "IF_MOUSE_RIGHT",
    "IF_KEY_DOWN", "IF_IS_ANCESTOR", "IF_IS_CHILD", "IF_IS_DESCENDANT",
    "REPEAT", "REPEAT_FOREVER",
    "TABLE_ITER",
}

BLOCK_CLOSERS = {"END_IF", "END_REPEAT", "END_ITER"}

CLOSER_MAP = {
    "END_IF":     ("IF_EQ", "IF_NEQ", "IF_GT", "IF_GTE", "IF_LT", "IF_LTE",
                   "IF_CONTAINS", "IF_NOT_CONTAINS", "IF_EXISTS", "IF_NOT_EXISTS",
                   "IF_AND", "IF_OR", "IF_NOR", "IF_XOR",
                   "IF_DARK_THEME", "IF_MOUSE_LEFT", "IF_MOUSE_MIDDLE", "IF_MOUSE_RIGHT",
                   "IF_KEY_DOWN", "IF_IS_ANCESTOR", "IF_IS_CHILD", "IF_IS_DESCENDANT"),
    "END_REPEAT": ("REPEAT", "REPEAT_FOREVER"),
    "END_ITER":   ("TABLE_ITER",),
}

class EmitError(Exception):
    def __init__(self, msg, line=None):
        self.line = line
        super().__init__(f"line {line}: {msg}" if line else msg)


class GlobalIDGen:
    def __init__(self):
        self._used = set()
        self._chars = string.ascii_letters + string.digits + "!@#$%^&*"

    def next(self):
        while True:
            gid = "".join(random.choices(self._chars, k=2))
            if gid not in self._used:
                self._used.add(gid)
                return gid


def tokenize_line(line):
    tokens = []
    i = 0
    while i < len(line):
        if line[i] == " ":
            i += 1
            continue
        if line[i] == '"':
            j = i + 1
            while j < len(line) and line[j] != '"':
                if line[j] == '\\':
                    j += 1
                j += 1
            if j >= len(line):
                raise EmitError(f"unterminated string: {line}")
            tokens.append(("STRING", line[i+1:j]))
            i = j + 1
            continue
        if line[i] == '(':
            j = line.index(')', i)
            tokens.append(("OBJECT", line[i+1:j]))
            i = j + 1
            continue
        if line[i] == '[':
            j = line.index(']', i)
            inner = line[i+1:j].strip()
            args = []
            if inner:
                sub = tokenize_line(inner)
                for t, v in sub:
                    args.append((t, v))
            tokens.append(("TUPLE", args))
            i = j + 1
            continue
        j = i
        while j < len(line) and line[j] not in (' ', '"', '(', '['):
            j += 1
        word = line[i:j]
        if word:
            tokens.append(("WORD", word))
        i = j
    return tokens


def parse_line(raw_line, lineno):
    line = raw_line.strip()
    if not line or line.startswith(";;"):
        return None
    tokens = tokenize_line(line)
    if not tokens:
        return None
    kind, val = tokens[0]
    if kind != "WORD":
        raise EmitError(f"expected opcode, got {val!r}", lineno)
    return val, tokens[1:]


def resolve_value(token):
    kind, val = token
    if kind == "WORD" and val == "EMPTY":
        return None
    if kind in ("STRING", "OBJECT"):
        return val
    raise EmitError(f"unexpected token type {kind!r} with value {val!r}")


def build_action(opcode, args, gid, lineno):
    if opcode in BLOCK_CLOSERS:
        return {"id": "25", "text": ["end"], "globalid": gid}
    if opcode == "ELSE":
        return {"id": "112", "text": ["else"], "globalid": gid}
    if opcode == "BREAK":
        return {"id": "24", "text": ["Break"], "globalid": gid}
    if opcode not in SCHEMA:
        raise EmitError(f"unknown opcode {opcode!r}", lineno)

    schema_entry = SCHEMA[opcode]
    text_out = []
    arg_idx = 0

    for slot in schema_entry["text"]:
        if isinstance(slot, str):
            text_out.append(slot)
            continue
        param = dict(slot)
        if param.get("t") == "tuple":
            if arg_idx >= len(args):
                raise EmitError(f"{opcode}: missing tuple arg", lineno)
            kind, tup_args = args[arg_idx]
            arg_idx += 1
            if kind != "TUPLE":
                raise EmitError(f"{opcode}: expected tuple [...], got {kind!r}", lineno)
            param["value"] = [
                {"t": "string", "l": "any", "value": v} if (v := resolve_value(t)) is not None
                else {"t": "string", "l": "any"}
                for t in tup_args
            ]
            text_out.append(param)
            continue
        if arg_idx >= len(args):
            raise EmitError(f"{opcode}: not enough args (slot {arg_idx})", lineno)
        value = resolve_value(args[arg_idx])
        arg_idx += 1
        if value is not None:
            param["value"] = value
        text_out.append(param)

    return {"id": schema_entry["id"], "text": text_out, "globalid": gid}


def build_event(event_type, event_args, actions, gid, x, y, lineno):
    if event_type not in EVENT_SCHEMA:
        raise EmitError(f"unknown event type {event_type!r}", lineno)

    schema = EVENT_SCHEMA[event_type]
    text_out = []
    arg_idx = 0

    for slot in schema["text"]:
        if isinstance(slot, str):
            text_out.append(slot)
            continue
        param = dict(slot)
        if arg_idx < len(event_args):
            value = resolve_value(event_args[arg_idx])
            arg_idx += 1
            if value is not None:
                param["value"] = value
        text_out.append(param)

    event = {
        "id": schema["id"],
        "text": text_out,
        "x": str(x),
        "y": str(y),
        "width": "350",
        "globalid": gid,
        "actions": actions,
    }

    if event_type == "FUNC_DEF":
        overrides = []
        if arg_idx < len(event_args):
            kind, tup_args = event_args[arg_idx]
            if kind == "TUPLE":
                for targ in tup_args:
                    v = resolve_value(targ)
                    overrides.append({"value": v} if v is not None else {"value": ""})
        event["variable_overrides"] = overrides

    return event


def check_version(file_version):
    try:
        fmaj, fmin = map(int, file_version.split("."))
        emaj, emin = map(int, CWIR_VERSION.split("."))
    except ValueError:
        print(f"warning: could not parse version {file_version!r}, proceeding anyway")
        return
    if fmaj > emaj:
        raise EmitError(
            f"version mismatch: file is CWIR {file_version}, emitter supports {CWIR_VERSION} — major bump, aborting"
        )
    if fmaj == emaj and fmin > emin:
        print(f"warning: file is CWIR {file_version}, emitter is {CWIR_VERSION} — some opcodes may not be recognized")


def emit(source):
    lines = source.splitlines()
    if not lines:
        raise EmitError("empty source")

    first = lines[0].strip()
    if not first.startswith("CWIR_VERSION"):
        raise EmitError("missing CWIR_VERSION declaration on first line", 1)

    vtokens = tokenize_line(first)
    if len(vtokens) >= 2:
        check_version(vtokens[1][1])

    gid_gen = GlobalIDGen()
    scripts = []
    flags = set()

    current_script_alias = None
    current_script_events = []
    in_script_block = False

    current_event_type = None
    current_event_args = None
    current_event_lineno = None
    current_actions = []
    block_stack = []

    x_cursor = 5000
    y_cursor = 5000
    event_gid = None

    def flush_event(lineno):
        nonlocal current_event_type, current_event_args, current_actions, event_gid, x_cursor
        if block_stack:
            raise EmitError(f"unclosed block {block_stack[-1]!r} at end of event", current_event_lineno)
        ev = build_event(
            current_event_type, current_event_args, current_actions,
            event_gid, x_cursor, y_cursor, current_event_lineno
        )
        current_script_events.append(ev)
        x_cursor += 400
        current_event_type = None
        current_event_args = None
        current_actions = []
        event_gid = None

    def flush_script():
        nonlocal current_script_alias, current_script_events, x_cursor
        script = {
            "class": "script",
            "globalid": gid_gen.next(),
            "content": current_script_events,
            "enabled": "true",
        }
        if current_script_alias:
            script["alias"] = current_script_alias
        scripts.append(script)
        current_script_alias = None
        current_script_events = []
        x_cursor = 5000

    for lineno, raw_line in enumerate(lines[1:], start=2):
        parsed = parse_line(raw_line, lineno)
        if parsed is None:
            continue

        opcode, args = parsed

        if opcode == "CWIR_VERSION":
            raise EmitError("CWIR_VERSION must only appear on line 1", lineno)

        if opcode == "FLAG":
            if not args:
                raise EmitError("FLAG requires a name", lineno)
            flag_name = args[0][1]
            if flag_name == "SINGLE_SCRIPT" and in_script_block:
                raise EmitError("FLAG SINGLE_SCRIPT cannot be used inside a SCRIPT block", lineno)
            flags.add(flag_name)
            continue

        if opcode == "SCRIPT":
            if "SINGLE_SCRIPT" in flags:
                raise EmitError("SCRIPT block not allowed when FLAG SINGLE_SCRIPT is set", lineno)
            if in_script_block:
                raise EmitError("nested SCRIPT blocks are not allowed", lineno)
            if current_event_type is not None:
                raise EmitError("SCRIPT declared inside an EVENT block", lineno)
            in_script_block = True
            x_cursor = 5000
            continue

        if opcode == "END_SCRIPT":
            if not in_script_block:
                raise EmitError("END_SCRIPT without SCRIPT", lineno)
            if current_event_type is not None:
                raise EmitError("END_SCRIPT inside an unclosed EVENT block", lineno)
            flush_script()
            in_script_block = False
            continue

        if opcode == "SCRIPT_ALIAS":
            if not args:
                raise EmitError("SCRIPT_ALIAS requires a string argument", lineno)
            current_script_alias = resolve_value(args[0])
            continue

        if opcode == "EVENT":
            if current_event_type is not None:
                raise EmitError("EVENT inside EVENT", lineno)
            if not args:
                raise EmitError("EVENT requires a type", lineno)
            current_event_type = args[0][1]
            current_event_args = args[1:]
            current_event_lineno = lineno
            event_gid = gid_gen.next()
            continue

        if opcode == "END_EVENT":
            if current_event_type is None:
                raise EmitError("END_EVENT without EVENT", lineno)
            flush_event(lineno)
            continue

        if current_event_type is None:
            raise EmitError(f"opcode {opcode!r} outside of EVENT block", lineno)

        if opcode in BLOCK_OPENERS:
            block_stack.append(opcode)

        if opcode in BLOCK_CLOSERS:
            if not block_stack:
                raise EmitError(f"{opcode} with no open block", lineno)
            opener = block_stack[-1]
            if opener not in CLOSER_MAP[opcode]:
                raise EmitError(f"{opcode} closes {opener!r} but expected one of {CLOSER_MAP[opcode]}", lineno)
            block_stack.pop()

        if opcode == "ELSE" and not block_stack:
            raise EmitError("ELSE with no open block", lineno)

        current_actions.append(build_action(opcode, args, gid_gen.next(), lineno))

    if current_event_type is not None:
        raise EmitError("unclosed EVENT block at end of file")
    if in_script_block:
        raise EmitError("unclosed SCRIPT block at end of file")

    if current_script_events or not scripts:
        flush_script()

    return json.dumps(scripts, indent=2, ensure_ascii=False)


def main():
    if len(sys.argv) < 2:
        print("usage: python emitter.py <input.cwobj> [output.json]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path.replace(".cwobj", ".json")

    with open(input_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        result = emit(source)
    except EmitError as e:
        print(f"error: {e}")
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"emitted → {output_path}")


if __name__ == "__main__":
    main()