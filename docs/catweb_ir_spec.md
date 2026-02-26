# CatWeb IR (CWIR) ABI Specification
> Intermediate representation for CatWeb compiler tooling. Targets CatWeb v2.15.0.3+

**Spec version:** 1.0

---

## Overview

CWIR is a plain-text, line-oriented intermediate representation that sits between a frontend language (e.g. Luau-flavored syntax) and the CatWeb JSON emitter.

**Pipeline:**
```
source.catlua (or your own format) → [Frontend] → source.cwobj → [Emitter] → output.json
```

---

## File Format

- Plain UTF-8 text, extension `.cwobj`
- One statement per line
- Blank lines ignored
- Lines starting with `;;` are comments (stripped before parsing)
- Case-sensitive opcodes (uppercase by convention)
- First non-comment line MUST be a version declaration:

```
CWIR_VERSION 1.0
```

Tooling should reject or warn on version mismatches. Bump minor for new opcodes, major for breaking changes.

---

## Value Syntax

| Syntax | Meaning | Example |
|--------|---------|---------|
| `"..."` | String value or variable ref | `"hello"`, `"{counter}"` |
| `(Name)` | Static object reference (by globalid/alias) | `(MyButton)`, `(parent)` |
| `[...]` | Tuple / argument list | `["arg1" "{var}" "3"]` |
| `EMPTY` | Absent optional param | `EMPTY` |

**Rules:**
- Every user value is double-quoted, no exceptions
- Variable refs use CatWeb's native syntax inside quotes: `"{var}"`, `"{o!var}"`, `"{l!var}"`, `"{table.entry}"`
- Object variables (runtime) are quoted like any value: `"{myObjVar}"` — the emitter infers `t:"object"` from the schema
- Static object refs are always wrapped in `()`, never quoted: `(MyButton)`, `(parent)`
- Tuple args are space-separated inside `[]`
- `EMPTY` is always bare, never quoted — `"EMPTY"` is the literal string EMPTY
- Any input slot accepts `EMPTY`. If a required field receives `EMPTY`, CatWeb may error at runtime
- The emitter infers `t` and `l` from the schema, not from the IR

---

## Event Blocks

Events are top-level block declarations. All opcodes must live inside an event block.

```
EVENT <type> [param]
    ...opcodes...
END_EVENT
```

### Event Types

| Type | Params | Notes |
|------|--------|-------|
| `LOADED` | — | When website loaded |
| `PRESSED` | `(object)` | When button pressed |
| `RIGHT_CLICKED` | `(object)` | When button right clicked |
| `MOUSE_ENTER` | `(object)` | When mouse enters object |
| `MOUSE_LEAVE` | `(object)` | When mouse leaves object |
| `MOUSE_DOWN` | `(object)` | When mouse down on object |
| `MOUSE_UP` | `(object)` | When mouse up on object |
| `KEY_PRESSED` | `"key"` | When key pressed |
| `CHANGED` | `(object)` | When object changed |
| `DONATION` | `(object)` | When donation bought |
| `INPUT_SUBMIT` | `(object)` | When input submitted |
| `MSG_RECEIVED` | — | When message received (exposes `{l!messageContent}`, `{l!messageSenderId}`, `{l!messageSenderName}`) |
| `CROSSSITE_MSG` | — | When cross-site message received (exposes `{l!sourceDomain}`, `{l!messageContent}`, `{l!messageSenderId}`, `{l!messageSenderName}`) |
| `FUNC_DEF` | `"name"` `["arg1" ...]` | Define function (args become `{l!argN}`) |

**Example:**
```
EVENT LOADED
    LOG "hello world"
END_EVENT

EVENT PRESSED (SubmitBtn)
    VAR_SET "clicked" "true"
END_EVENT

EVENT FUNC_DEF "greet" ["username"]
    VAR_SET "msg" "hello {l!username}"
    RETURN "{msg}"
END_EVENT
```

> **Note:** `FUNC_DEF` args map to `variable_overrides` in the emitted JSON, max 6.

---

## Block Control

Block opcodes open/close a scope. The emitter maintains a stack to emit matching `end` actions.

```
IF_EQ "a" "b"
    ...
ELSE
    ...
END_IF

REPEAT "10"
    ...
END_REPEAT

REPEAT_FOREVER
    ...
END_REPEAT

TABLE_ITER "myTable"
    ;; {l!index} and {l!value} available here
END_ITER
```

