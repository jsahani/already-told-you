#!/usr/bin/env python3
"""Already Told You - renderer: findings.json (+ stats.json) -> report.md and report.html.

The HTML is one self-contained file (inline CSS, no fonts or scripts from the internet).
Python 3 standard library only.

  python3 render.py --findings <dir>/findings.json --stats <dir>/data/stats.json --out <dir>
"""
import argparse
import html
import json
import os
import sys

SECTION_META = {
    "A": ("Where it keeps going wrong", "Repeated corrections and mistakes Claude repeats.", "#e5484d"),
    "B": ("What you keep explaining", "Context you re-explain across sessions, and the rule that would stop it.", "#f5a524"),
    "C": ("Skills you should already have", "Ranked by how often × how long. First drafts are written for the top ones.", "#3e63dd"),
    "D": ("Jobs you repeat by hand", "How often, the time it costs now, and how to get it down to minutes.", "#12a594"),
}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# The plugin was called "self-improve" before it became "Already Told You". Findings written by that version
# name the old commands and folder; show them under the current names.
LEGACY_NAMES = (("/self-improve:", "/already-told-you:"), ("~/claude-improve/", "~/already-told-you/"))


def modernise(f):
    text = json.dumps(f, ensure_ascii=False)
    for old, new in LEGACY_NAMES:
        text = text.replace(old, new)
    return json.loads(text)


def num(v, default=0):
    try:
        return float(v)
    except Exception:
        return default


def fmt_hours(h):
    h = num(h)
    if h < 1:
        return "%d min" % round(h * 60)
    return ("%.1f h" % h).replace(".0 h", " h")


def validate(f):
    problems = []
    for key in ("generated", "sections"):
        if key not in f:
            problems.append("missing '%s'" % key)
    for sec in "ABCD":
        for i, item in enumerate((f.get("sections") or {}).get(sec, [])):
            for key in ("title", "count", "quotes"):
                if key not in item:
                    problems.append("section %s item %d: missing '%s'" % (sec, i + 1, key))
    return problems


# --------------------------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------------------------

def quotes_md(item):
    out = []
    for q in (item.get("quotes") or [])[:2]:
        out.append('  > "%s"  \n  > — %s · %s\n' % (q.get("text", "").replace("\n", " "), q.get("date", "?"), q.get("project", "?")))
    return "".join(out)


def render_md(f, st):
    L = []
    L.append("# Your Claude Code, reviewed\n\n")
    L.append("*%s · %s · made by Already Told You (local extractor + your own Claude Code session) on %s. Dry run: nothing was installed or changed.*\n\n" % (
        f.get("scope") or st.get("scope", "all projects"), "%s → %s" % (st.get("analysed_from"), st.get("analysed_to")), f.get("generated")))
    if f.get("headline"):
        L.append("**%s**\n\n" % f["headline"])
    L.append("| Sessions analysed | Your messages | Hours with Claude | Corrections | Skills drafted | Time to win back |\n|---|---|---|---|---|---|\n")
    L.append("| %s of %s | %s | %s | %s | %d | %s/week |\n\n" % (
        st.get("sessions_analysed"), st.get("sessions_total"), st.get("your_messages"), st.get("active_hours"), st.get("corrections"),
        len([c for c in f["sections"].get("C", []) if c.get("draft")]), fmt_hours(saved_hours(f))))
    hist = f.get("history") or {}
    if hist.get("warning"):
        L.append("> ⚠️ **History check:** %s\n\n" % hist["warning"])
    elif hist.get("note"):
        L.append("> History check: %s\n\n" % hist["note"])

    since = f.get("since_last")
    if since:
        L.append("## Since last time (%s)\n\n" % since.get("previous", "?"))
        for k, label in (("fixed", "✅ Fixed"), ("better", "↘︎ Better"), ("still", "⏳ Still happening")):
            for x in since.get(k) or []:
                L.append("- %s: **%s** %s\n" % (label, x.get("title"), ("— " + x["detail"]) if x.get("detail") else ""))
        L.append("\n")

    for sec in "ABCD":
        title, sub, _ = SECTION_META[sec]
        items = f["sections"].get(sec, [])
        L.append("## %s · %s\n\n*%s*\n\n" % (sec, title, sub))
        if not items:
            L.append("Nothing strong enough to report yet.\n\n")
        for i, it in enumerate(items, 1):
            L.append("### %s%d. %s  (%s×)\n\n" % (sec, i, it["title"], it.get("count")))
            if it.get("detail"):
                L.append("%s\n\n" % it["detail"])
            if sec == "B":
                L.append("**Proposed rule** for `%s`:\n\n> %s\n\n" % (it.get("file", "CLAUDE.md"), it.get("rule", "")))
            if sec == "C":
                L.append("~%s min each · score %s%s\n\n" % (it.get("minutes_each", "?"), it.get("score", "?"),
                                                          (" · **draft written:** `%s`" % it["draft"]) if it.get("draft") else ""))
            if sec == "D":
                L.append("**%s/week now → %s after** · %s · how: **%s**\n\n" % (
                    fmt_hours(it.get("hours_per_week_now")), "%s min/week" % it.get("minutes_after", "?"),
                    ("%s×/week" % it["per_week"]) if it.get("per_week") is not None else "", it.get("how", "")))
                if it.get("automation"):
                    L.append("%s\n\n" % it["automation"])
                for s in it.get("steps") or []:
                    L.append("1. %s\n" % s)
                if it.get("steps"):
                    L.append("\n")
            if sec == "A" and it.get("fix"):
                L.append("**Fix:** %s\n\n" % it["fix"])
            L.append(quotes_md(it))
            L.append("\n")
    if f.get("summary"):
        L.append("## Summary\n\n%s\n\n" % f["summary"])
    if f.get("next"):
        L.append("## Next\n\n")
        for n in f["next"]:
            L.append("- %s\n" % n)
        L.append("\n")
    L.append("---\nMade with Already Told You, a free Claude Code plugin by @jsahani.ai. Dry run: nothing was installed or changed.\n")
    return "".join(L)


