#!/usr/bin/env python3
"""Add approved section-B rules from a self-improve report to a CLAUDE.md, inside a marked block.

  python3 apply_rules.py --preview --findings F --target PATH --ids b-1,b-2   show the unified diff (writes nothing)
  python3 apply_rules.py --write   --findings F --target PATH --ids b-1,b-2   write it

The block lives between <!-- self-improve:start --> and <!-- self-improve:end -->. Running again replaces the
block (never duplicates it). Text outside the block is never touched. Standard library only.
"""
import argparse
import difflib
import json
import os
import re
import sys

START = "<!-- self-improve:start -->"
END = "<!-- self-improve:end -->"


def build_block(rules, date):
    lines = [START, "## Learned from my Claude Code history (self-improve, %s)" % date, ""]
    for r in rules:
        rule = " ".join(str(r.get("rule", "")).split())
        if rule:
            lines.append("- %s" % rule)
    lines.append(END)
    return "\n".join(lines) + "\n"


def new_text(old, block):
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)
    if pat.search(old):
        return pat.sub(lambda m: block, old, count=1)
    if not old:
        return block
    sep = "" if old.endswith("\n\n") else ("\n" if old.endswith("\n") else "\n\n")
    return old + sep + block


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--preview", action="store_true")
    g.add_argument("--write", action="store_true")
    ap.add_argument("--findings", required=True)
    ap.add_argument("--target", required=True, help="the CLAUDE.md to change, e.g. ~/.claude/CLAUDE.md")
    ap.add_argument("--ids", required=True, help="comma-separated section-B finding ids the user approved")
    a = ap.parse_args(argv)

    with open(os.path.expanduser(a.findings), encoding="utf-8") as fh:
        f = json.load(fh)
    wanted = [x.strip() for x in a.ids.split(",") if x.strip()]
    by_id = {r.get("id"): r for r in (f.get("sections") or {}).get("B", [])}
    missing = [i for i in wanted if i not in by_id]
    if missing:
        print("STOP: no section-B finding with id %s. Known ids: %s" % (", ".join(missing), ", ".join(by_id)))
        return 2
    rules = [by_id[i] for i in wanted]
    target = os.path.expanduser(a.target)
    if os.path.basename(target) != "CLAUDE.md":
        print("STOP: the target must be a file named CLAUDE.md, got %s" % target)
        return 2
    old = ""
    if os.path.isfile(target):
        with open(target, encoding="utf-8") as fh:
            old = fh.read()
    new = new_text(old, build_block(rules, f.get("generated", "")))
    if new == old:
        print("No change: %s already has exactly these rules." % target)
        return 0
    diff = difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile=target + " (now)", tofile=target + " (after)")
    sys.stdout.write("".join(diff))
    if a.preview:
        print("\n(preview only - nothing written)")
        return 0
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(new)
    print("\nwrote %s (%d rules in the self-improve block)" % (target, len(rules)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
