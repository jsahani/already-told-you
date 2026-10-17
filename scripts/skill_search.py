#!/usr/bin/env python3
"""Search the open skills ecosystem (skills.sh) and vet the results. The only part of Already Told You that uses the
network, and only when the user says yes.

  python3 skill_search.py --plan   --keywords "playwright" "testing"        offline: cleans the keywords, prints what would be sent
  python3 skill_search.py --search --keywords "playwright" "testing"        sends ONLY the keywords to skills.sh, prints JSON results
  python3 skill_search.py --vet owner/repo@skill [owner/repo@skill ...]     looks the candidates up on GitHub and skills.sh

What leaves the computer:
  --plan    nothing.
  --search  one request: https://skills.sh/api/search?q=<the cleaned keywords>&limit=<n>
  --vet     for each candidate (public names taken from the search results, nothing from the user):
            api.github.com/repos/<owner>/<repo>, .../branches/<branch>, .../git/trees/<commit>,
            raw.githubusercontent.com for the files of that one skill folder, and the security scan results skills.sh
            publishes for it (https://skills.sh/tele/audit?source=<owner/repo>&skills=<skill>).

Keywords must be short and generic. The cleaner refuses anything that could identify the user or their work: paths,
URLs, emails, @handles, long numbers, key-like strings, the user's login name, the names of their projects (read
locally from the Claude Code history folder) and any word given with --deny. It never sends history text.

--vet downloads the skill folder (exact commit) to ~/already-told-you/skill-search/<date>/<owner>__<repo>__<skill>/
so Claude can read the real SKILL.md and scripts, and so install_skill.py can install exactly the copy that was
checked. Standard library only. No telemetry.
"""
import argparse
import datetime as dt
import getpass
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SEARCH_URL = "https://skills.sh/api/search"
AUDIT_URL = "https://skills.sh/tele/audit"
GITHUB_API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
UA = "already-told-you-skill-search/1.1"

MAX_KEYWORDS = 4
MAX_WORDS = 6
MAX_QUERY_CHARS = 60

# Owners with a public track record of publishing skills. Reputation is one signal, never a free pass.
REPUTABLE_OWNERS = {"anthropics", "vercel-labs", "vercel", "microsoft", "github", "openai", "google", "googleapis",
                    "google-gemini", "cloudflare", "supabase", "stripe", "figma", "notion", "huggingface", "aws",
                    "awslabs", "aws-samples", "netlify", "mongodb", "prisma", "sentry", "getsentry", "shopify",
                    "remotion-dev", "expo", "callstackincubator", "clerk", "neondatabase", "posthog", "pydantic",
                    "langchain-ai", "hashicorp", "docker", "elastic", "grafana", "atlassian", "linear", "slackapi"}

# Generic folder names that are fine as keywords even when a project happens to use them.
GENERIC = set("""api app apps web site sites website docs doc test tests testing src content scripts script frontend
backend server client clients blog notes demo tmp temp project projects worker workers brain sources source visuals
design data assets home main dev build tools tool utils lib code repo repos work playground sandbox examples
""".split())

MAX_FILES = 150
MAX_TOTAL_BYTES = 3 * 1024 * 1024


# ------------------------------------------------------------------------------------------------
# keyword cleaning (offline)
# ------------------------------------------------------------------------------------------------

RE_ALLOWED = re.compile(r"^[a-z0-9][a-z0-9 +.#-]*$")
RE_KEY_PREFIX = re.compile(r"^(sk|pk|rk|ghp|gho|ghs|github_pat|xox[abp]|glpat|akia|eyj)[-_]?[a-z0-9]", re.I)


def looks_secret(token):
    """A single space-free token that reads like a key, token or ID rather than a word."""
    t = token.strip()
    if len(t) >= 25:
        return True
    if len(t) >= 12 and RE_KEY_PREFIX.match(t):
        return True
    return len(t) >= 16 and bool(re.search(r"\d", t)) and bool(re.search(r"[a-z]", t, re.I))


def norm(s):
    return re.sub(r"[\s_-]+", " ", (s or "").strip().lower()).strip()


