#!/usr/bin/env python3
"""Install one drafted skill folder from a self-improve report.

  python3 install_skill.py --list  --report ~/claude-improve/2026-10-17
  python3 install_skill.py --check --src <report>/skills/<name> --dest ~/.claude/skills
  python3 install_skill.py --install --src <report>/skills/<name> --dest ~/.claude/skills [--force]

--dest is ~/.claude/skills (all projects) or <project>/.claude/skills (one project). An existing skill with the
same name is never replaced unless --force is given (the old folder is then kept as <name>.bak-<time>).
Standard library only.
"""
import argparse
import datetime as dt
import os
import re
import shutil
import sys


def frontmatter(path):
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except Exception as e:
        return None, "cannot read %s: %s" % (path, e)
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, "no YAML frontmatter between --- lines"
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    problems = []
    name = fm.get("name", "")
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name) or len(name) > 64:
        problems.append("name must be lowercase letters, digits and hyphens (max 64): %r" % name)
    if not fm.get("description"):
        problems.append("description is missing")
    elif len(fm["description"]) > 1024:
        problems.append("description is longer than 1024 characters")
    return fm, "; ".join(problems)


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--install", action="store_true")
    ap.add_argument("--report")
    ap.add_argument("--src")
    ap.add_argument("--dest")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)

    if a.list:
        root = os.path.join(os.path.expanduser(a.report or ""), "skills")
        if not os.path.isdir(root):
            print("No drafted skills in %s" % root)
            return 1
        for n in sorted(os.listdir(root)):
            p = os.path.join(root, n, "SKILL.md")
            if os.path.isfile(p):
                fm, prob = frontmatter(p)
                print("- %s: %s%s" % (n, (fm or {}).get("description", "")[:160], ("  [PROBLEM: %s]" % prob) if prob else ""))
        return 0

    src = os.path.expanduser(a.src or "")
    dest_root = os.path.expanduser(a.dest or "")
    if not os.path.isfile(os.path.join(src, "SKILL.md")) or not dest_root:
        print("STOP: give --src <folder with SKILL.md> and --dest <skills folder>")
        return 2
    fm, prob = frontmatter(os.path.join(src, "SKILL.md"))
    if prob:
        print("STOP: %s" % prob)
        return 2
    name = fm["name"]
    dest = os.path.join(dest_root, name)
    exists = os.path.exists(dest)
    print("skill: %s\nfrom:  %s\nto:    %s\nalready installed there: %s" % (name, src, dest, "YES" if exists else "no"))
    if a.check:
        return 0
    if exists and not a.force:
        print("STOP: %s already exists. Ask the user; re-run with --force to replace it (the old one is kept as a backup)." % dest)
        return 3
    os.makedirs(dest_root, exist_ok=True)
    if exists:
        bak = dest + ".bak-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.move(dest, bak)
        print("old version kept at %s" % bak)
    shutil.copytree(src, dest)
    print("installed: %s (Claude Code picks it up in this session; type /%s to use it)" % (dest, name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
