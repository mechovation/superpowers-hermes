---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing — requires running verification commands and confirming output before making any success claims. Evidence before assertions always.
version: 1.0.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [verification, quality, testing, completion, honesty]
    related_skills: [test-driven-development, systematic-debugging, finishing-a-development-branch]
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this turn, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test output: 0 failures | Previous run, "should pass" |
| Build succeeds | Build command: exit 0 | Linter passing |
| Bug fixed | Original symptom test passes | "Code changed, assumed fixed" |
| Requirements met | Line-by-line checklist | Tests passing alone |
| Agent completed | VCS diff shows changes | Agent reports "success" |

## Red Flags — STOP

If you catch yourself:
- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Done!")
- About to commit/push without verification
- Trusting agent success reports without checking
- Relying on partial verification
- Thinking "just this once"

**ALL of these mean: RUN THE VERIFICATION.**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence != evidence |
| "Just this once" | No exceptions |
| "Agent said success" | Verify independently |
| "Partial check is enough" | Partial proves nothing |

## Key Patterns

**Tests:**
```
OK:  [Run test command] [See: 34/34 pass] "All tests pass"
BAD: "Should pass now" / "Looks correct"
```

**Requirements:**
```
OK:  Re-read plan -> checklist -> verify each -> report gaps or completion
BAD: "Tests pass, phase complete"
```

**Agent delegation:**
```
OK:  Agent reports success -> check diff -> verify changes -> report actual state
BAD: Trust agent report
```

## Hermes Agent Integration

### After delegate_task

When subagents return results:
1. Read the summary
2. Check what files were actually modified
3. Run verification commands yourself
4. Only then claim the task is complete

### With Memory

Record verification outcomes. If a verification method was insufficient (missed a bug), record that so future sessions use better verification.

## The Bottom Line

**No shortcuts for verification.**

Run the command. Read the output. THEN claim the result.

This is non-negotiable.
