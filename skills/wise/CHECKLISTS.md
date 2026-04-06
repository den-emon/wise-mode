# Quick Reference Checklists

Use this file as a compact companion to `SKILL.md`.

The main skill defines the workflow.
This file is for fast verification when you are:
- planning a change,
- reviewing implementation,
- checking test quality,
- preparing a final handoff.

---

## 1) Intake Checklist

Before touching code, confirm:

- [ ] I understand the requested outcome in concrete terms
- [ ] I can state what will change
- [ ] I can state what will **not** change
- [ ] I have identified acceptance criteria
- [ ] I have classified the task as **lightweight** or **full path**
- [ ] I created a todo list with concrete steps
- [ ] I checked repository guidance (`CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, PR template, docs)
- [ ] I know whether GitHub issue/PR tracking is actually in use here
- [ ] If GitHub is unavailable, I have a non-GitHub tracking fallback (todo list + final summary)

If any of these are false, you are not ready to implement.

---

## 2) Exploration Checklist

Before proposing a design, confirm:

- [ ] I verified relevant files, functions, methods, classes, constants, and flags actually exist
- [ ] I identified local code patterns for logging, errors, validation, config, and tests
- [ ] I mapped callers and dependents of the code I may change
- [ ] I understand data touched by the change
- [ ] I identified external side effects
- [ ] I checked whether shared mutable state is involved
- [ ] I identified invariants that must remain true
- [ ] I chose the smallest safe design that matches repository conventions

Warning signs:
- You are relying on memory instead of search
- You are inventing abstractions before understanding current ones
- You are planning unrelated cleanup “while you are here”

---

## 3) Lightweight Path Checklist

Use only if **all** are true:

- [ ] Single file or very tightly localized
- [ ] Small change
- [ ] No public API/interface change
- [ ] No schema/migration implications
- [ ] No concurrency/shared-state concern
- [ ] Low regression risk
- [ ] Test impact is obvious

For lightweight tasks, confirm:

- [ ] I still did a short understanding pass
- [ ] I still verified symbols and patterns
- [ ] I still ran appropriate validation/tests
- [ ] I still performed adversarial review before finishing

If unsure, do not use the lightweight path.

---

## 4) TDD / Test Strategy Checklist

For non-trivial changes:

- [ ] **RED**: I wrote or updated a test before implementation
- [ ] The test failed for the correct reason
- [ ] **GREEN**: I implemented the minimum needed behavior
- [ ] The test now passes
- [ ] **REFACTOR**: I only cleaned structure while tests stayed green

Quality of tests:

- [ ] Assertions check specific values, not vague truthiness
- [ ] Boundary cases are covered where relevant
- [ ] Error paths are covered where relevant
- [ ] Important side effects are asserted
- [ ] Repeated execution / idempotency is checked where relevant
- [ ] Tests would catch subtle operator/condition regressions
- [ ] Tests are isolated from unrelated external dependencies where possible

Ask:
- Would this test catch `>` changing to `>=`?
- Would it catch a duplicate side effect?
- Would it catch missing persistence?
- Would it catch a partial update?

---

## 5) Legacy / Weakly-Tested Area Checklist

If the area has weak or no tests:

- [ ] I wrote characterization tests for current behavior first
- [ ] I ran them on the unmodified code
- [ ] I captured representative inputs, not just one happy path
- [ ] I only changed behavior intentionally
- [ ] If characterization tests broke, I verified whether that break was intended

Characterization tests are not the end state.
They are the safety net that lets you change code responsibly.

---

## 6) Implementation Checklist

While coding, confirm:

- [ ] I am using existing constants/enums/config where appropriate
- [ ] I am following local naming and module boundaries
- [ ] Input validation happens at the correct boundary
- [ ] Error handling is coherent with the repository style
- [ ] Logging/metrics follow existing patterns
- [ ] I did not introduce unnecessary scope creep
- [ ] I did not hard-code values that should be centralized

If shared state / async / transactions are involved:

- [ ] I identified all actors that can mutate the state
- [ ] I checked race and repeated-execution scenarios
- [ ] I defined invariants that must hold before and after execution
- [ ] I considered locking / serialization / atomicity needs
- [ ] I considered rollback behavior
- [ ] I considered which side effects must persist even on failure

---

## 7) Design Reset Checklist

If implementation reveals the design is wrong:

- [ ] Stop patching around the flawed design
- [ ] Update the todo list to reflect the new understanding
- [ ] Revisit exploration and impact analysis
- [ ] Revise tests if the target behavior changed
- [ ] Continue only after the new design is explicit

Do **not** keep layering fixes onto a design you no longer trust.

---

## 8) Verification Checklist

Before declaring success:

- [ ] I ran the smallest credible test scope
- [ ] All relevant tests passed
- [ ] I did not ignore failing relevant tests
- [ ] I checked nearby behavior that could regress
- [ ] I verified docs/config/examples if they were affected
- [ ] I reviewed the diff, not just the final files

Suggested test scope:
- Tiny isolated change → related tests
- Feature-local change → feature/module suite
- Cross-cutting change → all affected modules
- Schema/security/auth/concurrency change → broaden validation accordingly

---

## 9) Adversarial Review Checklist

Before handoff, ask:

- [ ] What happens if this runs twice?
- [ ] What happens with null, empty, zero, negative, huge, or malformed input?
- [ ] What assumptions could still be wrong?
- [ ] What else touches the same state?
- [ ] Could this create a race, duplicate side effect, stale read, or partial write?
- [ ] Does the code match local conventions?
- [ ] Are acceptance criteria actually met?
- [ ] Would I be comfortable owning this in production?

If any answer is weak, fix it or document the risk explicitly.

---

## 10) Docs and Tracking Checklist

If the change affected behavior, usage, config, or conventions:

- [ ] I updated docs accordingly
- [ ] I removed dead code instead of commenting it out
- [ ] I updated examples if needed

Tracking:

- [ ] If GitHub issue/PR workflow exists, I updated it
- [ ] If not, the final summary records the same information
- [ ] Open follow-up work is explicit, not implied

---

## 11) Final Handoff Checklist

My final output includes:

- [ ] What changed
- [ ] Why this approach
- [ ] Files changed
- [ ] Tests added/updated/run
- [ ] Risks checked
- [ ] Docs/tracking updated
- [ ] Open questions or next steps

A good handoff should let a reviewer answer:
“What changed, why, how was it validated, and what remains?”

---

## Quick Commands (Optional, Repo-Dependent)

Use these only if they fit the repository and environment.

```bash
# verify symbols / usages
grep -rn "symbol_name" .

# review changed code
git diff
git diff --staged

# compare against main branch
git diff main...HEAD

# run focused tests (example placeholders)
npm test -- path/to/test
pytest path/to/test_file.py
go test ./path/to/package
cargo test package_name
````

---

## Optional GitHub Commands

Only use these if the repository actually uses GitHub issues and `gh` is available.

```bash
# search issues
gh issue list --search "keyword"

# create issue
gh issue create --title "Title" --body "Body"

# update issue body
gh issue edit <issue-number> --body "Updated body"

# add a progress comment
gh issue comment <issue-number> --body "Progress update"

# add labels
gh issue edit <issue-number> --add-label "in-progress"

# close issue
gh issue close <issue-number> --comment "Completed"
```
