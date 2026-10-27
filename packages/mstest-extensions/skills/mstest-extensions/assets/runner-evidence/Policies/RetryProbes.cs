
namespace MSTestExtensionEvidence.Policies;

#pragma warning disable MSTESTEXP // The reusable retry policy deliberately exercises this experimental API.
[AttributeUsage(AttributeTargets.Method)]
public sealed class RetryUntilPassedAttribute(int maximumRetries) : RetryBaseAttribute
{
    protected override async Task<RetryResult> ExecuteAsync(RetryContext context)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(maximumRetries, 1);
        Assert.Contains(static result => result.Outcome != UnitTestOutcome.Passed, context.FirstRunResults);
        Evidence.Record("policy-first", detail: context.FirstRunResults[0].TestFailureException?.Message ?? "no exception");
        var history = new RetryResult();
        do
        {
            history.AddResult(await context.ExecuteTaskGetter());
        }
        while (history.AllResults.Count < maximumRetries &&
               history.AllResults[^1].Any(static result => result.Outcome != UnitTestOutcome.Passed));
        return history;
    }
}
#pragma warning restore MSTESTEXP

[TestClass]
public sealed class RetryPassProbe
{
    private static int _attempt;
    [TestMethod, RetryUntilPassed(2)]
    public void FailureThenInconclusiveThenPass()
    {
        var attempt = Interlocked.Increment(ref _attempt);
        Evidence.Record("retry-pass", detail: attempt.ToString(System.Globalization.CultureInfo.InvariantCulture));
        if (attempt == 1) Assert.Fail("retry-pass-original-marker");
        if (attempt == 2) Assert.Inconclusive("retry-inconclusive-original-marker");
        Assert.AreEqual(3, attempt);
    }
}

[TestClass]
public sealed class RetryExhaustedProbe
{
    private static int _attempt;
    [TestMethod, RetryUntilPassed(2)]
    public void ExhaustionPreservesTheFinalFailure()
    {
        var attempt = Interlocked.Increment(ref _attempt);
        Evidence.Record("retry-exhausted", detail: attempt.ToString(System.Globalization.CultureInfo.InvariantCulture));
        Assert.Fail($"retry-exhausted-original-marker-{attempt}");
    }
}

[TestClass]
public sealed class RetryCancellationProbe(TestContext context)
{
    private readonly string _id = Guid.NewGuid().ToString("N");
    [TestMethod, Retry(1), Timeout(200, CooperativeCancellation = true)]
    public async Task CancellationJoinsTheBodyBeforeCleanup()
    {
        Evidence.Record("cancel-start", _id);
        try { await Task.Delay(Timeout.InfiniteTimeSpan, context.CancellationToken); }
        catch (OperationCanceledException)
        {
            Evidence.Record("cancel-observed", _id);
            throw;
        }
        finally { Evidence.Record("cancel-joined", _id); }
    }

    [TestCleanup]
    public void Cleanup() => Evidence.Record("cancel-cleanup", _id);
}
