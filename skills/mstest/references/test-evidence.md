# Does the test prove the change?

Use this when the question is whether tests demonstrate a fix or a behavior, not whether they look
tidy. Keep three evidence classes apart in the report:

- **Static:** read in the code; nothing ran.
- **Hypothesis:** a suspected weakness that hasn't been executed.
- **Executed:** a run that failed or passed, with the stated reason checked in its output.

## 1. Assertion strength

For each test, ask which plausible wrong result would still pass. Typical answers:

- It asserts only `IsNotNull`, a count or `AreNotEqual(old, actual)`, so any wrong non-null value
  passes.
- The input already has the shape of the output (lowercase text into `ToLower`), so a no-op passes.
- The expected value comes from the code under test (calling the same helper, or reading back what
  was just written through the same path), so the oracle isn't independent.
- A property is checked before the object that holds it, so a null fails with a
  `NullReferenceException` instead of a diagnosable assertion. Assert the parent first, or use the
  typed return of `Assert.IsInstanceOfType<T>` or `Assert.ContainsSingle`.

Strengthen the test by asserting the exact expected value from an independent source: a literal,
a hand-computed result or a specification example.

## 2. Change evidence (counterexample probe)

To show a test protects a fix:

1. Re-introduce the defect, or substitute a plausible wrong result in the code under test. Keep
   the test untouched.
2. Run the test. It must fail **for the asserted reason**: read the assertion message. A compile
   error, a crash in setup or an unrelated failure doesn't count.
3. Restore the code, run again, and confirm it passes.
4. Report both runs as executed evidence, with the commands, exit codes and the failing assertion
   line.

Never leave the probe in the working tree. If the repository has uncommitted work by someone else,
probe in a separate worktree.

## 3. Gap mapping

Map each caller-visible outcome of the changed code (return values, thrown exceptions, side
effects, state transitions) to the tests that reach it, and sort the outcomes into:

- **Statically uncovered:** no test reaches the outcome.
- **Suspected weak:** a test reaches it, but section 1 finds a passing wrong result. This is a
  hypothesis until probed.
- **Executed survivor:** a probe from section 2 made the code wrong and every test still passed.

A coverage percentage establishes none of these. Use it only to find code no test executes, then
map outcomes for that code.

## 4. Output

```text
outcome | tests that reach it | class (uncovered / weak / survivor / proven) | evidence | proposed test
```

Propose the smallest test that turns each gap into "proven", and run the probe for it.