**Rules:**
- Every opener needs exactly one `END_*`
- `ELSE` is optional inside `IF_*` blocks
- `ELSE` does NOT get its own `END` - `END_IF` closes everything
- `BREAK` is valid inside `REPEAT` / `REPEAT_FOREVER` only
- Block openers that are also conditionals (`IF_DARK_THEME`, `IF_MOUSE_*`, `IF_KEY_DOWN`) follow the same `END_IF` pattern

---

## Opcodes Reference

### Console

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `LOG "value"` | any | 0 |
| `WARN "value"` | any | 1 |
| `ERROR "value"` | any | 2 |

---

### Logic / Conditionals

All conditionals open a block, closed with `END_IF`.

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `IF_EQ "a" "b"` | any, any | 18 |
| `IF_NEQ "a" "b"` | any, any | 19 |
| `IF_GT "a" "b"` | any, any | 20 |
| `IF_GTE "a" "b"` | any, any | 125 |
| `IF_LT "a" "b"` | any, any | 21 |
| `IF_LTE "a" "b"` | any, any | 126 |
| `IF_CONTAINS "a" "b"` | string, string | 37 |
| `IF_NOT_CONTAINS "a" "b"` | string, string | 38 |
| `IF_EXISTS "varname"` | variable | 92 |
| `IF_NOT_EXISTS "varname"` | variable | 93 |
| `IF_AND "varA" "varB"` | variable, variable | 44 |
| `IF_OR "varA" "varB"` | variable, variable | 45 |
| `IF_NOR "varA" "varB"` | variable, variable | 46 |
| `IF_XOR "varA" "varB"` | variable, variable | 47 |
| `IF_DARK_THEME` | — | 108 |
| `IF_MOUSE_LEFT` | — | 79 |
| `IF_MOUSE_MIDDLE` | — | 80 |
| `IF_MOUSE_RIGHT` | — | 81 |
| `IF_KEY_DOWN "key"` | key | 82 |
| `IF_IS_ANCESTOR (obj) (obj)` | object, object | 103 |
| `IF_IS_CHILD (obj) (obj)` | object, object | 104 |
| `IF_IS_DESCENDANT (obj) (obj)` | object, object | 105 |
| `ELSE` | — | 112 |
| `END_IF` | — | 25 |

---

### Loops

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `REPEAT "n"` | number | 22 |
| `REPEAT_FOREVER` | — | 23 |
| `BREAK` | — | 24 |
| `END_REPEAT` | — | 25 |

---

### Wait

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `WAIT "seconds"` | number | 3 |

---

### Variables & Math

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `VAR_SET "name" "value"` | variable, any | 11 |
| `VAR_INC "name" "amount"` | variable, number | 12 |
| `VAR_DEC "name" "amount"` | variable, number | 13 |
| `VAR_MUL "name" "amount"` | variable, number | 14 |
| `VAR_DIV "name" "amount"` | variable, number | 15 |
| `VAR_POW "name" "exp"` | variable, number | 40 |
| `VAR_MOD "name" "divisor"` | variable, number | 41 |
| `VAR_ROUND "name"` | variable | 16 |
| `VAR_FLOOR "name"` | variable | 17 |
| `VAR_CEIL "name"` | variable | 78 |
| `VAR_RANDOM "name" "min" "max"` | var, number, number | 27 |
| `VAR_DEL "name"` | variable | 96 |
| `MATH_RUN "function" ["args"] "outvar"` | function, tuple, variable | 114 |

---

### Looks

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `LOOK_HIDE (obj)` | object | 8 |
| `LOOK_SHOW (obj)` | object | 9 |
| `LOOK_SET_TEXT (obj) "text"` | object, string | 10 |
| `LOOK_SET_IMG (obj) "assetId"` | object, id | 106 |
| `LOOK_SET_AVATAR (obj) "userId" "resolution"` | object, userid, string? | 107 |
| `LOOK_SET_PROP "property" (obj) "value"` | property, object, any | 31 |
| `LOOK_GET_PROP "property" (obj) "outvar"` | property, object, variable | 39 |
| `LOOK_TWEEN "property" (obj) "value" "time" "style" "direction"` | property, object, any, number, string, string | 88 |
| `LOOK_DUPLICATE (obj) "outvar"` | object, variable | 49 |
| `LOOK_DELETE (obj)` | object | 50 |
| `LOOK_GET_AT_POS "x" "y" "outarray"` | string, string, array | 127 |
| `LOOK_GET_ASSET_INFO "info" "assetId" "outvar"` | string, string, variable | 129 |

