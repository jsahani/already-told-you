---
name: install-skills
description: Shows the skills that /already-told-you:run drafted from your history, lets you pick, shows each file, and installs only the ones you approve - for all projects (~/.claude/skills) or just one project. Never overwrites an existing skill without asking.
argument-hint: "[report date]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/install_skill.py --list *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/install_skill.py --check *) Read(~/already-told-you/**) Read(~/claude-improve/**) Glob
---

# Already Told You: install drafted skills

Nothing is installed until the user says yes to that specific skill.

1. **Find the report.** Use `~/already-told-you/$ARGUMENTS` if a date was given, otherwise the newest
   `~/already-told-you/<YYYY-MM-DD>/` folder that has a `skills/` folder (use Glob). If there is none, also look
   in `~/claude-improve/` (reports made before the plugin was renamed). If there is still none, say
   "No drafted skills yet - run /already-told-you:run first" and stop.
2. **List them.** Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/install_skill.py --list --report <report folder>`.
   If `<report>/findings.json` exists, add each skill's line from section C (how often it came up, minutes each).
   Ask which ones the user wants to look at (they can say "all").
3. **For each chosen skill, one at a time:**
   - Read its `SKILL.md` and show it in full. Point out any `TODO (check):` lines; offer to fill them in with the
     user's answers before installing (edit the draft in the report folder only).
   - Ask where: **all projects** (`~/.claude/skills`, or `$CLAUDE_CONFIG_DIR/skills` if the user set that
     variable) or **this project only** (`${CLAUDE_PROJECT_DIR}/.claude/skills`).
     Recommend all projects when the quotes behind it came from 2+ projects.
   - Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/install_skill.py --check --src <report>/skills/<name> --dest <dest>`.
     If it says the skill is already installed there, show both versions' differences and ask whether to replace
     it (the old one is kept as a backup) or skip.
   - Ask for a clear yes. Only then run
     `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/install_skill.py --install --src <report>/skills/<name> --dest <dest>`
     (add `--force` only if the user chose to replace an existing skill). This command asks for permission;
     that prompt is the second safety check, let the user answer it.
4. **Finish.** List what was installed where, and how to use each one (`/<name>`, or just ask for the task in the
   user's own words - the description holds their phrasing). Mention that removing a skill is deleting its folder.
