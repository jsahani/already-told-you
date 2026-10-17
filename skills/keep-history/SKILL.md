---
name: keep-history
description: Stops Claude Code from deleting your session history after 30 days by setting cleanupPeriodDays to 365 in ~/.claude/settings.json. Backs the file up first, keeps every other setting, and shows the result.
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/keep_history.py --check)
---

# self-improve: keep a year of history

Claude Code stores session transcripts in `~/.claude/projects/` and deletes them after `cleanupPeriodDays` days,
30 by default. /self-improve:run can only learn from what is still there.

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/keep_history.py --check` and show the output.
   - "Nothing to do" → tell the user they are already set and stop.
   - "STOP: ... not valid JSON" → explain that the settings file has a typo, nothing was changed, and stop.
2. Explain in two lines: it will back up `~/.claude/settings.json`, set `cleanupPeriodDays` to 365, and leave every
   other setting exactly as it is. Transcripts take disk space (a busy month can be a few GB); 365 days is a
   year. Transcripts already deleted cannot be brought back. Ask for a yes.
3. After a yes, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/keep_history.py --apply`. It asks for permission - let
   the user answer that prompt. Show the output: the backup path and the value read back from the file.
4. To undo later: copy the backup file back over `~/.claude/settings.json`, or delete the `cleanupPeriodDays` line.

Do not edit `settings.json` any other way.
