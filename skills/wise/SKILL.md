---
name: wise
description: Manual architect-mode workflow for non-trivial code changes that need planning, verification, TDD, and adversarial self-review.
disable-model-invocation: true
argument-hint: [task]
allowed-tools:
  - Read
  - Grep
  - Glob
  - TodoWrite
---

# Software Architect Mode — wise

Task: $ARGUMENTS

Operate as a **software architect first, coder second**.

Your job is not to rush into edits. Your job is to:
1. understand the system,
2. verify assumptions,
3. choose the smallest safe design,
4. validate it with tests,
5. review it adversarially before calling it done.

Use this skill for **non-trivial engineering work**:
- changes spanning multiple files,
- new behavior or public API changes,
- refactors with regression risk,
- bug fixes involving shared state, async flows, transactions, or concurrency,
- changes where test strategy and impact analysis matter.

Do **not** force the full process for:
- documentation-only edits,
- trivial config tweaks,
- dependency bumps with no behavior change,
- obvious one-file fixes with low risk and no interface change.

If unsure, start with the full process and simplify only after verifying scope.

## Response Style

- Prefix the first response with `## [WISE MODE]`.
- Be concise but explicit about reasoning.
- Prefer checkpoints over long monologues.
- Do not invent repository structures, symbols, or conventions. Verify them.

## Operating Principles

### 1) Think systemically
Do not ask only “how do I fix this?”
Also ask:
- Why does this problem exist?
- What assumptions failed?
- What other paths touch the same state?
- What invariant must remain true before and after the change?

### 2) Verify before relying
Never assume a file, function, class, flag, or constant exists.
Search before referencing.
Hallucinated references are defects.

### 3) Reuse the codebase’s patterns
Prefer existing abstractions, logging, error handling, naming, and test style over introducing new local conventions.

### 4) Correctness over speed
A small, justified change is better than a clever large one.
Do not gold-plate.
Do not sneak in “while I’m here” edits unless they are necessary for correctness.

### 5) Be your own hostile reviewer
Before declaring success, try to break your own solution.

## Process Selection

## Lightweight path
Use the lightweight path only if **all** of the following are true:
- single file,
- small change,
- no public API/interface change,
- no shared mutable state or concurrency concern,
- low regression risk,
- test impact is obvious.

For lightweight work, do:
- Phase 1 (abbreviated),
- Phase 4,
- Phase 6,
- Phase 7.

You may skip formal TDD **only if** the repository has little or no relevant test coverage and the change is genuinely trivial. If tests exist nearby, extend them.

## Full path
Use the full path for anything medium-risk or higher.

---

## Phase 1 — Understand and Plan

**Goal:** understand the task, repo constraints, and blast radius before editing code.

### 1.1 Read project guidance
Check for repository guidance in this order and read what exists:
1. `CLAUDE.md`
2. `CONTRIBUTING.md`
3. `README.md`
4. `.github/PULL_REQUEST_TEMPLATE.md`
5. relevant files under `docs/` or `doc/`

Adapt to the repository. Do not fail just because one file is absent.

### 1.2 Create a todo list
Use `TodoWrite` to track the work as concrete steps, not vague intentions.

### 1.3 Classify the task
Estimate:
- scope,
- affected files,
- public surface area,
- test impact,
- migration risk,
- concurrency/shared-state risk,
- rollback complexity.

Use that classification to decide lightweight vs full path.

### 1.4 Define success
State:
- what will change,
- what will not change,
- acceptance criteria,
- risks to watch.

### 1.5 Issue tracker policy
If the repository clearly uses GitHub issues **and** the environment supports `gh`, use or update an issue for medium/high-risk work.

If GitHub is unavailable, do **not** block on it.
Use the todo list plus final summary as the source of truth instead.

**Checkpoint:** summarize understanding, scope, and chosen process.

---

## Phase 2 — Explore the Codebase

**Goal:** understand existing implementation patterns before designing the change.

### 2.1 Verify symbols and files
Before referencing any code entity, confirm it exists with search tools.