def saved_hours(f):
    """Hours per week won back across section D: hours_per_week_now minus minutes_after (minutes per week)."""
    total = 0.0
    for d in f["sections"].get("D", []):
        total += max(0.0, num(d.get("hours_per_week_now")) - num(d.get("minutes_after")) / 60.0)
    return total


# --------------------------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------------------------

CSS = """
:root{--bg:#f7f6f3;--card:#fff;--ink:#16161a;--muted:#6b6b76;--line:#e7e5df;--soft:#f1efe9}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:56px 32px 80px}
.eyebrow{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
h1{font-size:56px;line-height:1.05;letter-spacing:-.03em;margin:10px 0 14px;font-weight:800}
.lede{font-size:21px;color:#3a3a44;max-width:820px;margin:0}
.meta{margin-top:14px;color:var(--muted);font-size:15px}
.pill{display:inline-block;padding:3px 10px;border-radius:999px;background:var(--soft);border:1px solid var(--line);font-size:13px;color:#4a4a55;margin:0 6px 6px 0}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:36px 0 18px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 20px 18px}
.stat b{display:block;font-size:44px;line-height:1;letter-spacing:-.03em;font-weight:800}
.stat span{display:block;margin-top:8px;color:var(--muted);font-size:14px}
.stat.hl{background:#16161a;color:#fff;border-color:#16161a}
.stat.hl span{color:#b9b9c4}
.warn{background:#fff7e6;border:1px solid #f6d58e;color:#6b4a00;border-radius:14px;padding:14px 18px;margin:14px 0}
.ok{background:#eefaf4;border:1px solid #b6e6cc;color:#1e5c3d;border-radius:14px;padding:12px 18px;margin:14px 0;font-size:15px}
nav{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:26px 0 8px}
nav a{text-decoration:none;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:9px 12px;font-weight:600;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
nav a i{font-style:normal;display:inline-grid;place-items:center;width:22px;height:22px;border-radius:7px;color:#fff;font-size:12px;margin-right:8px}
section{margin-top:56px}
.sh{display:flex;align-items:center;gap:16px;margin-bottom:6px}
.badge{width:46px;height:46px;border-radius:14px;display:grid;place-items:center;color:#fff;font-weight:800;font-size:22px;flex:none}
h2{font-size:34px;letter-spacing:-.02em;margin:0;line-height:1.1}
.sub{color:var(--muted);margin:6px 0 20px 62px}
.card{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:24px 26px;margin:14px 0;display:grid;grid-template-columns:92px 1fr;gap:22px}
.count{font-size:46px;font-weight:800;letter-spacing:-.03em;line-height:1}
.count small{display:block;font-size:13px;font-weight:600;color:var(--muted);letter-spacing:0;margin-top:6px}
h3{margin:0 0 6px;font-size:22px;letter-spacing:-.01em;line-height:1.25}
.detail{margin:0 0 10px;color:#33333d}
blockquote{margin:12px 0 0;padding:12px 16px;background:var(--soft);border-radius:12px;border-left:4px solid var(--accent);font-size:16px}
blockquote cite{display:block;font-style:normal;color:var(--muted);font-size:13px;margin-top:6px}
.fix{margin-top:12px;padding:12px 16px;border:1px dashed var(--line);border-radius:12px;font-size:16px}
.fix b{color:var(--accent)}
.rule{margin-top:10px;padding:14px 16px;border-radius:12px;background:#16161a;color:#f3f3f6;font:15px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap}
.file{font:13px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted);margin-top:8px}
.big{display:flex;align-items:baseline;gap:12px;margin:6px 0 10px;flex-wrap:wrap}
.big .now{font-size:30px;font-weight:800;letter-spacing:-.02em;color:#c2410c}
.big .arrow{font-size:24px;color:var(--muted)}
.big .after{font-size:30px;font-weight:800;letter-spacing:-.02em;color:#0f766e}
.big .per{color:var(--muted);font-size:15px}
.how{display:inline-block;background:var(--accent);color:#fff;border-radius:8px;padding:3px 10px;font-size:13px;font-weight:700;letter-spacing:.02em;text-transform:uppercase}
ol.steps{margin:10px 0 0;padding-left:22px}
ol.steps li{margin:4px 0}
.draft{display:inline-flex;gap:8px;align-items:center;margin-top:10px;background:#eef2ff;color:#2f3fa8;border-radius:10px;padding:6px 12px;font:14px ui-monospace,SFMono-Regular,Menlo,monospace}
.since{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.since div{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 18px}
.since h4{margin:0 0 8px;font-size:15px}
.since ul{margin:0;padding-left:18px;font-size:15px}
.next{background:#16161a;color:#fff;border-radius:22px;padding:28px 30px;margin-top:56px}
.next h2{color:#fff}
.next p{color:#d6d6de}
.next code{display:block;font:16px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;background:#26262d;border-radius:10px;padding:10px 14px;margin:8px 0;color:#fff}
.next code span{color:#9b9ba8}
footer{margin-top:28px;color:var(--muted);font-size:14px;text-align:center}
.empty{color:var(--muted);font-style:italic;margin-left:62px}
@media (max-width:900px){nav{grid-template-columns:repeat(2,1fr)}.stats{grid-template-columns:repeat(2,1fr)}.card{grid-template-columns:1fr}.since{grid-template-columns:1fr}h1{font-size:40px}}
"""


