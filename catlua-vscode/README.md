# CatLua extension

Adds CatLua support for CatWeb v2.16+ inside VS Code

## Features
- Recognizes `.catlua` files with grammar, language configuration, and snippets.
- Offers a completion list covering services (`LocalPlayer`, `Camera`, etc.), core functions (`print`, `warn`, `error`, `wait`, `playAudio`, `tween`), and keywords (`local`, `global`, `object`).
- Runs the CatLua compiler in lint mode, surfacing problems directly.

## Usage

1. Open or create files ending with `.catlua`; the extension activates automatically.
2. Write or edit scripts-syntax highlighting, snippets, and completions work right away.
3. Stop writing for 500ms to trigger the linting pass.

## Configuration

The extension exposes one setting:

| Setting | Description | Default |
| --- | --- | --- |
| `catlua.compilerPath` | Absolute path to `main.py` from the CatLua compiler; used whenever linting runs. | `E:\catlua\main.py` |

Update this path if your compiler lives somewhere else (workspaces or user settings).

## Snippets

Snippets are defined in the `snippets.json` file.