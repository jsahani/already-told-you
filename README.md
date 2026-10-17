# Already Told You

**Stop typing "I already told you this" to Claude.**

A free Claude Code plugin that reads your own Claude Code history and tells you how to work better with it:

1. **Where it keeps going wrong** - the corrections you make again and again, and the rule that stops each one.
2. **Skills you should already have** - the requests you repeat, ranked by time spent, with first drafts **written for you**.
3. **Jobs you repeat by hand** - how often, how many hours a week they cost, and how to automate each down to minutes.

Plus: **what you keep explaining** (ready-to-paste CLAUDE.md rules, so you never have to say it twice). One command, a report on your screen, nothing changed until you say yes.

## Before / after (example)

**Before:** every week you type some version of *"deploy a preview and send me the link"*, then explain the same
three steps, then correct Claude when it calls it done without checking the build.

**After `/already-told-you:run`:** the report shows *"Deploy a preview - 11 times, ~12 min each"* with your own
quotes, a drafted `deploy-preview` skill that already contains those steps (and asks you before anything goes live),
and a rule for CLAUDE.md: *"After any change, run the build and show the output before saying done."*
Two more commands install the skill and add the rule.

## Install

In your terminal:

```
claude plugin marketplace add jsahani/already-told-you
claude plugin install already-told-you@jsahani
```

Or paste this into Claude Code:

> Install the Already Told You plugin from github.com/jsahani/already-told-you

Then start Claude Code and type `/already-told-you:run`.

## The 6 commands

| Command | What it does | Changes anything? |
|---|---|---|
| `/already-told-you:run` | Reads your history (all projects, or `/already-told-you:run here` for this one) and writes the report to `~/already-told-you/<date>/` | No - writes only into `~/already-told-you/` |
| `/already-told-you:install-skills` | Shows each drafted skill, you pick, you see the file, you approve, it installs for all projects or one project | Only what you approve; never overwrites a skill without asking |
| `/already-told-you:find-skills [what you need]` | Searches the public skills directory ([skills.sh](https://skills.sh)) for a ready-made skill, checks each result (installs, publisher, GitHub stars, and reads its SKILL.md and scripts for risky instructions) and recommends the best 1-3. `/already-told-you:find-skills report` does this for the skills and jobs in your latest report. It also starts on its own when you ask Claude to "find a skill for X" | Only what you approve. The one command that uses the network: it shows the search keywords first and sends nothing until you say yes |
| `/already-told-you:apply-rules` | Adds the approved rules to the right CLAUDE.md inside a marked block, after showing the diff | Only the marked block; re-running refreshes it, never duplicates |
| `/already-told-you:automate` | Sets up one repeated job with you: a skill, a skill + app connection, or a scheduled run | Only what you approve; anything that sends, publishes, pays or deletes waits for your yes |
| `/already-told-you:keep-history` | Keeps a year of history instead of 30 days (`cleanupPeriodDays: 365`) | Your `~/.claude/settings.json`, after a backup and your yes |

Run `/already-told-you:run` again in a few weeks: the report adds a **Since last time** section showing what got
fixed and what is still happening.

## What happens to your history

- **No account, no dashboard, and your history goes to no third-party service.** The plugin has no server of its
  own. The bundled scripts are plain Python (standard library only); read them in `scripts/`. They make no network
  calls of their own unless you opt in to the skill search (below).
- **The extractor runs on your computer.** It reads your session transcripts in `~/.claude/projects/` (read-only;
  nothing in them is changed or moved) and the `cleanupPeriodDays` value in `~/.claude/settings.json`.
- **It writes only to `~/already-told-you/<date>/`** - `report.md`, `report.html`, `findings.json`, drafted
  skills, and the digest the report was built from. Delete the folder whenever you like.
- **The analysis is done by your own Claude Code session.** Claude reads the extracted digest (trimmed excerpts of
  your own messages, up to ~120k characters, with API keys, tokens and email addresses masked) the same way it
  reads anything in a Claude Code session: through Anthropic, under the same terms as the rest of your Claude Code
  use.
- **The skill search is opt-in, every time.** `/already-told-you:find-skills` is the only command that uses the
  network. Before anything is sent it shows you the 2-4 short, generic search keywords (for example
  `playwright testing`) and the exact web address, and waits for your yes. The script refuses keywords that look
  like file paths, web addresses, emails, @handles, long numbers, keys, your login name or the names of your
  projects. Never sent: your history, quotes, file paths, project, client or people's names. What it contacts:
  `skills.sh` (the search), then `api.github.com`, `raw.githubusercontent.com` and `skills.sh` again to check the
  results, using only the public names the search returned. Those services see your IP address, as with any web
  request. `/already-told-you:run` itself never searches.

## The 30-day trap

Claude Code deletes session transcripts after **30 days** by default (Anthropic's docs: transcripts are stored
locally "for 30 days by default ... Adjust the period with `cleanupPeriodDays`"). Less history means a thinner
report. `/already-told-you:run` tells you the date of your oldest session and warns you if the setting is under a
year. `/already-told-you:keep-history` sets it to 365 days. Transcripts that are already gone cannot be brought
back, so do this early.

## Requirements

- Claude Code on a paid plan (Pro, Max, Team or Enterprise) or an API key
- Python 3 (on a Mac, run `python3 --version`; if it offers to install the developer tools, say yes)
- About 10 sessions of history for useful results (it works with fewer, the report is just thinner)

## Uninstall

```
claude plugin uninstall already-told-you@jsahani
```

Your reports stay in `~/already-told-you/` until you delete that folder. Skills and rules you installed stay until
you remove them (delete the skill folder, or the block between `<!-- already-told-you:start -->` and
`<!-- already-told-you:end -->`).

## For the curious

- `scripts/extract.py` streams every transcript line by line (about 10 seconds for 2.4 GB), keeps only your own
  messages, finds corrections, interrupts, tool errors, repeated requests and repeated explanations, and writes a
  digest capped to fit one model context. On large histories `/already-told-you:run` splits the detail across
  subagents.
- `scripts/render.py` turns the findings into `report.md` and a single self-contained `report.html`.
- `scripts/skill_search.py` cleans the search keywords, queries skills.sh, and vets each result: GitHub stars, repo
  age, the security scans skills.sh publishes, and a scan of every file in the skill folder for remote code, secret
  requests, broad permissions, data sent out and hidden instructions. It keeps the copy it downloaded and checked,
  so the recommended install puts in exactly the files that were read. (It calls the public skills.sh search directly instead of
  `npx skills find`, which needs Node and also sends a usage ping.)
- Tests: `python3 -m unittest discover -s tests`

## Licence

MIT - see [LICENSE](LICENSE).

Made by [@jsahani.ai](https://www.instagram.com/jsahani.ai/).
