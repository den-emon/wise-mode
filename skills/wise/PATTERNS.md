# Common Patterns & Anti-Patterns

Reference document for the **wise** skill.

`SKILL.md` defines the workflow.
This file gives concrete implementation and testing patterns for tricky areas.

Use it when working with:
- shared mutable state,
- async/retry behavior,
- transactions and side effects,
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
````

Why this is dangerous:

* another worker may claim the record after the read,
* repeated execution may double-process work,
* you can violate invariants while “looking correct” in tests.

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
    # another worker already claimed it
    handle_already_claimed()
```

Look for:

* read-then-act flows,
* “if not exists, then create” without uniqueness protection,
* retries that can re-run side effects.

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

* same request/event twice,
* retry after partial failure,
* out-of-order delivery if relevant.

---

### 1.3 Shared-State Invariant Thinking

Before changing shared state, write down:

* who can modify it,
* under what conditions,
* what must always be true after the operation.

Example invariant set:

* an order cannot be both `paid` and `canceled`,
* only one worker can own a job at a time,
* a balance cannot go negative unless overdraft is explicitly allowed.

If you cannot state the invariants clearly, you are not ready to edit the code.

---

## 2) Transaction and Side-Effect Patterns

### 2.1 Side Effects That Must Survive Failure

A common mistake is writing important error/audit state inside a transaction that later rolls back.

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

* Which writes are part of the atomic business change?
* Which writes are diagnostic or compensating and must persist even on failure?
* What happens if the failure occurs halfway through?

---

### 2.2 Partial Failure Awareness

When external calls are involved, identify what happens if:

* DB write succeeds but external API call fails,
* external API call succeeds but local state update fails,
* timeout occurs after remote side effect actually happened.

Typical mitigations:

* idempotency keys,
* outbox/inbox patterns,
* compensating actions,
* explicit reconciliation jobs,
* durable status markers.

---

## 3) Test Patterns

### 3.1 Mutation-Resistant Assertions

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

* the wrong branch executed,
* a condition changed from `>` to `>=`,
* one field updated but another did not,
* the visible output is “truthy” but semantically wrong.

---

### 3.2 Boundary Testing

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

* duplicate inputs,
* malformed inputs,
* extreme but valid inputs,
* transition edges between states.

---

### 3.3 Side-Effect Assertions

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

Do not stop at “the function returned success.”
Check the state you actually care about.

---

### 3.4 Characterization Tests for Legacy Code

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

* use real observed inputs where possible,
* capture current behavior faithfully,
* do not “improve” the behavior inside the characterization test,
* once protected, refactor or change behavior intentionally.

---

### 3.5 Contract-Level Testing

If the change affects an interface, validate the contract rather than only internals.

Examples:

* HTTP response shape and status codes,
* event payload schema,
* CLI exit codes and output,
* database persistence visible to callers,
* public method behavior under invalid input.

A passing unit test is not enough if the public contract changed silently.

---

## 4) Implementation Patterns

### 4.1 Constants Over Magic Values

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

### 4.2 Reuse Local Conventions

Before adding a helper, abstraction, logger shape, or error type, check what already exists.

Look for:

* validation helpers,
* domain errors,
* config access patterns,
* logging fields,
* API response helpers,
* existing fixtures/builders in tests.

A “clean” abstraction that ignores repository conventions often increases maintenance cost.

---

### 4.3 DRY — But Only for Real Duplication

Do not extract abstractions from one occurrence.
Do extract when:

* the same logic exists in multiple places,
* the duplication creates bug risk,
* the shared behavior is conceptually stable.

```text
# useful search prompts
grep -rn "same_pattern" .
grep -rn "status = .*pending" .
grep -rn "normalize.*input" .
```

Bad DRY creates indirection without reducing risk.
Good DRY removes repeated behavior that would otherwise drift.

---

### 4.4 Smallest Safe Change

Prefer:

* narrower scope,
* existing extension points,
* fewer files,
* fewer new concepts,
* easier rollback,
* easier testability.

Avoid:

* opportunistic cleanup unrelated to the task,
* replacing patterns the codebase already standardized,
* introducing architecture-level changes to solve a local bug unless clearly necessary.

---

## 5) Verification Patterns

### 5.1 Review the Diff, Not Just the Result

Always inspect what changed.

Useful commands:

```bash
git diff
git diff --staged
git diff main...HEAD
```

Questions during diff review:

* Did I change only what I intended?
* Did I accidentally rename, reformat, or move unrelated code?
* Is the final naming clear?
* Is there hidden coupling I glossed over while coding?

---

### 5.2 Test Scope Selection

Choose the smallest scope that still gives credible confidence.

Examples:

* tiny isolated fix → related test file,
* feature-local change → feature/module suite,
* shared utility change → all dependents likely affected,
* schema/auth/concurrency change → broaden validation.

Do not confuse “fastest possible run” with “sufficient validation.”

---

## 6) Anti-Patterns to Watch For

### 6.1 Hallucinated Structure

You referenced a file, method, class, constant, or config flag without verifying it exists.

### 6.2 Patch-Through Design Failure

The original design is clearly wrong, but you keep adding conditions instead of rethinking it.

### 6.3 Assertion Poverty

Tests only check truthiness, status 200, or “no exception,” while missing the real behavior.

### 6.4 Hidden Scope Creep

The change quietly includes refactors, renames, and cleanup unrelated to the task.

### 6.5 Concurrency Blindness

The code looks correct for one caller but breaks under retries, parallel workers, or duplicate events.

### 6.6 Rollback Confusion

Error/audit state is written inside a transaction and disappears exactly when you need it most.

---

## 7) Pre-Flight Questions

Before writing code, answer these:

1. What are all the ways this code can be reached?
2. What other code reads or mutates the same state?
3. What invariants must remain true?
4. What happens under repeated or concurrent execution?
5. What edge cases matter here?
6. What test would prove the behavior and catch regressions?

If you cannot answer these, go back to exploration.