---

### Hierarchy

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `HIER_PARENT (obj) (parent)` | object, object | 58 |
| `HIER_GET_PARENT (obj) "outvar"` | object, variable | 97 |
| `HIER_FIND_CHILD "name" (obj) "outvar"` | string, object, variable | 99 |
| `HIER_FIND_ANCESTOR "name" (obj) "outvar"` | string, object, variable | 98 |
| `HIER_FIND_DESCENDANT "name" (obj) "outvar"` | string, object, variable | 100 |
| `HIER_GET_CHILDREN (obj) "outtable"` | object, table | 101 |
| `HIER_GET_DESCENDANTS (obj) "outtable"` | object, table | 102 |

---

### Input

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `INPUT_GET_TEXT (obj) "outvar"` | object(input), variable | 30 |
| `INPUT_GET_CURSOR "outx" "outy"` | variable, variable | 85 |
| `INPUT_GET_VIEWPORT "outx" "outy"` | variable, variable | 84 |

---

### Navigation

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `NAV_REDIRECT "url"` | string(href) | 4 |
| `NAV_GET_URL "outvar"` | variable | 117 |
| `NAV_GET_QUERY "param" "outvar"` | string, variable | 67 |

---

### Audio

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `AUDIO_PLAY "assetId" "outvar"` | id, variable? | 5 |
| `AUDIO_PLAY_LOOP "assetId" "outvar"` | id, variable? | 26 |
| `AUDIO_STOP_ALL` | — | 7 |
| `AUDIO_STOP "audiovar"` | variable | 74 |
| `AUDIO_PAUSE "audiovar"` | variable | 75 |
| `AUDIO_RESUME "audiovar"` | variable | 76 |
| `AUDIO_SET_VOL "audiovar" "volume"` | variable, number | 73 |
| `AUDIO_SET_SPEED "audiovar" "speed"` | variable, number | 77 |

---

### Network

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `NET_BROADCAST_PAGE "message"` | string | 32 |
| `NET_BROADCAST_SITE "message"` | string | 33 |
| `NET_BROADCAST_CROSSSITE "message" "page"` | string, string(href) | 130 |

---

### User

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `USER_GET_NAME "outvar"` | variable | 51 |
| `USER_GET_DISPLAY "outvar"` | variable | 53 |
| `USER_GET_ID "outvar"` | variable | 52 |

---

### Time

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `TIME_GET_UNIX "outvar"` | variable | 68 |
| `TIME_GET_SERVER_UNIX "outvar"` | variable | 116 |
| `TIME_GET_TICK "outvar"` | variable | 83 |
| `TIME_GET_TIMEZONE "outvar"` | variable | 118 |
| `TIME_FORMAT_NOW "format" "outvar"` | string, variable | 71 |
| `TIME_FORMAT_UNIX "timestamp" "format" "outvar"` | number, string, variable | 72 |

---

### Color

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `COLOR_HEX_TO_RGB "hex" "outvar"` | hex, variable | 119 |
| `COLOR_HEX_TO_HSV "hex" "outvar"` | hex, variable | 120 |
| `COLOR_RGB_TO_HEX "rgb" "outvar"` | RGB, variable | 121 |
| `COLOR_HSV_TO_HEX "hsv" "outvar"` | HSV, variable | 122 |
| `COLOR_LERP "hexA" "hexB" "alpha" "outvar"` | hex, hex, number, variable | 123 |

---

### Strings

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `STR_LEN "value" "outvar"` | string, variable | 48 |
| `STR_SPLIT "value" "sep" "outtable"` | string, string, table | 57 |
| `STR_LOWER "value" "outvar"` | string, variable | 69 |
| `STR_UPPER "value" "outvar"` | string, variable | 70 |
| `STR_CONCAT "a" "b" "outvar"` | string, string, variable | 109 |
| `STR_SUB "varname" "start" "end"` | variable, number, number | 42 |
| `STR_REPLACE "find" "varname" "replacement"` | string, variable, string | 43 |

---

