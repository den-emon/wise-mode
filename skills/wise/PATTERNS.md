# Common Patterns & Anti-Patterns

Reference document for the **wise** skill.

`SKILL.md` defines the workflow.
This file gives concrete implementation and testing patterns for tricky areas.

Use it when working with:
- shared mutable state,
- async or retry behavior,
- transactions and side effects,
- migrations and staged rollouts,
- security-sensitive boundaries,
- weakly tested legacy code,
- subtle regression risks.

---

## 1) Concurrency Patterns

### 1.1 TOCTOU Prevention (Time-of-Check to Time-of-Use)

Problem:
A value is checked, then used later after another actor may have changed it.

```text
# WRONG: stale read between check and update
status = read(record)

if status == "pending":
    update(record, "processing")
```

Why this is dangerous:

- another worker may claim the record after the read,
- repeated execution may double-process work,
- you can violate invariants while looking correct in tests.

Safer patterns:

```text
# BETTER: lock and perform check-and-act as one critical section
lock(record)
status = read(record)

if status == "pending":
    update(record, "processing")

unlock(record)
```

```text
# BETTER: atomic conditional update
affected = UPDATE jobs
SET status = 'processing', started_at = now()
WHERE id = ? AND status = 'pending'

if affected == 0:
    handle_already_claimed()
```

Look for:

- read-then-act flows,
- "if not exists, then create" without uniqueness protection,
- retries that can re-run side effects.

---

### 1.2 Idempotency for Retries and Replays

If a job, webhook, handler, or message consumer can run more than once, design for repeat execution.

```text
# RISKY
send_email(user)
mark_sent(user)
```

If the process crashes after `send_email` but before `mark_sent`, a retry may send twice.

Safer approach:

```text
# BETTER
if already_processed(event_id):
    return

record_processing_marker(event_id)
send_email(user)
mark_sent(user)
```

What to test:

- same request or event twice,
- retry after partial failure,
- out-of-order delivery if relevant.

---

### 1.3 Shared-State Invariant Thinking

Before changing shared state, write down:

- who can modify it,
- under what conditions,
- what must always be true after the operation.

Example invariants:

- an order cannot be both `paid` and `canceled`,
- only one worker can own a job at a time,
- a balance cannot go negative unless overdraft is explicitly allowed.

If you cannot state the invariants clearly, you are not ready to edit the code.

---

## 2) Transaction and Side-Effect Patterns

### 2.1 Side Effects That Must Survive Failure

A common mistake is writing important error or audit state inside a transaction that later rolls back.

```text
# BUGGY
begin_transaction()
create_audit_event("operation_failed")
update_record_status("blocked")
raise_error()
rollback_transaction()
```

Both the audit event and status update disappear.

Safer pattern:

```text
try:
    begin_transaction()
    do_work()
    commit_transaction()
except Error as e:
    create_audit_event("operation_failed")
    update_record_status("blocked")
    raise
```

Questions to ask:

- Which writes are part of the atomic business change?
- Which writes are diagnostic or compensating and must persist even on failure?
- What happens if the failure occurs halfway through?

---

### 2.2 Partial Failure Awareness

When external calls are involved, identify what happens if:

- DB write succeeds but external API call fails,
- external API call succeeds but local state update fails,
- timeout occurs after the remote side effect actually happened.

Typical mitigations:

- idempotency keys,
- outbox or inbox patterns,
- compensating actions,
- explicit reconciliation jobs,
- durable status markers.

---

## 3) Migration and Rollout Patterns

### 3.1 Expand / Contract Instead of Big-Bang Replacement

When data shape or interfaces change, prefer a phased rollout:

```text
1. Add the new column / field / API path
2. Write code that can read both old and new shapes
3. Backfill existing data
4. Switch writers to the new shape
5. Remove old readers only after validation
6. Drop old schema after the migration is proven safe
```

This lowers rollback pain because code and data stay temporarily compatible.

---

### 3.2 Backfill with Dry-Run and Restart Safety

A backfill should be observable and safe to resume.

```text
# BETTER
for batch in load_candidates(limit=1000):
    preview(batch) if dry_run
    transform(batch)
    write_progress_marker(last_id=batch[-1].id)
```

Good backfill properties:

- supports dry-run or preview mode,
- runs in batches,
- records progress,
- is idempotent or restart-safe,
- emits enough metrics to detect drift.

Questions to ask:

- Can it be safely restarted after partial completion?
- What happens if only half the fleet has the new code?
- Can operators tell whether it is done or merely quiet?

---

### 3.3 Feature Flags and Staged Rollout Guards