def big(v):
    """Whole numbers for the big stat cards once a value reaches 10 (143.7 -> 144)."""
    x = num(v, None)
    if x is None:
        return v
    return "%d" % round(x) if x >= 10 else ("%.1f" % x).rstrip("0").rstrip(".")


def e(s):
    return html.escape(str(s if s is not None else ""))


def quotes_html(item):
    out = []
    for q in (item.get("quotes") or [])[:2]:
        out.append('<blockquote>“%s”<cite>%s · %s</cite></blockquote>' % (e(q.get("text", "")), e(q.get("date", "")), e(q.get("project", ""))))
    return "".join(out)


def card(sec, it):
    unit = {"A": "times", "B": "sessions", "C": "times", "D": "times"}[sec]
    body = ['<h3>%s</h3>' % e(it["title"])]
    if it.get("detail"):
        body.append('<p class="detail">%s</p>' % e(it["detail"]))
    if sec == "D":
        body.append('<div class="big"><span class="now">%s/wk</span><span class="arrow">→</span><span class="after">%s min/wk</span>'
                    '<span class="per">%s</span></div>' % (
                        e(fmt_hours(it.get("hours_per_week_now"))), e(it.get("minutes_after", "?")),
                        e(("about %s×/week" % it["per_week"]) if it.get("per_week") is not None else "")))
        if it.get("how"):
            body.append('<span class="how">%s</span>' % e(it["how"]))
        if it.get("automation"):
            body.append('<p class="detail" style="margin-top:10px">%s</p>' % e(it["automation"]))
        if it.get("steps"):
            body.append('<ol class="steps">%s</ol>' % "".join("<li>%s</li>" % e(s) for s in it["steps"]))
    if sec == "C":
        meta = []
        if it.get("minutes_each") is not None:
            meta.append("~%s min each" % e(it["minutes_each"]))
        if it.get("score") is not None:
            meta.append("score %s" % e(it["score"]))
        if meta:
            body.append('<p class="detail">%s</p>' % " · ".join(meta))
        if it.get("draft"):
            body.append('<div class="draft">✓ draft written · %s</div>' % e(it["draft"]))
    if sec == "B" and it.get("rule"):
        body.append('<div class="rule">%s</div><div class="file">→ %s</div>' % (e(it["rule"]), e(it.get("file", "CLAUDE.md"))))
    if sec == "A" and it.get("fix"):
        body.append('<div class="fix"><b>Fix:</b> %s</div>' % e(it["fix"]))
    body.append(quotes_html(it))
    return '<div class="card"><div class="count">%s<small>%s</small></div><div>%s</div></div>' % (e(it.get("count")), unit, "".join(body))