### Tables

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `TABLE_CREATE "name"` | table | 54 |
| `TABLE_SET "entry" "table" "value"` | entry, table, any | 55 |
| `TABLE_SET_OBJ "entry" "table" (obj)` | entry, table, object | 66 |
| `TABLE_GET "entry" "table" "outvar"` | entry, table, variable | 56 |
| `TABLE_DEL "entry" "table"` | entry, table | 90 |
| `TABLE_LEN "array" "outvar"` | array, variable | 59 |
| `TABLE_INSERT "value" "pos" "array"` | any, number?, array | 89 |
| `TABLE_REMOVE "pos" "array"` | number?, array | 91 |
| `TABLE_JOIN "array" "sep" "outvar"` | array, string, variable | 110 |
| `TABLE_ITER "table"` | table | 113 |
| `END_ITER` | — | 25 |

> **Note:** `TABLE_INSERT` and `TABLE_REMOVE` accept `EMPTY` for the position arg to insert/remove at end. Like all slots, any input accepts `EMPTY` — behavior depends on CatWeb at runtime.

> **Warning:** Setting index `"1"` permanently converts a table to an array. Key-value pairs cannot be added after. Plan structure before compiling.

---

### Audio Variable Properties (id 94/95)

These act on audio variables stored from `AUDIO_PLAY` / `AUDIO_PLAY_LOOP`.

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `AVAR_SET "property" "audiovar" "value"` | property, variable, any | 94 |
| `AVAR_GET "property" "audiovar" "outvar"` | property, variable, variable | 95 |

---

### Functions

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `FUNC_RUN "name" ["args"] "outvar"` | function, tuple, variable? | 87 |
| `FUNC_RUN_BG "name" ["args"]` | function, tuple | 63 |
| `FUNC_RUN_PROTECTED "name" ["args"] "successvar" "outvar"` | function, tuple, variable?, variable? | 128 |
| `RETURN "value"` | any | 115 |

> `outvar` and `successvar` accept `EMPTY` like any other slot.

---

### Cookies *(requires Cookies gamepass)*

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `COOKIE_SET "name" "value"` | cookie, any | 34 |
| `COOKIE_INC "name" "amount"` | cookie, number | 35 |
| `COOKIE_DEL "name"` | cookie | 62 |
| `COOKIE_GET "name" "outvar"` | cookie, variable | 36 |

---

### Comments

| Opcode | Inputs | CatWeb ID |
|--------|--------|-----------|
| `COMMENT "text"` | string | 124 |

> Emits a CatWeb comment block (id 124). `help` field is intentionally not exposed in the IR.

---

## Complete Example

```
EVENT LOADED
    TABLE_CREATE "scores"
    VAR_SET "i" "0"
    REPEAT "5"
        VAR_INC "i" "1"
        TABLE_SET "{i}" "scores" "{i}"
    END_REPEAT
    FUNC_RUN "printScores" ["{scores}"] EMPTY
END_EVENT

EVENT FUNC_DEF "printScores" ["tbl"]
    TABLE_ITER "{l!tbl}"
        LOG "{l!value}"
    END_ITER
    RETURN EMPTY
END_EVENT
```

---

## Known Roadblocks & Notes

**`EMPTY` behavior** - any input slot accepts `EMPTY`. the emitter should emit an absent `value` field (no `"value"` key at all) for `EMPTY`, never emit `{"value": "EMPTY", ...}`.

**`TABLE_SET_OBJ` exists as a separate opcode** because the schema for id 66 uses `t:"object"` for the value slot while id 55 uses `t:"string"`. they look identical in source but emit differently - the emitter can't infer which to use without the separate opcode.

**`FUNC_DEF` args max 6** - frontend should error if more than 6 args are declared. maps to `variable_overrides` in emitted JSON.

**`ELSE` stack behavior** - the nesting stack must treat `ELSE` as a mid-block token, not a new frame. `END_IF` pops the frame opened by the `IF_*`, not a frame opened by `ELSE`.

**Tuple `[]` in no-arg calls** - when a function takes no args, emit an empty tuple `[]`. the emitter should still produce `{"t":"tuple","value":[]}` not omit the tuple entirely.

**`assetbrowser` and `href` metadata** - these are invisible in the IR but required in emitted JSON for specific opcodes. the emitter schema table must attach them automatically. the IR author never needs to think about them.
