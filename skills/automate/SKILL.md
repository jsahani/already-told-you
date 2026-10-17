---
name: automate
description: Picks one repeated job from section D of your self-improve report and sets up its automation with you - a skill, a skill plus an app connection (MCP), or a scheduled run - always ending with one human approval step before anything is sent, published, paid or deleted.
argument-hint: "[job number or name]"
disable-model-invocation: true
allowed-tools: Read(~/claude-improve/**) Glob Bash(cat ${CLAUDE_SKILL_DIR}/reference/*) Bash(cat ${CLAUDE_PLUGIN_ROOT}/skills/run/reference/*)
---

# self-improve: automate one job

Work through one job at a time, in plain English, and confirm each step with the user. Nothing outside
`~/claude-improve/` is created or changed without a yes.

1. **Pick the job.** Read the newest `~/claude-improve/<YYYY-MM-DD>/findings.json` (Glob). None → "Run
   /self-improve:run first" and stop. Show section D as a numbered list: title, hours/week now → minutes after,
   suggested `how`. Use `$ARGUMENTS` if it names one; otherwise ask which.
2. **Agree the shape.** Restate the job as: trigger (when / who starts it) → what Claude does → what comes out →
   where the human approves. Confirm the automation type using the options below; change it if the user prefers.
   Ask only what is missing (which folder, which app, what time, where the output should go).
3. **Make the skill.** Every automation runs through a skill. If section C drafted one for this job, start from
   `<report>/skills/<name>/SKILL.md`; otherwise write a new draft there with the same rules (frontmatter `name` +
   `description` quoting the user's words; numbered steps; last step = approval). Show it, refine it with the user,
   then install it the same way /self-improve:install-skills does (show, ask where, ask yes).
   **The approval step:** if the job sends, publishes, posts, pays or deletes, the skill prepares the result and
   stops. Scheduled runs have nobody to ask, so in a scheduled run the skill only writes a draft to a folder (or a
   draft in the app, e.g. an email draft) and the user approves it later. Never let a scheduled run send.
4. **Connect / schedule it** - only what the chosen type needs:
   - `skill + MCP`: name the app connection the job needs. If it is not connected, tell the user how
     (`claude mcp add ...` from the app's docs, `/mcp` to check, or a claude.ai connector). Never paste secrets into
     files or chat; API keys belong in the user's own secret store or environment.
   - `schedule (desktop)`: give step-by-step clicks for the Claude Code Desktop app → Routines → new local task,
     with the exact prompt to paste (`/<skill-name>` plus any detail), the schedule, the project folder, and the
     permission choice. Remind: it runs only while the app is open and the computer awake.
   - `schedule (routine)`: give the exact line to type, e.g. `/schedule every Monday at 9am, run /<skill-name> ...`,
     and say it runs in the cloud on a fresh copy of a GitHub repo with connectors - no local files.
   - `schedule (cron)` on macOS: fill in the launchd template below. Find the claude path with `command -v claude`
     (ask before running). Write the filled plist to `~/claude-improve/automation/<label>.plist` first and show it.
     After a yes, copy it to `~/Library/LaunchAgents/` and load it with
     `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/<label>.plist` (each command asks for permission).
     `--allowedTools` in it must list only what the job needs - never `--dangerously-skip-permissions`.
     On Linux, show the equivalent crontab line for the user to add with `crontab -e`.
5. **Try it once** if the user agrees: run the skill now by hand and show the draft it produced.
6. **Finish.** Summarise what was set up, where the approval happens, the time it should save
   (hours/week now → minutes after, from the report), and exactly how to switch it off.

---

!`cat ${CLAUDE_PLUGIN_ROOT}/skills/run/reference/automation-options.md`

---

!`cat ${CLAUDE_SKILL_DIR}/reference/launchd-template.plist`
