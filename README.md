# CatLua

A full front-to-back compiler toolchain and VS Code Language Server for **CatWeb** (v2.16+). Write your CatWeb scripts in a clean, Luau-flavored syntax and compile them directly into CatWeb-ready JSON files.

## Features

* **Custom Compiler Pipeline:** Lexing, parsing, semantic analysis, and IR emission built from scratch.
* **Optimizer:** Features constant folding and Dead Code Elimination (DCE) via `-O1` and `-O2` flags so your scripts are optimized in action counts.
* **VS Code Extension:** Real-time linting, rich auto-complete menus for CatWeb services, and full syntax highlighting.
* **Scope Tracking:** Explicit tracking for `local` (`l!`), `global` (`g!`), and `object` (`o!`) variables.
* **Annotations:** Use `--#type audio` (`--@ type=audio`) or `--@ builtin` to force specific CatWeb routing (like `AVAR_SET` vs `LOOK_SET_PROP`).
* **Multi-File Linker:** Organize massive projects using `require("file.catlua")`.
* **Safety:** Automatically warns you if you hit the CatWeb 120-action limit per event.

## Usage

### The Compiler

1. Clone this repository
2. Ensure you have Python installed
3. Run the compiler via CLI:

```bash
python main.py <file.catlua> [-o output.json] [--ir] [-O0|-O1|-O2]

```

### VS Code Extension

1. Grab the `.vsix` file inside the Releases tab, or build the extension yourself
2. Go to your VS Code Settings and search for `CatLua`
3. Set the `Compiler Path` to the absolute path of your `main.py` file

## Syntax Examples

**Basic Scopes and Services**

```lua
OnWebsiteLoaded
    local myVar = 10
    object myObjVar = "hello"
    
    -- emits USER_GET_NAME
    local name = LocalPlayer.Name
    print(`welcome {name}!`)
end

```

**Annotations**

```lua
--#type audio
mySong.Volume = 8
mySong.PlaybackSpeed = 1.2
--#type

-- the compiler knows this is an object and emits TABLE_SET_OBJ
myTable["btn"] = (MenuButton)

```

**Method Desugaring**

```lua
-- compiles down perfectly to IF_IS_ANCESTOR and IF_CONTAINS
if ancestor:IsAncestorOf(child) then
    if myString:find("hello") then
        print("found it!")
    end
end

```