Use a flag when the blast radius is high or rollback needs to be fast.

```text
if feature_flag("new_writer"):
    write_new_shape(record)
else:
    write_old_shape(record)
```

Flags help when you need:

- canary rollout,
- environment-by-environment activation,
- fast disable without redeploy,
- different read/write timing.

Do not add a flag by reflex.
Use one when it clearly reduces operational risk.

---

### 3.4 Rollback Is a Separate Design Problem

Code rollback and data rollback are not the same thing.

Check explicitly:

- Can the old binary read data written by the new binary?
- Is the migration reversible, partially reversible, or irreversible?
- If irreversible, what is the mitigation path?
- What operator action is needed during rollback?

If the answer is "we would restore from backup," say that plainly and treat it as a serious risk.

---

### 3.5 Reconciliation for Silent Drift

After a staged rollout or backfill, have a way to prove convergence.

Examples:

- count records in old vs new representation,
- compare checksums or aggregates,
- emit audit events for dual-write mismatch,
- run a one-off reconciliation query,
- log rows that fail normalization.

A migration is not finished just because the job stopped erroring.

---

## 4) Security Review Patterns

### 4.1 Authentication vs Authorization

Do not treat "the user is logged in" as proof they may perform the action.

Check separately:

- Who is the caller?
- What resource are they trying to access?
- Where is the authorization decision enforced?
- Can a client bypass the UI and call the endpoint directly?

Security bugs often hide in code that authenticates correctly but authorizes too late or too loosely.

---

### 4.2 Validate and Canonicalize at the Boundary

Normalize and validate untrusted input before deeper logic depends on it.

```text
# BETTER
email = normalize_email(input.email)
validate_email(email)
user = find_user_by_email(email)
```

Watch for:

- duplicate-but-different encodings,
- path traversal via `../`,
- mixed-case identifiers,
- malformed URLs,
- integer parsing edge cases.

---

### 4.3 Injection and Unsafe Composition

Any time you compose queries, shell commands, HTML, or file paths from input, pause.

Prefer:

- parameterized SQL,
- structured command arguments rather than shell strings,
- escaping or templating that matches the sink,
- explicit allowlists for file paths or hosts.

Examples of risky patterns:

```text
sql = "SELECT * FROM users WHERE id = " + user_input
cmd = "curl " + url
path = base_dir + "/" + filename
```

---

### 4.4 Secrets, Tokens, and Sensitive Logs

Common accidental leaks:

- printing full Authorization headers,
- logging raw access tokens or API keys,
- storing secrets in fixtures,
- echoing passwords in test failures,
- including PII in analytics or error payloads.

Safer habits:

- redact secrets before logging,
- use placeholders in tests,
- keep secret material in dedicated config paths,
- review new logs as carefully as new code.

---

### 4.5 Replay, Rate Limit, and Abuse Thinking

Externally triggered actions should be reviewed for abuse cases.

Ask:

- Can the same request be replayed?
- Can an attacker amplify cost with repeated calls?
- Is there an idempotency key, nonce, or rate limit?
- Do error messages reveal too much about valid identities or resources?

---

## 5) Test Patterns

### 5.1 Mutation-Resistant Assertions

Weak assertions miss subtle regressions.

```text
# WEAK
assert result.success is True
```

```text
# STRONGER
assert result.status == "completed"
assert result.count == 5
assert result.completed_at is not None
assert result.items[0].name == "expected"
```

Prefer assertions that would fail if:

- the wrong branch executed,
- a condition changed from `>` to `>=`,
- one field updated but another did not,
- the visible output is truthy but semantically wrong.

---

### 5.2 Boundary Testing

Whenever logic depends on thresholds, lengths, counts, or state transitions, test around the boundary.

Examples:

```text
# numeric threshold
test(value=-1)
test(value=0)
test(value=1)

# length limit
test(name="")
test(name="a")
test(name="a" * MAX)
test(name="a" * (MAX + 1))
```

Also consider:

- duplicate inputs,
- malformed inputs,
- extreme but valid inputs,
- transition edges between states.

---

### 5.3 Side-Effect Assertions

If the code updates multiple fields or emits effects, test all important outcomes.

```text
# TOO WEAK
assert response.status_code == 200
```

```text
# BETTER
assert response.status_code == 200
assert order.status == "processed"
assert order.processed_at is not None
assert audit_event.type == "order_processed"
assert email_queue.contains(order.id)
```

Do not stop at "the function returned success."
Check the state you actually care about.

---

### 5.4 Characterization Tests for Legacy Code

When changing poorly understood code, capture current behavior before changing it.

