# wise-mode

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that transforms Claude into a **Software Architect** — enforcing systematic thinking, TDD, adversarial self-review, and quality gates before any code is committed.

## What it does

When you type `/wise` in Claude Code, the agent shifts into architect mode:

- **Think first, code second** — 70% understanding, 30% coding
- **8-phase workflow** — from planning through PR readiness
- **TDD enforcement** — RED / GREEN / REFACTOR cycle
- **Adversarial self-review** — "What if this runs twice concurrently?"
- **Lightweight mode** — auto-scales down for simple, low-risk changes

## Quick install

Run this in your **project root** (where `.git/` lives):

```bash
curl -fsSL https://raw.githubusercontent.com/den-emon/wise-mode/main/install.sh | bash
```

This installs the skill into `.claude/skills/wise/` in your project.

### Manual install

```bash
mkdir -p .claude/skills/wise
cd .claude/skills/wise
curl -fsSLO https://raw.githubusercontent.com/den-emon/wise-mode/main/.claude/skills/wise/SKILL.md
curl -fsSLO https://raw.githubusercontent.com/den-emon/wise-mode/main/.claude/skills/wise/CHECKLISTS.md
curl -fsSLO https://raw.githubusercontent.com/den-emon/wise-mode/main/.claude/skills/wise/PATTERNS.md
```

## Usage

In Claude Code, type:

```
/wise implement user authentication with JWT
```

Claude will activate architect mode and work through:

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

### Lightweight mode

Simple changes (single file, < 50 lines, no interface changes) automatically skip the full ceremony — only phases 1, 4, and 7 run.

## Skill files

| File | Purpose |
|------|---------|
| `SKILL.md` | Core skill definition — phases, principles, and workflow |
| `CHECKLISTS.md` | Quick-reference checklists for each phase |
| `PATTERNS.md` | Concrete code examples for concurrency, testing, and implementation patterns |

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- `curl` or `wget` (for the installer)

## Uninstall

```bash
rm -rf .claude/skills/wise
```

## License

MIT