def local_names(projects_dir=None):
    """Names that identify this user or their work: login and home folder names, and the last folder name of every
    project in the Claude Code history. Read locally, never sent anywhere."""
    names = set()
    for n in (getpass.getuser(), os.path.basename(os.path.expanduser("~"))):
        if n:
            names.add(norm(n))
    root = projects_dir or os.path.join(os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude"), "projects")
    if not os.path.isdir(root):
        return names
    rx = re.compile(r'"cwd":\s?"((?:[^"\\]|\\.)*)"')
    for folder in os.listdir(root):
        d = os.path.join(root, folder)
        if not os.path.isdir(d):
            continue
        cwd = None
        for f in sorted(os.listdir(d))[:3]:
            if not f.endswith(".jsonl"):
                continue
            try:
                with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh):
                        m = rx.search(line)
                        if m:
                            cwd = json.loads('"%s"' % m.group(1))
                            break
                        if i > 40:
                            break
            except (OSError, ValueError):
                continue
            if cwd:
                break
        if cwd:
            base = norm(os.path.basename(cwd.rstrip("/")))
            if base and base not in GENERIC:
                names.add(base)
    return {n for n in names if n}


def clean_keywords(raw, deny=(), names=None):
    """Return (keywords, problems). Problems name each refused keyword and why; refused ones are dropped."""
    names = set(names or ()) | {norm(d) for d in deny if norm(d)}
    keep, problems = [], []
    for k in raw:
        k0 = (k or "").strip()
        k1 = norm(k0)
        why = None
        if not k1:
            continue
        if re.search(r"[/\\~]|https?:|www\.", k0, re.I):
            why = "looks like a path or web address"
        elif "@" in k0:
            why = "looks like an email or @handle"
        elif re.search(r"\d{5,}", k1):
            why = "contains a long number"
        elif any(looks_secret(t) for t in k0.split()):
            why = "looks like a key or ID"
        elif not RE_ALLOWED.match(k1):
            why = "use plain words only (letters, digits, + . # -)"
        elif len(k1) > 30:
            why = "too long (keep each keyword under 30 characters)"
        else:
            hit = [n for n in names if n == k1 or (len(n) >= 4 and re.search(r"(^| )%s( |$)" % re.escape(n), k1))]
            if hit:
                why = "matches a personal or project name (%s)" % hit[0]
        if why:
            problems.append("%r refused: %s" % (k0, why))
        elif k1 not in keep:
            keep.append(k1)
    if len(keep) > MAX_KEYWORDS:
        problems.append("only the first %d keywords are used" % MAX_KEYWORDS)
        keep = keep[:MAX_KEYWORDS]
    words = " ".join(keep).split()
    if len(words) > MAX_WORDS or len(" ".join(keep)) > MAX_QUERY_CHARS:
        problems.append("the search is limited to %d words / %d characters; shorten the keywords" % (MAX_WORDS, MAX_QUERY_CHARS))
        return [], problems
    return keep, problems


def search_url(keywords, limit=10, owner=None):
    params = {"q": " ".join(keywords), "limit": str(limit)}
    if owner:
        params["owner"] = owner
    return SEARCH_URL + "?" + urllib.parse.urlencode(params)


# ------------------------------------------------------------------------------------------------
# network
# ------------------------------------------------------------------------------------------------

