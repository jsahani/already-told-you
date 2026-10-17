## findings.json format

One JSON object. `render.py` checks it and refuses missing required fields (`generated`, `sections`, and per
finding `title`, `count`, `quotes`). Quotes are verbatim, short (under 200 characters), at most 2 per finding.

```json
{
  "generated": "YYYY-MM-DD",
  "scope": "all projects",
  "headline": "One or two plain sentences: the biggest pattern and the time it costs.",
  "history": {"warning": "only if the extractor printed a history_warning", "note": "otherwise: kept N days, oldest session YYYY-MM-DD"},
  "sections": {
    "A": [{"id": "a-short-id", "title": "Says it's done before checking", "count": 14,
           "detail": "What happens, in one or two sentences.",
           "fix": "One concrete rule or habit that stops it.",
           "quotes": [{"text": "verbatim quote", "date": "YYYY-MM-DD", "project": "name"}],
           "keywords": ["phrases the user types about it"]}],
    "B": [{"id": "b-short-id", "title": "...", "count": 9,
           "rule": "The exact CLAUDE.md instruction to add.",
           "file": "~/.claude/CLAUDE.md or /absolute/project/path/CLAUDE.md",
           "quotes": [], "keywords": []}],
    "C": [{"id": "c-short-id", "name": "skill-name", "title": "What the skill does", "count": 11,
           "minutes_each": 12, "score": 132, "draft": "skills/skill-name/SKILL.md (only for drafted ones)",
           "quotes": [], "keywords": []}],
    "D": [{"id": "d-short-id", "title": "...", "count": 5, "per_week": 1.0,
           "hours_per_week_now": 1.5, "minutes_after": 10,
           "how": "skill | skill + MCP | schedule (desktop) | schedule (routine) | schedule (cron)",
           "automation": "One sentence: what runs, when, and where the human approves.",
           "steps": ["step 1", "step 2"],
           "quotes": [], "keywords": []}]
  },
  "since_last": {"previous": "YYYY-MM-DD",
                 "fixed": [{"title": "...", "detail": "before 6, after 0"}],
                 "better": [], "still": []},
  "summary": "Two or three sentences.",
  "next": ["/self-improve:install-skills — review and install the drafted skills",
           "/self-improve:apply-rules — add the section B rules to your CLAUDE.md",
           "/self-improve:automate — set up one job from section D"]
}
```

- `count` in B is the number of sessions; elsewhere the number of times.
- `minutes_after` is minutes **per week** after automating (usually review and approval time).
- Omit `since_last` when there was no previous report. Use `[]` for an empty section, never drop the key.
- Each `next` entry is `command — what it does` (with the long dash).
