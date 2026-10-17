---
name: apply-rules
description: Adds the rules from section B of your Already Told You report ("What you keep explaining") to the right CLAUDE.md - yours for every project or one project's - inside a marked already-told-you block. Shows the diff first and writes only what you approve. Re-running refreshes the block instead of duplicating it.
argument-hint: "[report date]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/apply_rules.py --preview *) Read(~/already-told-you/**) Read(~/claude-improve/**) Glob
---

# Already Told You: apply rules to CLAUDE.md

1. **Find the report.** `~/already-told-you/$ARGUMENTS/findings.json` if a date was given, else the newest
   `~/already-told-you/<YYYY-MM-DD>/findings.json` (use Glob). If there is none, also look in `~/claude-improve/`
   (reports made before the plugin was renamed). None → "Run /already-told-you:run first" and stop.
2. **Show the rules.** Read section B. Number each rule and show: title, how many sessions, the exact rule text and
   its target file (`~/.claude/CLAUDE.md` = every project; a project path = only that project). Ask which to
   apply; the user may also reword a rule or change its target - if so, edit `findings.json` in the report folder
   (only `rule` / `file` of that item) before continuing.
3. **Preview, per target file.** Group the approved rules by target file. For each file run
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/apply_rules.py --preview --findings <findings.json> --target <file> --ids <id1,id2>`
   and show the diff exactly as printed. Explain in one line: text outside the
   `<!-- already-told-you:start -->` / `<!-- already-told-you:end -->` block is never touched, and running this
   again replaces the block rather than adding a second one (an older `self-improve` block is replaced too). Include in `--ids` every rule that should stay in that
   file's block (an earlier approved rule that is left out gets removed from the block).
4. **Ask for a yes per file.** Only after a clear yes run the same command with `--write` instead of `--preview`.
   It asks for permission - that prompt is the second safety check, let the user answer it.
5. **Finish.** Say which files changed and that Claude Code reads CLAUDE.md at the start of each session, so the
   rules apply from the next session. To undo: delete the block between the two markers.

Never edit any other part of a CLAUDE.md, and never write a CLAUDE.md the user did not approve.