```text
def test_current_behavior_for_known_input():
    result = legacy_function("ABC-123")
    assert result == {
        "normalized": "abc123",
        "valid": True,
        "source": "legacy-rule",
    }
```

Then add more representative cases:

```text
def test_current_behavior_for_empty_input():
    result = legacy_function("")
    assert result == {
        "normalized": "",
        "valid": False,
        "source": "legacy-rule",
    }
```

Guidelines:

- use real observed inputs where possible,
- capture current behavior faithfully,
- do not improve the behavior inside the characterization test,
- once protected, refactor or change behavior intentionally.

---

### 5.5 Contract-Level Testing

If the change affects an interface, validate the contract rather than only internals.

Examples:

- HTTP response shape and status codes,
- event payload schema,
- CLI exit codes and output,
- database persistence visible to callers,
- public method behavior under invalid input.

A passing unit test is not enough if the public contract changed silently.

---

## 6) Implementation Patterns

### 6.1 Constants Over Magic Values

```text
# NOT IDEAL
status = "active"
kind = "traditional_ira"
```

```text
# BETTER
status = Status.ACTIVE
kind = AccountType.TRADITIONAL_IRA
```

Prefer central definitions when they already exist.
Do not create a new constant layer unless it actually reduces duplication or drift.

---

### 6.2 Reuse Local Conventions

Before adding a helper, abstraction, logger shape, or error type, check what already exists.

Look for:

- validation helpers,
- domain errors,
- config access patterns,
- logging fields,
- API response helpers,
- existing fixtures or builders in tests.

A clean abstraction that ignores repository conventions often increases maintenance cost.

---

### 6.3 DRY, But Only for Real Duplication

Do not extract abstractions from one occurrence.
Do extract when:

- the same logic exists in multiple places,
- the duplication creates bug risk,
- the shared behavior is conceptually stable.

```text
# useful search prompts
grep -rn "same_pattern" .
grep -rn "status = .*pending" .
grep -rn "normalize.*input" .
```

Bad DRY creates indirection without reducing risk.
Good DRY removes repeated behavior that would otherwise drift.

---

### 6.4 Smallest Safe Change

Prefer:

- narrower scope,
- existing extension points,
- fewer files,
- fewer new concepts,
- easier rollback,
- easier testability.

Avoid:

- opportunistic cleanup unrelated to the task,
- replacing patterns the codebase already standardized,
- introducing architecture-level changes to solve a local bug unless clearly necessary.

---

## 7) Verification Patterns

### 7.1 Review the Diff, Not Just the Result

Always inspect what changed.

Useful commands:

```bash
git diff
git diff --staged
git diff main...HEAD
```

Questions during diff review:

- Did I change only what I intended?
- Did I accidentally rename, reformat, or move unrelated code?
- Is the final naming clear?
- Is there hidden coupling I glossed over while coding?

---

### 7.2 Test Scope Selection

Choose the smallest scope that still gives credible confidence.

Examples:

- tiny isolated fix: related test file,
- feature-local change: feature or module suite,
- shared utility change: all dependents likely affected,
- schema, auth, migration, rollout, or concurrency change: broaden validation.

Do not confuse "fastest possible run" with "sufficient validation."

---

## 8) Anti-Patterns to Watch For

### 8.1 Hallucinated Structure

You referenced a file, method, class, constant, or config flag without verifying it exists.

### 8.2 Patch-Through Design Failure

The original design is clearly wrong, but you keep adding conditions instead of rethinking it.

### 8.3 Assertion Poverty

Tests only check truthiness, status 200, or "no exception," while missing the real behavior.

### 8.4 Hidden Scope Creep

The change quietly includes refactors, renames, and cleanup unrelated to the task.

### 8.5 Concurrency Blindness

The code looks correct for one caller but breaks under retries, parallel workers, or duplicate events.

### 8.6 Rollback Confusion

Error or audit state is written inside a transaction and disappears exactly when you need it most.

### 8.7 Migration Without Reconciliation

A rollout is declared complete because the job ended, not because old and new states were proven consistent.

### 8.8 Security by Assumption

The code assumes authentication implies authorization, or assumes validation happened somewhere else.

---

## 9) Pre-Flight Questions

Before writing code, answer these:

1. What are all the ways this code can be reached?
2. What other code reads or mutates the same state?
3. What invariants must remain true?
4. What happens under repeated or concurrent execution?
5. What rollout or rollback constraints matter here?
6. What trust boundaries or sensitive data are involved?
7. What test would prove the behavior and catch regressions?

If you cannot answer these, go back to exploration.
