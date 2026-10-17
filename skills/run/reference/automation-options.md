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