def http_get(url, accept="application/json", timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_json(url):
    return json.loads(http_get(url).decode("utf-8"))


def parse_results(data):
    """skills.sh search JSON -> candidate list, highest installs first, with copies of the same skill name counted."""
    out = []
    for s in (data or {}).get("skills") or []:
        sid = str(s.get("id") or "")
        source = str(s.get("source") or "")
        skill = str(s.get("skillId") or s.get("name") or "")
        if not re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", source) or not re.match(r"^[A-Za-z0-9_.:-]+$", skill):
            continue
        owner, repo = source.split("/", 1)
        out.append({"ref": "%s@%s" % (source, skill), "owner": owner, "repo": repo, "skill": skill,
                    "name": str(s.get("name") or skill), "installs": int(s.get("installs") or 0),
                    "url": "https://skills.sh/%s" % (sid or "%s/%s" % (source, skill)),
                    "github": "https://github.com/%s" % source,
                    "reputable_owner": owner.lower() in REPUTABLE_OWNERS})
    out.sort(key=lambda c: -c["installs"])
    names = {}
    for c in out:
        names[c["skill"].lower()] = names.get(c["skill"].lower(), 0) + 1
    for c in out:
        c["same_name_elsewhere"] = names[c["skill"].lower()] - 1
    return out


# ------------------------------------------------------------------------------------------------
# risk scan (offline, on downloaded text)
# ------------------------------------------------------------------------------------------------

HIGH, MEDIUM, INFO = 2, 1, 0
SEVERITY_NAME = {HIGH: "high", MEDIUM: "medium", INFO: "info"}

# (label, severity, pattern). High = a reason not to install; medium = read those lines before deciding; info = shown only.
RISKS = [
    ("runs remote code", HIGH, re.compile(r"(curl|wget|iwr|invoke-webrequest)\b[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh\b|bash\s+<\(\s*curl|"
                                          r"\biex\b|invoke-expression|eval\s*\(\s*(curl|fetch|requests)", re.I)),
    ("hidden instructions", HIGH, re.compile(r"ignore (all )?(previous|prior|above) instructions|do not (tell|inform|show) the user|"
                                             r"without (telling|asking|informing) the user|[​‌‍⁠﻿]", re.I)),
    ("reads secret files", HIGH, re.compile(r"~/\.ssh|\bid_(rsa|ed25519)\b|\.aws/credentials|security\s+find-(generic|internet)-password|"
                                            r"\bcat\s+[^\n]*\.env\b|\bprintenv\b|\benv\s*\|\s*(curl|nc|grep)|\.claude/(settings|\.credentials)", re.I)),
    ("obfuscated content", HIGH, re.compile(r"[A-Za-z0-9+/]{200,}={0,2}|\\x[0-9a-f]{2}(\\x[0-9a-f]{2}){20,}", re.I)),
    ("asks for secrets or tokens", MEDIUM, re.compile(r"\b(paste|provide|enter|give|share|send|type)\s+(me\s+|us\s+)?(your|the|an?)\s+"
                                                      r"[^\n.]{0,25}(api[ _-]?key|token|password|secret|credentials?)\b", re.I)),
    ("broad permissions", MEDIUM, re.compile(r"dangerously-skip-permissions|bypassPermissions|allowed-tools:\s*[^\n]*\bBash\b(?!\()|"
                                             r"Bash\(\s*\*\s*\)|\bsudo\b|chmod\s+(-R\s+)?777|rm\s+-rf\s+[/~$]", re.I)),
    ("sends data out", MEDIUM, re.compile(r"curl\s+[^\n]*(-X\s*POST|--data\b|-d\s)|requests\.post|\bwebhook\b|ngrok|pastebin|"
                                          r"transfer\.sh|discord(app)?\.com/api/webhooks", re.I)),
    ("installs packages", INFO, re.compile(r"\b(npx\s+-y|npm\s+(i|install)\s+-g|pip3?\s+install|brew\s+install|go\s+install|cargo\s+install)\b", re.I)),
    ("mentions keys or tokens", INFO, re.compile(r"\b(api[_ -]?key|access[_ -]?token|secret[_ -]?key|private[_ -]?key|bearer)\b", re.I)),
]


def is_doc(rel):
    """Reference and example files count one level lower than SKILL.md and scripts: they often hold sample code."""
    return rel != "SKILL.md" and (rel.lower().endswith((".md", ".txt", ".mdx", ".rst")) or rel.lower().startswith(("examples/", "references/", "docs/")))


def scan_text(text, rel="SKILL.md"):
    """{label: {"severity": n, "hits": [{"file", "line", "text"}]}}; at most 3 hits per label, one per line."""
    found = {}
    lines = text.splitlines()
    for label, sev, rx in RISKS:
        seen = set()
        for m in rx.finditer(text):
            line = text[:m.start()].count("\n") + 1
            if line in seen:
                continue
            seen.add(line)
            s = max(INFO, sev - 1) if is_doc(rel) else sev
            f = found.setdefault(label, {"severity": s, "hits": []})
            f["severity"] = max(f["severity"], s)
            if len(f["hits"]) < 3:
                f["hits"].append({"file": rel, "line": line, "text": (lines[line - 1].strip() if line <= len(lines) else "")[:140]})
    return found


def merge_flags(into, new):
    for label, f in new.items():
        g = into.setdefault(label, {"severity": f["severity"], "hits": []})
        g["severity"] = max(g["severity"], f["severity"])
        g["hits"].extend(f["hits"][: max(0, 4 - len(g["hits"]))])
    return into


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def verdict(c):
    """'recommend' / 'caution' / 'avoid' from the numbers and the scan. Claude still reads the files and decides."""
    reasons, level = [], 0
    inst, stars = c.get("installs"), c.get("stars")
    if inst is None:
        reasons.append("install count unknown (vetted without search results)")
        inst = 0
    elif inst < 100:
        reasons.append("under 100 installs")
        level = max(level, 1)
    elif inst < 1000:
        reasons.append("under 1,000 installs")
    if stars is None:
        reasons.append("GitHub repo could not be checked")
        level = max(level, 1)
    else:
        if stars < 100 and not c.get("reputable_owner"):
            reasons.append("under 100 GitHub stars")
            level = max(level, 1)
        if inst >= 10000 and stars < 100:
            reasons.append("install count looks inflated next to %d stars" % stars)
            level = max(level, 1)
    if c.get("repo_age_days") is not None and c["repo_age_days"] < 30:
        reasons.append("repo is under 30 days old")
        level = max(level, 1)
    if c.get("archived"):
        reasons.append("repo is archived")
        level = max(level, 1)
    if c.get("same_name_elsewhere"):
        reasons.append("%d other repos publish a skill with this name; check this is the original" % c["same_name_elsewhere"])
    if not c.get("skill_md"):
        reasons.append("SKILL.md not found")
        level = 2
    for label, f in sorted((c.get("flags") or {}).items(), key=lambda kv: -kv[1]["severity"]):
        if f["severity"] > INFO:
            reasons.append("%s risk: %s (%s)" % (SEVERITY_NAME[f["severity"]], label, ", ".join(
                "%s:%s" % (h["file"], h["line"]) for h in f["hits"][:2])))
            level = max(level, f["severity"])
    for scanner, risk in sorted((c.get("third_party_scans") or {}).items()):
        if str(risk).lower() in ("high", "critical"):
            reasons.append("note: the %s scan on skills.sh rates it %s (scanners often disagree; read the files)" % (scanner, risk))
    if c.get("reputable_owner"):
        reasons.insert(0, "known publisher")
    return ["recommend", "caution", "avoid"][level], reasons


def find_skill_path(tree, skill, repo="", read=None):
    """Path of the skill's SKILL.md in the repo tree. read(path) -> text is used last, to match the name: field."""
    blobs = [t["path"] for t in tree if t.get("type") == "blob"]
    mds = [p for p in blobs if os.path.basename(p) == "SKILL.md"]
    s = skill.lower()
    exact = [p for p in mds if os.path.basename(os.path.dirname(p)).lower() == s]
    if exact:
        return sorted(exact, key=len)[0]
    if "SKILL.md" in mds and (s == repo.lower() or s in repo.lower() or repo.lower() in s):
        return "SKILL.md"
    if len(mds) == 1:
        return mds[0]
    loose = [p for p in mds if s in p.lower()]
    if loose:
        return sorted(loose, key=len)[0]
    if read:
        for p in sorted(mds, key=len)[:8]:
            try:
                if frontmatter(read(p)).get("name", "").lower() == s:
                    return p
            except (urllib.error.URLError, OSError, UnicodeDecodeError):
                continue
    return None


def vet_one(ref, out_root, search_info=None):
    m = re.match(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)@([A-Za-z0-9_.:-]+)$", ref)
    if not m:
        return {"ref": ref, "error": "expected owner/repo@skill"}
    owner, repo, skill = m.groups()
    c = dict(search_info or {})
    c.update({"ref": ref, "owner": owner, "repo": repo, "skill": skill,
              "reputable_owner": owner.lower() in REPUTABLE_OWNERS,
              "github": "https://github.com/%s/%s" % (owner, repo),
              "url": c.get("url") or "https://skills.sh/%s/%s/%s" % (owner, repo, skill)})
    c.setdefault("installs", None)
    c.setdefault("same_name_elsewhere", 0)
    try:
        r = get_json("%s/repos/%s/%s" % (GITHUB_API, owner, repo))
        c["stars"] = int(r.get("stargazers_count") or 0)
        c["archived"] = bool(r.get("archived"))
        c["fork"] = bool(r.get("fork"))
        c["license"] = ((r.get("license") or {}).get("spdx_id"))
        created = (r.get("created_at") or "")[:10]
        c["created"], c["last_push"] = created, (r.get("pushed_at") or "")[:10]
        if created:
            c["repo_age_days"] = (dt.date.today() - dt.date.fromisoformat(created)).days
        branch = r.get("default_branch") or "main"
        b = get_json("%s/repos/%s/%s/branches/%s" % (GITHUB_API, owner, repo, urllib.parse.quote(branch)))
        commit = b["commit"]["sha"]
        c["commit"] = commit
        t = get_json("%s/repos/%s/%s/git/trees/%s?recursive=1" % (GITHUB_API, owner, repo, commit))
        tree = t.get("tree") or []
    except urllib.error.HTTPError as e:
        c["stars"] = c.get("stars")
        c["error"] = "GitHub said %s%s" % (e.code, " (rate limit: try again in an hour)" if e.code == 403 else "")
        c["verdict"], c["reasons"] = verdict(c)
        return c
    except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
        c["stars"] = c.get("stars")
        c["error"] = "could not reach GitHub: %s" % e
        c["verdict"], c["reasons"] = verdict(c)
        return c

    path = find_skill_path(tree, skill, repo, lambda p: http_get(
        "%s/%s/%s/%s/%s" % (RAW, owner, repo, commit, urllib.parse.quote(p)), accept="*/*").decode("utf-8"))
    flags, files = {}, []
    if path:
        folder = os.path.dirname(path)
        c["skill_path"] = path
        inside = [x for x in tree if x.get("type") == "blob" and (not folder or x["path"].startswith(folder + "/"))]
        if not folder:
            inside = [x for x in inside if x["path"] == "SKILL.md" or not x["path"].startswith(".")]
        dest = os.path.join(out_root, "%s__%s__%s" % (owner, repo, skill))
        total, complete = 0, True
        for x in inside[:MAX_FILES]:
            size = int(x.get("size") or 0)
            if total + size > MAX_TOTAL_BYTES:
                complete = False
                break
            rel = x["path"][len(folder) + 1:] if folder else x["path"]
            try:
                data = http_get("%s/%s/%s/%s/%s" % (RAW, owner, repo, commit, urllib.parse.quote(x["path"])), accept="*/*")
            except (urllib.error.URLError, OSError):
                complete = False
                continue
            total += len(data)
            target = os.path.join(dest, rel)
            if not os.path.abspath(target).startswith(os.path.abspath(dest) + os.sep):
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as fh:
                fh.write(data)
            files.append(rel)
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                if not re.search(r"\.(png|jpe?g|gif|webp|ico|svg|pdf|woff2?|ttf|otf|mp3|mp4|wav)$", rel, re.I):
                    merge_flags(flags, {"binary file": {"severity": MEDIUM, "hits": [{"file": rel, "line": 0, "text": "not readable text"}]}})
                continue
            merge_flags(flags, scan_text(text, rel))
            if rel == "SKILL.md":
                fm = frontmatter(text)
                c["skill_md"] = os.path.join(dest, "SKILL.md")
                c["description"] = fm.get("description", "")[:400]
                c["allowed_tools"] = fm.get("allowed-tools", "")
                c["lines"] = text.count("\n") + 1
        if len(inside) > MAX_FILES:
            complete = False
        c["local_copy"] = dest
        c["complete_copy"] = complete
        c["files"] = files
        c["scripts"] = [f for f in files if re.search(r"\.(sh|bash|zsh|py|js|mjs|cjs|ts|rb|pl|ps1|exe|bin)$", f)]
    c["flags"] = flags
    try:
        a = get_json(AUDIT_URL + "?" + urllib.parse.urlencode({"source": "%s/%s" % (owner, repo), "skills": skill}))
        c["third_party_scans"] = {k: v.get("risk") for k, v in (a.get(skill) or {}).items() if isinstance(v, dict)}
    except (urllib.error.URLError, OSError, ValueError, AttributeError):
        c["third_party_scans"] = None
    c["install_copy"] = ("python3 <plugin>/scripts/install_skill.py --install --src %s --dest ~/.claude/skills" % c["local_copy"]
                         if c.get("complete_copy") and c.get("skill_md") else None)
    c["install_npx"] = "DISABLE_TELEMETRY=1 npx skills add %s -g -a claude-code -y" % ref
    c["verdict"], c["reasons"] = verdict(c)
    return c


# ------------------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true", help="offline: clean the keywords and print exactly what --search would send")
    g.add_argument("--search", action="store_true", help="send the cleaned keywords to skills.sh and print the results")
    g.add_argument("--vet", nargs="+", metavar="OWNER/REPO@SKILL", help="check candidates on GitHub and skills.sh")
    ap.add_argument("--keywords", nargs="+", default=[])
    ap.add_argument("--deny", nargs="*", default=[], help="extra words that must never be sent (client, people, product names)")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--owner", help="only this GitHub owner")
    ap.add_argument("--results", help="--vet: the JSON file written by --search, to carry install counts over")
    ap.add_argument("--out", help="folder for results (default ~/already-told-you/skill-search/<date>)")
    ap.add_argument("--projects-dir", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)

    out_root = os.path.expanduser(a.out or os.path.join("~/already-told-you/skill-search", dt.date.today().isoformat()))
    limit = max(1, min(a.limit, 20))
    owner = a.owner.strip().lower() if a.owner else None
    if owner and not re.match(r"^[a-z0-9](?:[a-z0-9-]{0,38})$", owner):
        print("STOP: --owner must be a GitHub owner name")
        return 2

    if a.plan or a.search:
        kws, problems = clean_keywords(a.keywords, a.deny, local_names(a.projects_dir))
        for p in problems:
            print("note: " + p)
        if not kws:
            print("STOP: no usable keywords. Use 2-4 short generic words about the task, e.g. \"playwright\" \"testing\".")
            return 2
        url = search_url(kws, limit, owner)
        if a.plan:
            print("keywords: " + ", ".join(kws))
            print("will send: " + url)
            print("nothing else is sent. The results are then checked on GitHub using only the public repo names they contain.")
            return 0
        try:
            data = get_json(url)
        except (urllib.error.URLError, OSError, ValueError) as e:
            print("STOP: could not reach skills.sh: %s" % e)
            return 3
        res = parse_results(data)
        os.makedirs(out_root, exist_ok=True)
        path = os.path.join(out_root, "search-%s.json" % re.sub(r"[^a-z0-9]+", "-", " ".join(kws)).strip("-"))
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"sent": url, "keywords": kws, "searched": dt.datetime.now().isoformat(timespec="seconds"),
                       "results": res}, fh, indent=2)
        print(json.dumps({"sent": url, "count": len(res), "saved": path,
                          "results": [{k: c[k] for k in ("ref", "installs", "reputable_owner", "same_name_elsewhere", "url")}
                                      for c in res]}, indent=1))
        return 0

    known = {}
    if a.results:
        try:
            for c in json.load(open(os.path.expanduser(a.results), encoding="utf-8")).get("results", []):
                known[c["ref"]] = c
        except (OSError, ValueError, KeyError):
            pass
    os.makedirs(out_root, exist_ok=True)
    report = [vet_one(ref, out_root, known.get(ref)) for ref in a.vet[:6]]
    if len(a.vet) > 6:
        print("note: only the first 6 candidates were checked")
    path = os.path.join(out_root, "vetted.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    slim = []
    for c in report:
        slim.append({k: c.get(k) for k in ("ref", "verdict", "reasons", "installs", "stars", "created", "last_push", "license",
                                            "skill_md", "scripts", "third_party_scans", "complete_copy", "local_copy",
                                            "url", "github", "error")})
        slim[-1]["flags"] = {k: {"severity": SEVERITY_NAME[v["severity"]], "hits": v["hits"][:2]} for k, v in (c.get("flags") or {}).items()}
    print(json.dumps({"saved": path, "candidates": slim}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
