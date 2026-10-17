---
name: run
description: Reads your whole Claude Code history on this computer and writes a report on where Claude keeps going wrong, what you keep re-explaining, which skills you should already have (with first drafts written), and which jobs you repeat by hand and how to automate them. Dry run - it only writes into ~/claude-improve/. Run it with /self-improve:run, or /self-improve:run here for the current project only.
argument-hint: "[here]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract.py *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render.py *) Bash(cat ${CLAUDE_SKILL_DIR}/reference/*) Read(~/claude-improve/**) Write(~/claude-improve/**) Edit(~/claude-improve/**) Glob Grep
---

# self-improve: run

You are reviewing the user's own Claude Code history to help them work better with Claude. Everything stays on
this computer: you read the digest the bundled extractor makes, and you write only inside `~/claude-improve/`.

**Run the two scripts exactly as written below**, with the full folder path typed out: no shell variables, no
`cd`, no `&&` or `;`. Only that exact form is pre-approved; any other form stops for a permission prompt.

**Dry run, always.** In this command never edit a CLAUDE.md, never install a skill, never change settings, never
write outside `~/claude-improve/<date>/`. The user approves changes later with the other commands.

Arguments: `$ARGUMENTS`

## 1. Extract (one command)

If the arguments say `here`, `this project` or similar, analyse only the current project; otherwise all projects.

- All projects: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract.py --report-root ~/claude-improve`
- This project only: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract.py --report-root ~/claude-improve --project "${CLAUDE_PROJECT_DIR}"`

It streams `~/.claude/projects/` read-only and prints a JSON line with the numbers, then `report folder: <DIR>` and
`previous report compared: <path or none>`. Use that `<DIR>` (it is `~/claude-improve/<YYYY-MM-DD>`) for everything
below. If it prints "No Claude Code history found", tell the user and stop. If fewer than 5 sessions were analysed,
say the report will be thin and continue.

## 2. History check (tell the user straight away)

From the printed JSON: Claude Code deletes transcripts after `cleanupPeriodDays` days, 30 by default. Tell the user
the oldest session date found. If `history_warning` is set (the setting is missing or under 365), warn them that
older sessions are already gone or soon will be and that `/self-improve:keep-history` keeps a year.

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
- `/self-improve:install-skills` - review the drafted skills and install the ones you want
- `/self-improve:apply-rules` - add the section B rules to the right CLAUDE.md (you see the diff first)
- `/self-improve:automate` - set up one job from section D, with an approval step
- `/self-improve:keep-history` - only if the history check warned you

Remind them: this was a dry run, nothing was installed or changed.

---

!`cat ${CLAUDE_SKILL_DIR}/reference/findings-schema.md`

---

!`cat ${CLAUDE_SKILL_DIR}/reference/skill-template.md`

---

!`cat ${CLAUDE_SKILL_DIR}/reference/automation-options.md`
