
# Checklist — A Simple Python CLI To‑Do List

A tiny, dependency-free command-line checklist app written in Python. It stores your items in a JSON file and supports listing, adding, removing, and moving items using intuitive **1-based indexing**. This README also documents **planned/feature** commands you asked to highlight: `prio`, `update`, and `swap`.

> **Author**: David Degbor  
> **Role**: Software Test Engineer Intern

---

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Commands](#commands)
  - [Options](#options)
  - [Indexing Rules](#indexing-rules)
- [Examples](#examples)
- [Storage & Data Format](#storage--data-format)
- [Error Handling & Exit Codes](#error-handling--exit-codes)
- [Design Overview](#design-overview)
- [Extending the App (prio, update, swap)](#extending-the-app-prio-update-swap)
  - [Implementing `update` (rename item)](#implementing-update-rename-item)
  - [Implementing `swap` (exchange positions)](#implementing-swap-exchange-positions)
  - [Implementing `prio` (set item priority)](#implementing-prio-set-item-priority)
  - [Migrating storage for priorities](#migrating-storage-for-priorities)
- [Cross‑Platform Notes](#crossplatform-notes)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

---

## Features
- **List** all items in order
- **Add** items (multi‑word without quotes supported)
- **Remove** by 1‑based index
- **Move** items from one index to another
- **Use a custom storage file** with `--file`
- **Planned/Featured** enhancements you requested:
  - `update <item_idx> <new_name>` — rename an existing item
  - `swap <src> <dest>` — swap two items’ positions
  - `prio <item_idx> <priority>` — set priority for an item (e.g., `low|med|high` or `1..3`)

> ⚠️ **Note**: As of the provided code, `update`, `swap`, and `prio` are **not yet implemented**. This README describes their expected behavior and offers implementation guidance.

---

## Prerequisites
- Python **3.8+** (works with any modern CPython)

---

## Installation
```bash
# Clone your repo
git clone <your-repo-url>
cd <repo-name>

# Optionally make it executable on Unix
chmod +x checklist.py

# (Optional) Add to PATH or create a shell alias
alias checklist="python3 /path/to/checklist.py"
```

On Windows PowerShell, you can run:
```powershell
python .\checklist.py
```

---

## Quick Start
```bash
# Show the current checklist (stored at ~/.checklist.json by default)
python3 checklist.py

# Add a couple items
python3 checklist.py add Buy milk
python3 checklist.py add Call mom

# Move the second item to the top
python3 checklist.py mv 2 1

# Remove the first item
python3 checklist.py rm 1
```

---

## Usage
The app exposes a minimal set of commands with a single optional flag to choose the storage file.

### Commands
```text
checklist.py                 # Show checklist
checklist.py add <item>      # Add a new item
checklist.py rm <item_idx>   # Remove item at 1-based index
checklist.py mv <src_idx> <dst_idx>  # Move item from src to dst (1-based)
```

#### Featured (Planned) Commands
```text
checklist.py update <item_idx> <new_name>   # Rename item at index
checklist.py swap <src_idx> <dst_idx>       # Swap two items
checklist.py prio <item_idx> <priority>     # Set item priority (low|med|high or 1..3)
```

### Options
```text
checklist.py --file <path>   # Use a custom storage file (default: ~/.checklist.json)
checklist.py --help          # Show help
```

### Indexing Rules
- All indices are **1-based** (first item is `1`).
- Commands validate indices and fail with a helpful error if out of range.

---

## Examples
```bash
# Add items (multi-word items work even without quotes)
checklist.py add Buy oat milk
checklist.py add Schedule dentist appointment

# Remove the second item
checklist.py rm 2

# Move item 3 to position 1
checklist.py mv 3 1

# Use a custom storage file
checklist.py --file ~/work-tasks.json add "Fix login bug"
checklist.py --file ~/work-tasks.json
```

**Planned feature examples:**
```bash
# Rename item 2
checklist.py update 2 "Schedule annual physical"

# Swap items 1 and 4
checklist.py swap 1 4

# Set priority to high
checklist.py prio 3 high
# or a numeric scheme
checklist.py prio 3 3
```

---

## Storage & Data Format
By default, data is stored at `~/.checklist.json`.

- **Current format (v1):** a JSON array of strings
  ```json
  [
    "Buy milk",
    "Call mom"
  ]
  ```
- **Proposed format (v2, for priorities):** an array of objects
  ```json
  [
    { "name": "Buy milk", "priority": "high" },
    { "name": "Call mom", "priority": "low" }
  ]
  ```

> The app currently tolerates a missing or unreadable file by starting fresh with an empty list.

Use `--file <path>` to maintain separate lists (e.g., personal vs work):
```bash
checklist.py --file ~/.personal.json add "Renew car registration"
checklist.py --file ~/.work.json add "Write unit tests"
```

---

## Error Handling & Exit Codes
- Input validation ensures:
  - Indices are numeric and within range.
  - `add` receives a non-empty item string.
- On error, messages are printed to **stderr** and the program exits with **code 2** for usage errors; **code 1** is used for save failures.

Examples:
```text
Error: 'rm' requires exactly one index.
Error: item_idx out of range. Must be between 1 and N.
Error: could not save file '/path': <OS error>
```

---

## Design Overview
Key functions:
- `load_items(file_path: Path) -> list[str]`  
  Loads items from JSON. Returns `[]` if the file is missing or corrupt.

- `save_items(file_path: Path, items)`  
  Writes items back to JSON with `indent=2` for readability.

- `print_items(items)`  
  Renders the checklist to stdout with **1-based numbering**.

- `parse_args(argv)`  
  Minimal parser supporting `add`, `rm`, `mv`, and `--file`. Joins remaining tokens for `add` to allow multi-word items without quotes.

- `ensure_1_based_index(idx_str, items_len, label="index") -> int`  
  Validates and converts a user-provided index string.

- `main()`  
  Orchestrates command execution and persistence.

**Notable implementation choices:**
- Robust against corrupt JSON (starts fresh).
- Stores plain strings for simplicity (v1). Priorities require a v2 format.
- Moves (`mv`) clamp when moving to the end: if destination is `len+1`, the item is inserted at the tail.

---

## Extending the App (prio, update, swap)
Below are suggested approaches to add the three featured commands.

### Implementing `update` (rename item)
**Behavior:** Change the text of the item at `item_idx`.

**Pseudo-code:**
```python
elif cmd == "update":
    if len(items) == 0:
        print("Checklist is empty; nothing to update.")
        return
    idx = ensure_1_based_index(args[0], len(items), label="item_idx")
    new_name = " ".join(args[1:]).strip()
    if not new_name:
        print("Error: new_name cannot be empty.", file=sys.stderr)
        sys.exit(2)

    # v1 format (strings)
    items[idx - 1] = new_name

    save_items(file_path, items)
    print(f"Updated: #{idx} -> '{new_name}'")
    print_items(items)
    return
```

### Implementing `swap` (exchange positions)
**Behavior:** Exchange the positions of items at `src` and `dst`.

**Pseudo-code:**
```python
elif cmd == "swap":
    if len(items) < 2:
        print("Need at least two items to swap.")
        return
    src = ensure_1_based_index(args[0], len(items), label="src_idx")
    dst = ensure_1_based_index(args[1], len(items), label="dst_idx")
    if src == dst:
        print("No-op: src and dst are the same.")
        return
    items[src - 1], items[dst - 1] = items[dst - 1], items[src - 1]
    save_items(file_path, items)
    print(f"Swapped: #{src} <-> #{dst}")
    print_items(items)
    return
```

### Implementing `prio` (set item priority)
**Behavior:** Assign a priority to a given item. You can choose either `low|med|high` or a numeric scheme (`1..3`).

Because v1 storage uses strings, priorities require adopting **v2** (objects). A gradual approach can be:

1. **Detect format** at load time: if the JSON contains strings, convert to v2 with default priority (e.g., `"med"`).
2. **Persist objects** from then on.

**Loader shim:**
```python
def load_items(file_path: Path):
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            # v2 objects
            if data and isinstance(data[0], dict):
                return [
                    {"name": str(x.get("name", "")), "priority": x.get("priority", "med")}
                    for x in data
                ]
            # v1 strings -> upgrade
            return [{"name": str(x), "priority": "med"} for x in data]
        return []
    except (json.JSONDecodeError, OSError):
        return []
```

**Setter:**
```python
VALID_PRIOS = {"low", "med", "high"}

elif cmd == "prio":
    if len(items) == 0:
        print("Checklist is empty; nothing to prioritize.")
        return
    idx = ensure_1_based_index(args[0], len(items), label="item_idx")
    level = args[1].lower()
    if level not in VALID_PRIOS:
        print("Error: priority must be one of low|med|high.", file=sys.stderr)
        sys.exit(2)
    items[idx - 1]["priority"] = level
    save_items(file_path, items)
    print(f"Priority set: #{idx} -> {level}")
    # Optionally print with an indicator
    for i, it in enumerate(items, start=1):
        mark = {"low": "-", "med": "*", "high": "!"}[it["priority"]]
        print(f"{i}. [{mark}] {it['name']}")
    return
```

> If you prefer numeric priorities, adjust validation accordingly and store a number in `priority`.

### Migrating storage for priorities
If you already have `~/.checklist.json` with strings, the loader shim above auto-upgrades. Alternatively, you can run a one-off migration:
```python
# migrate_v1_to_v2.py
import json, pathlib
p = pathlib.Path.home() / ".checklist.json"
with p.open("r", encoding="utf-8") as f:
    data = json.load(f)
if isinstance(data, list) and (not data or isinstance(data[0], str)):
    data = [{"name": x, "priority": "med"} for x in data]
with p.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Migrated to v2 (objects with priority)")
```

---

## Cross‑Platform Notes
- Paths: `~/.checklist.json` expands appropriately on macOS/Linux and Windows (e.g., `C:\Users\<user>\`).
- Quoting: The `add` command joins tokens, so quotes are **not required** for multi-word items; nonetheless, quoting is still fine.
- Unicode: Files are read/written with UTF‑8, so non‑ASCII item names are supported.

---

## FAQ
**Q: Why 1‑based indices?**  
A: It aligns with how people naturally count items on a list and matches the printed numbering.

**Q: What happens if the storage file is corrupt?**  
A: The app starts fresh with an empty list, preventing crashes.

**Q: Can I keep multiple lists?**  
A: Yes — use `--file <path>` to point to any JSON file.

---

## Contributing
1. Fork the repo and create a feature branch: `feat/update-command`.
2. Add tests (e.g., using `pytest`) for new behavior.
3. Ensure style consistency and update this README.
4. Open a PR with a clear description and screenshots of terminal output when helpful.

---

## License
Specify your license (e.g., MIT). Include `LICENSE` in the repository.

---

## Developer Notes (for maintainers)
- Consider adding basic **file locking** to avoid concurrent write issues.
- Add a `--sort` view or grouping by priority when `prio` is implemented (e.g., show High first).
- Add `--json` output mode for scripting.
- Add `--version` flag and semantic versioning.

---

## Help Output
Running `checklist.py --help` prints the embedded docstring help:
```text
Simple command-line checklist app.

Usage:
  checklist.py                 # Show checklist
  checklist.py add <item>      # Add a new item
  checklist.py rm <item_idx>   # Remove item at 1-based index
  checklist.py mv <src_idx> <dst_idx>  # Move item from src to dst (1-based)
  checklist.py --file <path>   # Optional: use a custom storage file

Examples:
  checklist.py add "Buy milk"
  checklist.py rm 2
  checklist.py mv 3 1
```

---

### Acknowledgements
Thanks for sharing the project structure, David! This README aims to be future-proof for the `update`, `swap`, and `prio` commands you want to feature.