def render_html(f, st):
    drafted = len([c for c in f["sections"].get("C", []) if c.get("draft")])
    hist = f.get("history") or {}
    H = []
    H.append('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    H.append("<title>Your Claude Code, reviewed · %s</title><style>%s</style></head><body><div class=\"wrap\">" % (e(f.get("generated")), CSS))
    H.append('<div class="eyebrow">Already Told You · report · %s</div>' % e(f.get("generated")))
    H.append("<h1>Your Claude Code,<br>reviewed.</h1>")
    if f.get("headline"):
        H.append('<p class="lede">%s</p>' % e(f["headline"]))
    H.append('<div class="meta"><span class="pill">%s</span><span class="pill">%s → %s</span><span class="pill">%s projects</span>'
             '<span class="pill">no account · no third-party service</span></div>' % (
                 e(f.get("scope") or st.get("scope", "all projects")), e(st.get("analysed_from")), e(st.get("analysed_to")), e(st.get("projects"))))
    H.append('<div class="stats">')
    for val, label, hl in (
            (st.get("sessions_analysed"), "sessions analysed (of %s)" % st.get("sessions_total"), False),
            (big(st.get("active_hours")), "hours working with Claude", False),
            (st.get("corrections"), "times you corrected Claude", False),
            (drafted, "skills drafted for you", False),
            (fmt_hours(saved_hours(f)), "per week to win back", True)):
        H.append('<div class="stat%s"><b>%s</b><span>%s</span></div>' % (" hl" if hl else "", e(val), e(label)))
    H.append("</div>")
    if hist.get("warning"):
        H.append('<div class="warn">⚠️ <b>History check.</b> %s</div>' % e(hist["warning"]))
    elif hist.get("note"):
        H.append('<div class="ok">History check: %s</div>' % e(hist["note"]))
    H.append("<nav>")
    short_labels = {"A": "Where it goes wrong", "B": "What you re-explain", "C": "Skills to have", "D": "Jobs to automate"}
    for sec in "ABCD":
        H.append('<a href="#%s"><i style="background:%s">%s</i>%s</a>' % (sec, SECTION_META[sec][2], sec, e(short_labels[sec])))
    H.append("</nav>")

    since = f.get("since_last")
    if since:
        H.append('<section id="since"><div class="sh"><div class="badge" style="background:#16161a">↺</div><h2>Since last time</h2></div>'
                 '<p class="sub">Compared with the report from %s.</p><div class="since">' % e(since.get("previous", "?")))
        for k, label in (("fixed", "✅ Fixed"), ("better", "↘︎ Better"), ("still", "⏳ Still happening")):
            xs = since.get(k) or []
            H.append("<div><h4>%s · %d</h4><ul>%s</ul></div>" % (label, len(xs), "".join(
                "<li><b>%s</b>%s</li>" % (e(x.get("title")), (" — " + e(x["detail"])) if x.get("detail") else "") for x in xs) or "<li>none</li>"))
        H.append("</div></section>")

    for sec in "ABCD":
        title, sub, color = SECTION_META[sec]
        H.append('<section id="%s" style="--accent:%s"><div class="sh"><div class="badge" style="background:%s">%s</div><h2>%s</h2></div>'
                 '<p class="sub">%s</p>' % (sec, color, color, sec, e(title), e(sub)))
        items = f["sections"].get(sec, [])
        if not items:
            H.append('<p class="empty">Nothing strong enough to report yet.</p>')
        for it in items:
            H.append(card(sec, it))
        H.append("</section>")

    H.append('<div class="next"><h2>What next</h2>')
    if f.get("summary"):
        H.append("<p>%s</p>" % e(f["summary"]))
    for n in f.get("next") or []:
        cmd, _, rest = str(n).partition(" — ")
        H.append("<code>%s%s</code>" % (e(cmd), (" <span>— %s</span>" % e(rest)) if rest else ""))
    H.append("</div>")
    H.append("<footer>Made with <b>Already Told You</b>, a free Claude Code plugin by @jsahani.ai · "
             "a local extractor plus your own Claude Code session · no account, no third-party service · "
             "dry run: nothing was installed or changed · %s sessions, %s MB of history read</footer>" % (
                 e(st.get("sessions_total")), e(round(num(st.get("bytes_read")) / 1e6))))
    H.append("</div></body></html>")
    return "".join(H)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render Already Told You findings to report.md + report.html")
    ap.add_argument("--findings", required=True)
    ap.add_argument("--stats", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    f = modernise(load(os.path.expanduser(a.findings)))
    st = load(os.path.expanduser(a.stats))
    problems = validate(f)
    if problems:
        print("findings.json has problems:\n- " + "\n- ".join(problems), file=sys.stderr)
        return 1
    for sec in "ABCD":
        f["sections"].setdefault(sec, [])
    out = os.path.expanduser(a.out)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(render_md(f, st))
    with open(os.path.join(out, "report.html"), "w", encoding="utf-8") as fh:
        fh.write(render_html(f, st))
    print("wrote %s and %s" % (os.path.join(out, "report.md"), os.path.join(out, "report.html")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
