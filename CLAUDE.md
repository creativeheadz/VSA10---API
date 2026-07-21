# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the tool

```bash
python main.py                              # interactive navigator
python main.py <folder>/<script_name> [args] # run a single script directly
```

There is no `requirements.txt`. Runtime deps are `slumber` and `python-dotenv` (the latter is auto-installed by `main.py` if missing). Credentials live in `.env` at the repo root (`ENDPOINT`, `TOKEN_ID`, `TOKEN_SECRET`) — `main.py` will prompt for and create this on first run.

Logs are appended to `vsa_api_tool.log` in the repo root.

## Architecture

This is a folder-as-menu wrapper around the VSA 10 REST API. There is no build step, no test suite, and no framework — `main.py` is a directory scanner that turns the filesystem into an interactive CLI.

**The discovery contract.** `main.py` enumerates immediate subdirectories of the repo root (skipping `__pycache__` and dotfiles) and presents each as a top-level menu entry. Inside a selected folder, every `*.py` file (excluding `__*.py` and `main.py`) becomes a runnable script. When the user picks a script, `main.py` reads the source, scrubs null bytes if present (overwriting the file with cleaned UTF-8), compiles it into a fresh module, and then:

1. Calls `module.main()` if defined, otherwise
2. Calls a function whose **name equals the filename** (e.g. `get_all_devices.py` → `get_all_devices()`), otherwise
3. Reports "executed with no entrypoint."

For option (2), `main.py` introspects the signature and `input()`-prompts for each required positional argument. This means **the function name must match the filename stem** for a script to be auto-runnable from the menu.

**Friendly names.** Each script may declare `__friendly_name__ = "Human Readable Title"` at module level; `main.py` parses this with a simple line scan (not by importing) and uses it as the menu label. Without it, the raw filename is shown.

**Config sharing.** `config.py` at the repo root reads `.env` via `python-dotenv` and exposes `ENDPOINT`, `TOKEN_ID`, `TOKEN_SECRET`. Scripts in subfolders import it one of two ways:

- `import config` — works because `main.py` injects the repo root into `sys.path` before exec
- `sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import config` — used by scripts that should also be runnable standalone (`python Devices/move_a_device.py`)

Prefer the second pattern in new scripts so they work both inside and outside the launcher.

**API access pattern.** All scripts use `slumber.API(config.ENDPOINT, auth=(config.TOKEN_ID, config.TOKEN_SECRET))` and chain attribute/call access to build the URL (e.g. `api.devices(device_id).move.put(body)` → `PUT /devices/{id}/move`). Results are typically `json.dumps(..., indent=4)`'d straight to stdout. Errors are caught and printed, never re-raised — the menu loop expects to return to the prompt after every run.

**Connectivity check.** On startup `main.py` searches subfolders for `get_environment_information.py`, runs it (subprocess first, then in-process import as fallback), parses the JSON response, and displays customer/version info under the main menu. The script lives in `Environment/` but the search is location-tolerant — it'll find it anywhere.

## Conventions for new scripts

A new endpoint script in folder `Foo/`, file `do_thing.py`:

```python
import slumber, json, sys, os
__friendly_name__ = "Do The Thing"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def do_thing(some_arg):                          # name == filename stem
    api = slumber.API(config.ENDPOINT, auth=(config.TOKEN_ID, config.TOKEN_SECRET))
    try:
        result = api.foo(some_arg).get()
        print(json.dumps(result, indent=4))
    except Exception as e:
        print(f"DoThing raised an exception: {e}")

if __name__ == "__main__":
    do_thing(sys.argv[1] if len(sys.argv) > 1 else input("Arg: "))
```

To add a whole new API category, just create a new folder at the repo root — it shows up in the menu automatically on next launch.

The `Hacks/` folder is a scratch area for experimental scripts and does not follow the conventions above.
