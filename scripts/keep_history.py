#!/usr/bin/env python3
"""Keep Claude Code transcripts for longer by setting cleanupPeriodDays in ~/.claude/settings.json.

  python3 keep_history.py --check          show the current value and what would change (writes nothing)
  python3 keep_history.py --apply          back up settings.json, then set cleanupPeriodDays (default 365)

Every other key is kept as it is. Never lowers a value that is already higher. Standard library only.
"""
import argparse
import datetime as dt
import json
import os
import shutil
import sys


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--apply", action="store_true")
    ap.add_argument("--days", type=int, default=365)
    a = ap.parse_args(argv)

    cfg = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude")  # Claude Code's config folder
    path = os.path.join(cfg, "settings.json")
    data = {}
    exists = os.path.isfile(path)
    if exists:
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            data = json.loads(text) if text.strip() else {}
        except Exception as e:
            print("STOP: %s is not valid JSON (%s). Nothing changed. Fix the file first." % (path, e))
            return 2
        if not isinstance(data, dict):
            print("STOP: %s does not hold a JSON object. Nothing changed." % path)
            return 2
    current = data.get("cleanupPeriodDays")
    print("settings file: %s%s" % (path, "" if exists else " (does not exist yet)"))
    print("cleanupPeriodDays now: %s" % ("not set (Claude Code default: 30 days)" if current is None else current))
    if isinstance(current, (int, float)) and current >= a.days:
        print("Nothing to do: transcripts are already kept for %s days." % current)
        return 0
    print("will set: cleanupPeriodDays = %d (all other %d keys unchanged)" % (a.days, len([k for k in data if k != "cleanupPeriodDays"])))
    if a.check:
        return 0

    os.makedirs(os.path.dirname(path), exist_ok=True)
    if exists:
        backup = path + ".bak-self-improve-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(path, backup)
        print("backup: %s" % backup)
    data["cleanupPeriodDays"] = a.days
    tmp = path + ".tmp-self-improve"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)
    with open(path, encoding="utf-8") as fh:
        check = json.load(fh)
    print("done: cleanupPeriodDays = %s (verified by reading the file back)" % check.get("cleanupPeriodDays"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
