"""
Simple command-line checklist app.

Usage:
  todo-cli.py                            # Show checklist
  todo-cli.py add <item>                 # Add a new item
  todo-cli.py rm <item_idx>              # Remove item at 1-based index
  todo-cli.py mv <src_idx> <dst_idx>     # Move item from src to dst (1-based)
  todo-cli.py prio <item_idx> <priority> # Set item priority (low|med|high or 1..3)
  todo-cli.py --file <path>              # Optional: use a custom storage file

Examples:
  todo-cli.py add "Buy milk"
  todo-cli.py rm 2
  todo-cli.py mv 3 1
  todo-cli.py prio 1 high
"""

import sys
import json
import os
from pathlib import Path

DEFAULT_FILE = Path.home() / ".checklist.json"

def _load_items(file_path: Path):
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            # Ensure all items are strings
            return [str(x) for x in data]
        return []
    except (json.JSONDecodeError, OSError):
        # Corrupt or unreadable file — start fresh
        return []
    
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
                    {"name": str(x.get("name", "")), "priority": x.get("priority", "none")}
                    for x in data
                ]
            # v1 strings -> upgrade
            return [{"name": str(x), "priority": "none"} for x in data]
        return []
    except (json.JSONDecodeError, OSError):
        return []

def save_items(file_path: Path, items):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Error: could not save file '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)

def print_items(items):
    if not items:
        print("Checklist is empty.")
        return
    for i, item in enumerate(items, start=1):
        mark = {"none": "x","low": "-", "med": "*", "high": "!"}[item["priority"]]
        print(f"{i}. [{mark}] {item['name']}")

def parse_args(argv):
    """
    Minimal argument parser supporting:
      add <item>
      rm <idx>
      mv <src> <dst>
      --file <path>

    Returns: (cmd, args, file_path)
      cmd: 'add' | 'rm' | 'mv' | 'list'
      args: list of strings for the command
      file_path: Path object for storage
    """
    file_path = DEFAULT_FILE
    # Allow --file anywhere; strip it from argv
    cleaned = []
    i = 0
    while i < len(argv):
        if argv[i] == "--file":
            if i + 1 >= len(argv):
                print("Error: --file requires a path.", file=sys.stderr)
                sys.exit(2)
            file_path = Path(argv[i + 1]).expanduser()
            i += 2
        else:
            cleaned.append(argv[i])
            i += 1

    if not cleaned:
        return ("list", [], file_path)

    cmd = cleaned[0]
    if cmd == "add":
        if len(cleaned) < 2:
            print("Error: 'add' requires an item string.", file=sys.stderr)
            sys.exit(2)
        # Join remaining parts so multi-word items work without quotes
        item = " ".join(cleaned[1:])
        return ("add", [item], file_path)
    elif cmd == "rm":
        if len(cleaned) != 2:
            print("Error: 'rm' requires exactly one index.", file=sys.stderr)
            sys.exit(2)
        return ("rm", [cleaned[1]], file_path)
    elif cmd == "mv":
        if len(cleaned) != 3:
            print("Error: 'mv' requires src_idx and dst_idx.", file=sys.stderr)
            sys.exit(2)
        return ("mv", [cleaned[1], cleaned[2]], file_path)
    elif cmd == "prio":
        if len(cleaned) != 3:
            print("Error: 'prio' requires item and priority level.", file=sys.stderr)
            sys.exit(2)
        return("prio", [cleaned[1], cleaned[2]], file_path)
    elif cmd == "edit":
        if len(cleaned) != 3:
            print("Error: 'edit' requires item idx followed by its new name", file=sys.stderr)
            sys.exit(2)
        return("edit", [cleaned[1], cleaned[2]], file_path)
    elif cmd in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)
    else:
        print(f"Error: unknown command '{cmd}'.", file=sys.stderr)
        print("Use 'add', 'rm', 'mv', or run without args to list. For help: todo-cli.py --help")
        sys.exit(2)

def ensure_1_based_index(idx_str, items_len, label="index"):
    try:
        idx = int(idx_str)
    except ValueError:
        print(f"Error: {label} must be a number (got '{idx_str}').", file=sys.stderr)
        sys.exit(2)
    if idx < 1 or idx > items_len:
        print(f"Error: {label} out of range. Must be between 1 and {items_len}.", file=sys.stderr)
        sys.exit(2)
    return idx

def main():
    cmd, args, file_path = parse_args(sys.argv[1:])
    items = load_items(file_path)
    VALID_PRIOS = {"none","low", "med", "high"}

    if cmd == "list":
        print_items(items)
        return

    if cmd == "add":
        item = args[0].strip()
        if not item:
            print("Error: item cannot be empty.", file=sys.stderr)
            sys.exit(2)
        obj = {"name": item, "priority": "none"}
        items.append(obj)
        save_items(file_path, items)
        print(f"Added: '{obj["name"]}'")
        print_items(items)
        return

    if cmd == "rm":
        if len(items) == 0:
            print("Checklist is empty; nothing to remove.")
            return
        idx = ensure_1_based_index(args[0], len(items), label="item_idx")
        removed = items.pop(idx - 1)
        save_items(file_path, items)
        print(f"Removed: '{removed["name"]}' (was #{idx})")
        print_items(items)
        return

    if cmd == "mv":
        if len(items) == 0:
            print("Checklist is empty; nothing to move.")
            return
        src = ensure_1_based_index(args[0], len(items), label="src_itm_idx")
        dst = ensure_1_based_index(args[1], len(items), label="dst_itm_idx")
        # Extract and insert
        item = items.pop(src - 1)
        # After popping, adjust destination if moving forward in list
        if dst - 1 > len(items):
            # If dst was equal to len+1 (moving to end), clamp
            dst = len(items) + 1
        items.insert(dst - 1, item)
        save_items(file_path, items)
        print(f"Moved: '{item["name"]}' from #{src} to #{dst}")
        print_items(items)
        return
    
    elif cmd == "prio":
        if len(items) == 0:
            print("Checklist is empty; nothing to prioritize.")
            return
        idx = ensure_1_based_index(args[0], len(items), label="item_idx")
        level = args[1].lower()
        if level not in VALID_PRIOS:
            print("Error: priority must be one of none|low|med|high.", file=sys.stderr)
            sys.exit(2)
        items[idx - 1]["priority"] = level
        save_items(file_path, items)
        print(f"Priority set: #{idx} -> {level}")
        # Optionally print with an indicator
        print_items(items)
        return
    elif cmd == "edit":
        if len(items) == 0:
            print("Checklist is empty; nothing to edit.")
            return
        idx = ensure_1_based_index(args[0], len(items), label="item_idx")
        new_name = " ".join(args[1:]).strip()
        if not new_name:
            print("Error: new_name cannot be empty.", file=sys.stderr)
            sys.exit(2)

        items[idx - 1]["name"] = new_name

        save_items(file_path, items)
        print(f"edited: #{idx} -> '{new_name}'")
        print_items(items)
        return

if __name__ == "__main__":
    main()
