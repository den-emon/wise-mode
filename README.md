# wise-mode

A collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills and hooks for disciplined development — **wise** for architect-mode quality gates, **wise-cont** for persistent architect mode, and **cclog** for automatic session logging.

## Components

| Name | Type | Description |
|------|------|-------------|
| **wise** | Skill (`/wise`) | Architect mode — systematic planning, TDD, adversarial self-review, and quality gates (single task) |
| **wise-cont** | Skill (`/wise-cont`) | Continuous architect mode — activate once, applies to all subsequent messages in the session |
| **cclog** | Hook | Auto-records all Claude Code sessions to `.claude/log/` — zero token consumption |

## Quick install

Run this in your **project root** (where `.git/` lives):

```bash
curl -fsSL https://raw.githubusercontent.com/den-emon/wise-mode/main/install.sh | bash
```

This installs skills into `.claude/skills/`, the cclog hook into `.claude/hooks/`, and merges hook configuration into `.claude/settings.local.json`.

### Manual install

```bash
# wise
mkdir -p .claude/skills/wise
cd .claude/skills/wise
curl -fsSLO https://raw.githubusercontent.com/den-emon/wise-mode/main/.claude/skills/wise/SKILL.md
curl -fsSLO https://raw.githubusercontent.com/den-emon/wise-mode/main/.claude/skills/wise/CHECKLISTS.md
curl -fsSLO https://raw.githubusercontent.com/den-emon/wise-mode/main/.claude/skills/wise/PATTERNS.md

# wise-cont
mkdir -p .claude/skills/wise-cont
cd .claude/skills/wise-cont
curl -fsSLO https://raw.githubusercontent.com/den-emon/wise-mode/main/.claude/skills/wise-cont/SKILL.md

# cclog (hook)
mkdir -p .claude/hooks
cd .claude/hooks
curl -fsSLO https://raw.githubusercontent.com/den-emon/wise-mode/main/.claude/hooks/cclog-hook.sh
chmod +x cclog-hook.sh
```

For cclog, add the following to `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/cclog-hook.sh PostToolUse",
            "timeout": 5000
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/cclog-hook.sh Stop",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

## wise — Architect Mode

When you type `/wise` in Claude Code, the agent shifts into architect mode for a **single task**:

- **Think first, code second** — 70% understanding, 30% coding
- **8-phase workflow** — from planning through PR readiness
- **TDD enforcement** — RED / GREEN / REFACTOR cycle
- **Adversarial self-review** — "What if this runs twice concurrently?"
- **Lightweight mode** — auto-scales down for simple, low-risk changes

```
/wise implement user authentication with JWT
```

| Phase | What happens |
|-------|-------------|
| 1. **Understanding & Planning** | Reads project docs, assesses complexity, creates a plan |
| 2. **Codebase Exploration** | Maps existing patterns, verifies APIs exist, identifies impact zone |
| 3. **TDD** | Writes failing tests first, then minimal implementation, then refactors |
| 4. **Implementation** | Builds following existing patterns — constants, logging, error handling |
| 5. **Test Verification** | Runs the appropriate test suite, fixes regressions |
| 6. **Documentation** | Updates docs and GitHub issues |
| 7. **Pre-Commit Review** | Adversarial self-review checklist |
| 8. **PR Readiness** | Self-reviews the diff, opens a clean PR |

Simple changes (single file, < 50 lines, no interface changes) automatically skip the full ceremony — only phases 1, 4, and 7 run.

### Skill files

| File | Purpose |
|------|---------|
| `SKILL.md` | Core skill definition — phases, principles, and workflow |
| `CHECKLISTS.md` | Quick-reference checklists for each phase |
| `PATTERNS.md` | Concrete code examples for concurrency, testing, and implementation patterns |

## wise-cont — Continuous Architect Mode

Activate once, and **every subsequent message** in the session is handled with architect-mode standards — no need to type `/wise` each time.

```
/wise-cont
```

The agent automatically assesses each request and applies the appropriate level:

| Request type | Mode applied |
|-------------|--------------|
| Question / discussion (no code changes) | Q&A — architect thinking principles only |
| Single file, < 50 lines, low risk | Lightweight — phases 1, 4, 7 |
| Multi-file, clear scope | Full — phases 1–8 |
| Complex (4+ files, schema changes, etc.) | Full + GitHub issue required |

Deactivate with `/wise-cont-off` or "back to normal mode".

## cclog — Session Logger (Hook)

Automatically records all Claude Code tool usage to `.claude/log/` as Markdown files. Runs as a hook — **zero session token consumption**.

### How it works

- **PostToolUse hook** — logs every tool call with timestamps, input parameters, and execution results
- **Stop hook** — adds turn separators between Claude responses
- **Session detection** — groups entries by `session_id`, one file per session

### What gets recorded

| Tool | Recorded content |
|------|-----------------|
| **Bash** | Command, description, execution result (in `<details>` collapse) |
| **Edit** | File path, diff (`- old` / `+ new`) |
| **Grep** | Pattern, path, glob filter, match results |
| **Glob** | Pattern, path, matched files |
| **Read** | File path |
| **Write** | File path |
| **Agent** | Type, description, prompt |
| **Skill** | Skill name, arguments |
| **Others** | Tool name, input JSON, result |

### Log format

Logs are saved as `.claude/log/YYYY-MM-DD_HHMMSS.md`:

````markdown
# Claude Code Session Log
**Date:** 2026-03-20
**Start:** 14:30:22
**Project:** my-project

---

### [14:30] `Bash` — Run unit tests
```bash
npm test
```
<details><summary>result</summary>

```
PASS src/app.test.ts
  ✓ renders correctly (12ms)
Tests: 1 passed
```
</details>

### [14:31] `Edit` — `src/app.ts`
```diff
- const x = 1
+ const x = 2
```

### [14:32] `Grep` — `handleError` in `src/` (`*.ts`)
```
src/app.ts:42:  handleError(err)
src/utils.ts:10:export function handleError(e: Error) {
```

---
> Turn ended at 14:32:45
````

### Managing logs

```bash
# List sessions
ls -lt .claude/log/*.md

# View a session
cat .claude/log/2026-03-20_143022.md

# Delete a session
rm .claude/log/2026-03-20_143022.md

# Delete all logs
rm -rf .claude/log/*
```

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- `python3` (for cclog hook JSON parsing and installer config merge)
- `curl` or `wget` (for the installer)

## Uninstall

```bash
# All components
rm -rf .claude/skills/wise .claude/skills/wise-cont .claude/hooks/cclog-hook.sh

# Individual
rm -rf .claude/skills/wise
rm -rf .claude/skills/wise-cont
rm .claude/hooks/cclog-hook.sh
```

After removing cclog, also remove the `hooks` section from `.claude/settings.local.json`.

## License

MIT
