---
name: swarm

description: >
  Decompose a complex task into parallel subagents, create all agent files,
  and deliver a ready-to-execute orchestration plan with wave structure.

  Invoke when: "create agents for this", "spin up a swarm", "parallel agents",
  "swarm this", "break this into subagents", "orchestrate agents for",
  "what agents do I need", "build a swarm",
  "I need agents for this", "decompose this task".

argument-hint: <endstate or full task description>

allowed-tools: Read, Write, Edit, Grep, Glob, Bash

---

## Mission

Analyze a requested endstate, decompose it into independent parallel workstreams,
design a purpose-built subagent for each, create all agent files, and deliver a
ready-to-execute orchestration plan with wave structure and exact invocation commands.

Bias toward action: create files first, explain after.

---

## Phase 1: Context Capture

Read all available project context before designing anything:

- Scan repository structure (Glob up to 2 levels)
- Read key files: README, package.json / pyproject.toml / build.gradle, main entrypoints, CI configs
- Detect language(s), runtime(s), frameworks, and existing conventions
- Note coding standards and patterns already in use — subagents must conform to them

If context is insufficient to design agents safely, state assumptions explicitly and proceed.

---

## Phase 2: Task Decomposition

Transform the requested endstate into parallelizable workstreams:

Rules:
- Each subagent owns exactly one concern — no shared ownership
- Prefer 3–6 agents; resist over-fragmentation
- Separate concerns: implementation / validation / integration / documentation
- Identify dependencies and assign each agent a wave number

Output a task graph:

```
Wave 1 (parallel): [agent-a, agent-b, agent-c]
Wave 2 (parallel, after Wave 1): [agent-d, agent-e]
Wave 3 (after Wave 2): [integrator]
```

---

## Phase 3: Agent Design

For each agent, define the following before generating any files:

| Field | Description |
|---|---|
| `name` | Kebab-case identifier (e.g., `auth-module-builder`) |
| `role` | One-sentence responsibility |
| `wave` | Execution wave number |
| `inputs` | Files or artifacts it reads |
| `outputs` | Concrete artifacts it produces (with paths) |
| `constraints` | Files and areas it must NOT touch |
| `success_criteria` | Observable, verifiable completion signals |

Always include one final **integrator agent** in the last wave:
- Merges outputs from all prior agents
- Resolves conflicts and inconsistencies
- Runs build / test / validation
- Confirms the endstate is achieved

---

## Phase 4: File Generation

Create all agent files at `.swarm/agents/<agent-name>.md` using this exact template:

```markdown
# Agent: <name>

## Role
<One-sentence responsibility>

## Wave
<Wave number and dependency> (e.g., "Wave 2 — runs after agent-a and agent-b complete")

## Inputs
- <file or artifact path>

## Outputs
- <path/to/output> — <what it contains>

## Constraints
- Do NOT modify: <files or areas out of scope>
- Do NOT proceed if: <blocking condition>

## Task
<Detailed step-by-step instructions for this agent>

## Success Criteria
- [ ] <verifiable criterion>
- [ ] <verifiable criterion>
```

Also generate `.swarm/plan.md` containing the full orchestration plan (wave structure,
dependency graph, and CLI commands). See Phase 5–6 for contents.

After creating all files, verify:

```bash
ls -la .swarm/agents/
cat .swarm/plan.md
```

---

## Phase 5: Orchestration Plan

Write `.swarm/plan.md` with the following structure:

### Wave Structure

Group agents by wave. Within each wave, all agents run in parallel.

```
Wave 1 — Independent (no dependencies)
  Agents: agent-a, agent-b, agent-c

Wave 2 — Depends on Wave 1 outputs
  Agents: agent-d, agent-e

Wave 3 — Integration
  Agents: integrator
```

### Dependency Notes

List artifact handoffs between waves:
- "agent-d reads `src/api/` produced by agent-a"
- "integrator reads all outputs from Wave 1 and Wave 2"

---

## Phase 6: Invocation Commands

Provide exact, copy-pasteable CLI commands.

**Single agent:**
```bash
claude -p "$(cat .swarm/agents/agent-a.md)"
```

**Wave execution (parallel within wave, sequential between waves):**
```bash
# Wave 1 — run in parallel
claude -p "$(cat .swarm/agents/agent-a.md)" &
claude -p "$(cat .swarm/agents/agent-b.md)" &
claude -p "$(cat .swarm/agents/agent-c.md)" &
wait

# Wave 2 — run after Wave 1 completes
claude -p "$(cat .swarm/agents/agent-d.md)" &
claude -p "$(cat .swarm/agents/agent-e.md)" &
wait

# Wave 3 — integration
claude -p "$(cat .swarm/agents/integrator.md)"
```

---

## Phase 7: Handoff Summary

End with a concise summary printed to the user:

```
Swarm created: N agents across M waves

  .swarm/agents/
  ├── agent-a.md     [Wave 1] — <role>
  ├── agent-b.md     [Wave 1] — <role>
  ├── agent-d.md     [Wave 2] — <role>
  └── integrator.md  [Wave 3] — merge, validate, confirm endstate

Full plan: .swarm/plan.md

Start execution:
  bash .swarm/plan.md  (or copy commands from Phase 6 above)

Completion criteria:
  All agent files generated ✓
  Wave plan is runnable    ✓
  Integrator confirms endstate after final wave ✓
```

---

## Design Principles

- Maximize parallelism without breaking correctness
- Minimize cross-agent communication — agents should not need to talk to each other mid-execution
- Prefer deterministic outputs: concrete file paths, not vague descriptions
- Treat each agent like a junior engineer with a narrow, well-specified task
- The integrator agent is not optional — every swarm needs a single point of truth verification

---

## Anti-Patterns (avoid)

- Agents with vague responsibilities ("handle the backend")
- Multiple agents writing to the same file simultaneously
- Hidden dependencies between Wave 1 agents
- Overly sequential plans where parallelism was possible
- Invocation commands that haven't been verified to exist
- Skipping the integrator because "it seems obvious"

---

## Output Requirements

Every swarm must produce:

1. Agent list with roles and wave assignments
2. Dependency graph (which agent feeds which)
3. Wave execution plan
4. All `.swarm/agents/*.md` files created on disk
5. `.swarm/plan.md` with copy-pasteable CLI commands
