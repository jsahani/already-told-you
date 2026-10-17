# self-improve

**A free Claude Code plugin that reads your own Claude Code history and tells you how to work better with it.**

1. **Where it keeps going wrong** - the corrections you make again and again, and the rule that stops each one.
2. **Skills you should already have** - the requests you repeat, ranked by time spent, with first drafts **written for you**.
3. **Jobs you repeat by hand** - how often, how many hours a week they cost, and how to automate each down to minutes.

Plus: **what you keep explaining** (ready-to-paste CLAUDE.md rules). One command, a report on your screen, nothing changed until you say yes.

## Before / after (example)

**Before:** every week you type some version of *"deploy a preview and send me the link"*, then explain the same
three steps, then correct Claude when it calls it done without checking the build.

**After `/self-improve:run`:** the report shows *"Deploy a preview - 11 times, ~12 min each"* with your own quotes,
a drafted `deploy-preview` skill that already contains those steps (and asks you before anything goes live), and a
rule for CLAUDE.md: *"After any change, run the build and show the output before saying done."*
Two more commands install the skill and add the rule.

## Install

In your terminal:

```
claude plugin marketplace add jsahani/claude-self-improve
claude plugin install self-improve@jsahani
```

Or paste this into Claude Code:

> Install the self-improve plugin from github.com/jsahani/claude-self-improve

Then start Claude Code and type `/self-improve:run`.

## The 5 commands

| Command | What it does | Changes anything? |
|---|---|---|
| `/self-improve:run` | Reads your history (all projects, or `/self-improve:run here` for this one) and writes the report to `~/claude-improve/<date>/` | No - writes only into `~/claude-improve/` |
| `/self-improve:install-skills` | Shows each drafted skill, you pick, you see the file, you approve, it installs for all projects or one project | Only what you approve; never overwrites a skill without asking |
| `/self-improve:apply-rules` | Adds the approved rules to the right CLAUDE.md inside a marked block, after showing the diff | Only the marked block; re-running refreshes it, never duplicates |
| `/self-improve:automate` | Sets up one repeated job with you: a skill, a skill + app connection, or a scheduled run | Only what you approve; anything that sends, publishes, pays or deletes waits for your yes |
| `/self-improve:keep-history` | Keeps a year of history instead of 30 days (`cleanupPeriodDays: 365`) | Your `~/.claude/settings.json`, after a backup and your yes |

Run `/self-improve:run` again in a few weeks: the report adds a **Since last time** section showing what got fixed
and what is still happening.

## What happens to your history

- **No account, no dashboard, no third-party service.** The plugin has no server of its own and the bundled
  scripts make no network calls of their own. They are plain Python (standard library only); read them in
  `scripts/`.
- **The extractor runs on your computer.** It reads your session transcripts in `~/.claude/projects/` (read-only;
  nothing in them is changed or moved) and the `cleanupPeriodDays` value in `~/.claude/settings.json`.
- **It writes only to `~/claude-improve/<date>/`** - `report.md`, `report.html`, `findings.json`, drafted skills,
  and the digest the report was built from. Delete the folder whenever you like.
- **The analysis is done by your own Claude Code session.** Claude reads the extracted digest (trimmed excerpts of
  your own messages, up to ~120k characters, with API keys, tokens and email addresses masked) the same way it
  reads anything in a Claude Code session: through Anthropic, under the same terms as the rest of your Claude Code
  use.

## The 30-day trap

Claude Code deletes session transcripts after **30 days** by default (Anthropic's docs: transcripts are stored
locally "for 30 days by default ... Adjust the period with `cleanupPeriodDays`"). Less history means a thinner
report. `/self-improve:run` tells you the date of your oldest session and warns you if the setting is under a year.
`/self-improve:keep-history` sets it to 365 days. Transcripts that are already gone cannot be brought back, so do
this early.

## Requirements

- Claude Code on a paid plan (Pro, Max, Team or Enterprise) or an API key
- Python 3 (on a Mac, run `python3 --version`; if it offers to install the developer tools, say yes)
- About 10 sessions of history for useful results (it works with fewer, the report is just thinner)

## Uninstall

```
claude plugin uninstall self-improve@jsahani
```

Your reports stay in `~/claude-improve/` until you delete that folder. Skills and rules you installed stay until
you remove them (delete the skill folder, or the block between `<!-- self-improve:start -->` and
`<!-- self-improve:end -->`).

## For the curious

- `scripts/extract.py` streams every transcript line by line (about 10 seconds for 2.4 GB), keeps only your own
  messages, finds corrections, interrupts, tool errors, repeated requests and repeated explanations, and writes a
  digest capped to fit one model context. On large histories `/self-improve:run` splits the detail across
  subagents.
- `scripts/render.py` turns the findings into `report.md` and a single self-contained `report.html`.
- Tests: `python3 -m unittest discover -s tests`

## Licence

MIT - see [LICENSE](LICENSE).

Made by [@jsahani.ai](https://www.instagram.com/jsahani.ai/).
