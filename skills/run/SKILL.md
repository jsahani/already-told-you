---
name: run
description: Reads your whole Claude Code history (the transcripts in ~/.claude/projects) and writes a report on where Claude keeps going wrong, what you keep re-explaining, which skills you should already have (with first drafts written), and which jobs you repeat by hand and how to automate them. Dry run - it only writes into ~/already-told-you/. Run it with /already-told-you:run, or /already-told-you:run here for the current project only.
argument-hint: "[here]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract.py *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render.py *) Read(~/already-told-you/**) Write(~/already-told-you/**) Edit(~/already-told-you/**) Glob Grep
---

# Already Told You: run

You are reviewing the user's own Claude Code history to help them work better with Claude. The bundled extractor
runs on this computer and writes only to `~/already-told-you/`; you, the user's own Claude Code session, do the
analysis by reading its digest; and you write only inside `~/already-told-you/`. If the user asks where their data
goes, say exactly that: no account, no dashboard, no third-party service and no network calls of the plugin's own
in this command; you read the extracts the same way you read anything in a Claude Code session, through Anthropic.
(The only command that uses the network is the opt-in `/already-told-you:find-skills`, which sends only search
keywords the user approves. Never run it from here.)

**Run the two scripts exactly as written below**, with the full folder path typed out: no shell variables, no
`cd`, no `&&` or `;`. Only that exact form is pre-approved; any other form stops for a permission prompt.

**Dry run, always.** In this command never edit a CLAUDE.md, never install a skill, never change settings, never
write outside `~/already-told-you/<date>/`. The user approves changes later with the other commands.

Arguments: `$ARGUMENTS`

## 1. Extract (one command)

If the arguments say `here`, `this project` or similar, analyse only the current project; otherwise all projects.

- All projects: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract.py --report-root ~/already-told-you`
- This project only: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract.py --report-root ~/already-told-you --project "${CLAUDE_PROJECT_DIR}"`

It streams `~/.claude/projects/` read-only and prints a JSON line with the numbers, then `report folder: <DIR>` and
`previous report compared: <path or none>`. Use that `<DIR>` (it is `~/already-told-you/<YYYY-MM-DD>`) for everything
below. If it prints "No Claude Code history found", tell the user and stop. If fewer than 5 sessions were analysed,
say the report will be thin and continue.

## 2. History check (tell the user straight away)

From the printed JSON: Claude Code deletes transcripts after `cleanupPeriodDays` days, 30 by default. Tell the user
the oldest session date found. If `history_warning` is set (the setting is missing or under 365), warn them that
older sessions are already gone or soon will be and that `/already-told-you:keep-history` keeps a year.

## 3. Read the evidence

