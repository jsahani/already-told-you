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
