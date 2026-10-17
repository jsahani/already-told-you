---
name: automate
description: Picks one repeated job from section D of your self-improve report and sets up its automation with you - a skill, a skill plus an app connection (MCP), or a scheduled run - always ending with one human approval step before anything is sent, published, paid or deleted.
argument-hint: "[job number or name]"
disable-model-invocation: true
allowed-tools:
  - Read(~/claude-improve/**)
  - Glob
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/install_skill.py --check *)
  - Bash(plutil -lint *)
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
   then install it with the bundled installer, never by writing into a skills folder yourself: ask where
   (`~/.claude/skills` = all projects, `${CLAUDE_PROJECT_DIR}/.claude/skills` = this project), run
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/install_skill.py --check --src <report>/skills/<name> --dest <dest>`,
   and after a yes `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/install_skill.py --install --src <report>/skills/<name> --dest <dest>`
   (it asks for permission and never replaces an existing skill unless the user agrees to `--force`).
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

---

## launchd template (schedule (cron) on macOS)

Fill in every `{{...}}` and save it as `<label>.plist`:

- `{{label}}` - e.g. `com.self-improve.weekly-client-update`
- `{{claude}}` - absolute path printed by `command -v claude`
- `{{skill}}` - the installed skill name
- `{{tools}}` - only what the job needs, e.g. `Read,Write(~/drafts/**),Bash(git log *)`
- `{{project}}` - absolute project folder the job works in
- `{{weekday}}` / `{{hour}}` / `{{minute}}` - 0 = Sunday; hour 0-23
- `{{home}}` - the user's home folder written out in full (launchd does not expand `~`)

The first line of the file must be the XML declaration, followed by the Apple plist DOCTYPE line
(`PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"`), then:

```xml
<plist version="1.0">
<dict>
  <key>Label</key><string>{{label}}</string>
  <key>WorkingDirectory</key><string>{{project}}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{{claude}}</string>
    <string>-p</string>
    <string>/{{skill}} (scheduled run: prepare drafts only, never send, publish, pay or delete)</string>
    <string>--allowedTools</string>
    <string>{{tools}}</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>{{weekday}}</integer>
    <key>Hour</key><integer>{{hour}}</integer>
    <key>Minute</key><integer>{{minute}}</integer>
  </dict>
  <key>StandardOutPath</key><string>{{home}}/claude-improve/automation/{{label}}.log</string>
  <key>StandardErrorPath</key><string>{{home}}/claude-improve/automation/{{label}}.log</string>
</dict>
</plist>
```

Check the finished file with `plutil -lint <file>` before showing it to the user.