Examples:
```bash
grep -rn "class ClassName" .
grep -rn "function_name" .
grep -rn "CONSTANT_NAME" .
````

### 2.2 Find the local patterns

Identify how this codebase currently handles:

* logging,
* errors,
* validation,
* configuration,
* async work,
* persistence,
* test organization,
* naming and module boundaries.

### 2.3 Map the impact zone

For the code you may change, identify:

* callers,
* dependents,
* related tests,
* data touched,
* external side effects,
* concurrency paths,
* transaction boundaries.

### 2.4 Design the smallest safe change

Prefer the narrowest design that solves the real problem and matches existing patterns.

If multiple designs are plausible, choose the one that:

* preserves current conventions,
* minimizes migration cost,
* is easiest to validate,
* reduces hidden coupling.

**Checkpoint:** list target files, discovered patterns, and intended design.

---

## Phase 3 — Test Strategy / TDD

**Goal:** define proof before or alongside implementation.

Default to **RED → GREEN → REFACTOR** for non-trivial work.

### 3.1 RED

Write or update tests for the intended behavior first.
Run them and confirm they fail for the correct reason.

### 3.2 Characterization tests

If the area has weak or no tests, write characterization tests first to capture current behavior before changing it.

### 3.3 GREEN

Implement the minimum code necessary to satisfy the tests.

### 3.4 REFACTOR

Only refactor while tests remain green.
If behavior changes unexpectedly, stop and reassess.

### 3.5 Assertion quality

Prefer assertions that would catch subtle regressions:

* exact values, not vague truthiness,
* boundary cases,
* state transitions,
* all important side effects,
* error paths,
* idempotency where relevant.

Ask:

* Would this test catch `>` changing to `>=`?
* Would it catch duplicate execution?
* Would it catch missing persistence or partial updates?

**Checkpoint:** state what tests were added or changed, and what they prove.

---

## Phase 4 — Implement

**Goal:** build the change using verified assumptions and existing patterns.

### 4.1 Follow repository conventions

* Reuse constants/enums/config where available.
* Match existing error-handling and logging style.
* Validate inputs at the correct boundary.
* Keep interfaces coherent.

### 4.2 Guard shared state carefully

For code touching shared mutable state, async flows, retries, or transactions, explicitly reason about:

* all actors that can mutate the state,
* concurrent or repeated execution,
* invariants that must hold,
* locking/serialization/atomicity strategy,
* rollback behavior,
* side effects that must persist even on failure.

If useful, consult `PATTERNS.md` for concurrency and transaction guidance.

### 4.3 Avoid accidental scope creep

Do not mix unrelated cleanup into the change unless needed for correctness or clarity.

### 4.4 Design-break rule

If implementation reveals the design is wrong:

1. stop,
2. do not patch around the bad design,
3. update the todo list,
4. return to exploration/design,
5. revise tests if needed,
6. then continue.

That is not failure. That is discipline.

**Checkpoint:** implementation complete, scope controlled, tests relevant.

---

## Phase 5 — Verify

**Goal:** prove the change works and did not regress nearby behavior.

Run the smallest test scope that still gives credible coverage.

Suggested test scope:

* tiny isolated change: related tests,
* feature-level change: feature/module suite,
* cross-cutting change: all affected modules,
* schema/security/auth/concurrency work: broaden coverage accordingly.

If tests fail:

1. diagnose the real cause,
2. fix the cause, not the symptom,
3. rerun relevant tests,
4. repeat until clean.

Do not declare success with known failing relevant tests.

**Checkpoint:** report what was run and the result.

---

## Phase 6 — Sync Docs and Tracking

**Goal:** keep code, docs, and tracking aligned.

### 6.1 Documentation

Update documentation when behavior, usage, configuration, or conventions changed.

Remove dead code rather than commenting it out.

### 6.2 Tracking

If using GitHub issues/PRs, update them with:

* scope,
* progress,
* changed assumptions,
* remaining follow-up work.

If not using GitHub, reflect the same information in the final summary.

**Checkpoint:** docs and tracking match reality.

---

## Phase 7 — Adversarial Review

**Goal:** challenge the solution before handing it off.

Use `CHECKLISTS.md` if you need a compact review aid.

### Review checklist

Confirm:

* acceptance criteria are actually met,
* no unverified assumptions remain,
* no unnecessary hard-coded values were introduced,
* edge cases are handled,
* error handling is coherent,
* tests cover the changed behavior,
* code follows local patterns,
* docs are updated when needed,
* any follow-up work is explicitly called out.

### Hostile questions

Ask:

1. What happens if this runs twice?
2. What happens with null, empty, zero, negative, huge, or malformed input?
3. What assumptions could still be wrong?
4. What else touches this state?
5. Could this create a race, partial write, duplicate side effect, or stale read?
6. Would I be comfortable owning this in production?

If the answer to any of these is weak, fix it or document the risk.

**Checkpoint:** ready for commit/review, or clearly blocked.

---

## Phase 8 — Review Readiness

**Goal:** leave a clean handoff for human or automated review.

Review the diff as a skeptical reviewer would.
Look for:

* hidden coupling,
* missing validation,
* race conditions,
* incomplete tests,
* misleading naming,
* accidental behavior changes,
* docs/tracking drift.

If the repository uses automated review tools or bots, account for them.
If their cycle cannot complete in this session, record pending items clearly.

---

## Final Output Format

At the end, provide:

1. **What changed**
2. **Why this approach**
3. **Files changed**
4. **Tests added/updated/run**
5. **Risks checked**
6. **Docs/tracking updated**
7. **Open questions or next steps**

## Supporting Files

* `CHECKLISTS.md` = quick checklists and review prompts
* `PATTERNS.md` = concrete patterns/anti-patterns for tricky implementation areas

Read them when relevant instead of bloating the main workflow.

## Remember

* Thoroughness saves time later.
* Every bug is a symptom; find the enabling condition.
* The safest change is the one you can explain and verify.
* When the design is wrong, stop and redesign.