Read `<DIR>/data/digest.md` in full. It has: numbers, templates/app prompts, a projects table, repeated tasks
(clusters with counts, minutes, dates, quotes), repeated context, repeated tool errors, corrections (the user's
push-back right after Claude's turn, with what Claude had said), and a session index.

**Large history:** if `sessions_analysed` is over 40 or the digest says it was trimmed, also use subagents so your
own context never overflows. Split the files in `<DIR>/data/chunks/` into groups of about 150k characters (the
digest lists them; the projects table shows their size), and start one subagent per group, all in one message,
**in the foreground** (`run_in_background: false`): you need their results before you can continue, and this
whole command must finish in one turn. Each subagent gets this task: "Read these files with the Read tool (no shell commands): <list>. They are a user's own
messages to Claude Code, one section per session, `[C]` marks a likely correction. Return at most 900 words:
(A) mistakes Claude repeats, (B) context the user re-explains, (C) tasks they ask for again and again,
(D) recurring jobs with a rhythm (daily/weekly), each with a count, 1-2 verbatim quotes with their date and
project, and nothing you cannot quote." Merge their answers with the digest; the digest's numbers win.

## 4. Decide the findings

Be precise and honest. Every finding needs a count, 1-2 short **verbatim** quotes (as they appear in the digest or
chunks, with date and project) and must be backed by at least 2 sessions. Never invent numbers; derive them from
the digest. Prefer 3-5 strong findings per section over many weak ones. Write in plain English for a
non-programmer. Do not quote secrets, keys or personal data (the extractor already masks most).

- **A · Where it keeps going wrong** - group the corrections and repeated tool errors by root cause (for example
  "says it's done without checking", "ignores the stated tool", "changes things it wasn't asked to"). For each:
  `detail` (what happens), `fix` (one concrete rule or habit that would stop it).
- **B · What you keep explaining** - from repeated context, corrections that restate a preference, and habitual
  pastes in the templates list (ignore app prompts the user never typed). For each give `rule`: the exact text to
  add, written as a CLAUDE.md instruction, and `file`: `~/.claude/CLAUDE.md` if it applies across 2+ projects,
  otherwise `<project path>/CLAUDE.md` (paths are in the projects table).
- **C · Skills you should already have** - repeated tasks ranked by `score = occurrences × average minutes`.
  Write first drafts for the top 3 (at most 5) into `<DIR>/skills/<skill-name>/SKILL.md`, following the
  **Skill draft template** below exactly. Set `draft` to `skills/<skill-name>/SKILL.md`.
- **D · Jobs you repeat by hand** - recurring jobs with a rhythm or a fixed recipe. `per_week` from the digest's
  days/week, `hours_per_week_now = per_week × average minutes / 60`, `minutes_after` = realistic minutes per week
  once automated (usually the time to review and approve). Pick `how` from the **Automation options** below
  (only the options listed there exist) and give 2-4 `steps`.

If `<DIR>/data/digest.md` has a "Previous findings re-checked" section, fill `since_last` from it: `fixed`,
`better` and `still` lists with the finding titles and the before/after numbers as `detail`.

## 5. Write the report

1. Write `<DIR>/findings.json` following the **findings.json format** below exactly. Give every
   finding 2-4 `keywords`: short phrases the user actually types about it, so the next run can check if it is fixed.
2. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render.py --findings <DIR>/findings.json --stats <DIR>/data/stats.json --out <DIR>`.
   If it reports problems, fix `findings.json` and run it again.
3. Check with Glob that `<DIR>/report.md`, `<DIR>/report.html` and each drafted `SKILL.md` exist.

## 6. Tell the user

End with a short summary (at most 10 lines, plain English): sessions analysed and date range, the single biggest
finding in each of A-D with its number, the hours per week they could win back, the drafted skill names, and the
history warning if any. Then the report path and these next commands:

- `open <DIR>/report.html` - read the full report (macOS; on Linux `xdg-open`)
- `/already-told-you:install-skills` - review the drafted skills and install the ones you want
- `/already-told-you:find-skills report` - optional: check whether a vetted ready-made skill already exists for
  the skills and jobs in sections C and D (asks first; sends only short search keywords you approve)
- `/already-told-you:apply-rules` - add the section B rules to the right CLAUDE.md (you see the diff first)
- `/already-told-you:automate` - set up one job from section D, with an approval step
- `/already-told-you:keep-history` - only if the history check warned you

Remind them: this was a dry run, nothing was installed or changed.

---

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
  "next": ["/already-told-you:install-skills — review and install the drafted skills",
           "/already-told-you:apply-rules — add the section B rules to your CLAUDE.md",
           "/already-told-you:automate — set up one job from section D"]
}
```

- `count` in B is the number of sessions; elsewhere the number of times.
- `minutes_after` is minutes **per week** after automating (usually review and approval time).
- Omit `since_last` when there was no previous report. Use `[]` for an empty section, never drop the key.
- Never add a `match` field to C or D items: only `/already-told-you:find-skills report` sets it, after the user
  opts in to a search. If the previous report's items had one, do not copy it over.
- Each `next` entry is `command — what it does` (with the long dash).

---

## Skill draft template (for section C drafts)

Write each draft to `<DIR>/skills/<skill-name>/SKILL.md`. Rules:

- `<skill-name>`: lowercase letters, digits and hyphens, at most 64 characters, says what it does
  (`weekly-client-update`, `ship-reel-cover`). Never the name of a built-in command (`/review`, `/init`, `/plan`...).
- `description`: at most 1,024 characters. Start with what the skill does, then "Use when the user asks to ..."
  followed by 2-3 phrasings **quoted from the user's real messages** so Claude recognises the request when they
  say it again.
- The body is the recipe the user kept explaining: inputs to ask for if missing, numbered steps with the tools,
  folders, file names and quality checks the history shows they want, and how to show the result.
- The last step is always an approval gate when the job sends, publishes, posts, pays, deletes or overwrites
  anything: show the result and wait for an explicit "yes" first.
- Facts only from the history. Where you are unsure, write `TODO (check):` so the user fills it in when they
  review the draft. Keep it under 80 lines.

```markdown
---
name: weekly-client-update
description: Drafts the weekly client status update from this week's git history and roadmap cards. Use when the user asks to "write the weekly update for the client", "do the Monday report" or "summarise what we shipped this week".
---

# Weekly client update

1. Ask which client if it is not clear from the project.
2. Collect this week's work: `git log --since="last monday" --oneline` and the roadmap cards moved to done.
3. Write the update in the user's format: three sections - Shipped, In progress, Needs your input. Plain English, no jargon, under 200 words.
4. Save it to `updates/<YYYY-MM-DD>.md` and show it.
5. **Approval:** ask "Send this to the client?" and do nothing more until the user says yes. Never send on your own.
```

---

## Automation options (checked against code.claude.com/docs, October 2026 - use only these)

Pick the lightest option that fully does the job. The `how` field takes one of: `skill`, `skill + MCP`,
`schedule (desktop)`, `schedule (routine)`, `schedule (cron)`.

1. **`skill`** - the job is the same recipe every time, started by the user. A skill in `~/.claude/skills/<name>/`
   (all projects) or `<project>/.claude/skills/<name>/` (one project) turns a 15-minute explain-and-steer into one
   `/<name>` command. Usually also drafted in section C.
2. **`skill + MCP`** - the recipe needs another app (email, calendar, Notion, Slack, a database...). The skill
   calls that app through an MCP server. The user connects it with `claude mcp add ...` or `/mcp`, or uses a
   claude.ai connector. Only name a specific app if the history shows they use it.
3. **`schedule (desktop)`** - it should happen on a rhythm and needs local files. *Desktop scheduled tasks* in the
   Claude Code Desktop app (Routines page → new local task) start a new session at the chosen time and frequency.
   Runs on the user's machine, only while the app is open and the computer is awake; permissions are set per task.
4. **`schedule (routine)`** - it should happen on a rhythm and does not need local files (it works on a GitHub
   repo or through connectors). *Routines* run on Anthropic's cloud even when the laptop is closed; create one with
   `/schedule` in Claude Code (e.g. `/schedule every Monday at 9am, ...`) or at claude.ai/code/routines. Research
   preview, Pro/Max/Team/Enterprise plans, minimum interval one hour.
5. **`schedule (cron)`** - fallback without the Desktop app: macOS `launchd` (or `cron`) runs
   `claude -p "/<skill-name>"` headless at a set time, with `--allowedTools` listing only what the job needs.

Not an option for a recurring job: `/loop` and session cron tasks only run while a Claude Code session is open,
and expire after seven days.

**Approval rule for every automation:** anything that sends, publishes, pays or deletes stops for one human
approval step (the run prepares a draft or a preview; the user says yes before it goes out).
