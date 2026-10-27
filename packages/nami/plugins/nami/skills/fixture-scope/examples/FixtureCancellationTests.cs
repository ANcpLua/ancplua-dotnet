using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Nami.FixtureExamples.Fixtures;

namespace Nami.FixtureExamples;

[TestClass]
[DoNotParallelize]
public sealed class FixtureCancellationTests(TestContext context)
{
    [TestInitialize]
    public void ResetCreation() => CancellableProbe.Reset();

    [TestMethod]
    public async Task CancelledWaiter_DoesNotCancelSharedCreation()
    {
        await using var owner = new ClassFixture<CancellableProbe>();
        await CancellableProbe.Started.Task.WaitAsync(context.CancellationToken);
        using var waiter = new CancellationTokenSource();
        var waiting = owner.GetAsync(waiter.Token);

        await waiter.CancelAsync();

        await Assert.ThrowsAsync<OperationCanceledException>(() => waiting);
        Assert.IsFalse(CancellableProbe.CreationToken.IsCancellationRequested);
        CancellableProbe.Ready.SetResult();
        var fixture = await owner.GetAsync(context.CancellationToken);
        Assert.AreSame(fixture, await owner.GetAsync(context.CancellationToken));
    }

    [TestMethod]
    public async Task OwnerDisposal_CancelsPendingCreation()
    {
        var owner = new ClassFixture<CancellableProbe>();
        await CancellableProbe.Started.Task.WaitAsync(context.CancellationToken);

        await owner.DisposeAsync();

        Assert.IsTrue(CancellableProbe.CreationToken.IsCancellationRequested);
        Assert.IsTrue(CancellableProbe.CancellationObserved);
    }

    [TestMethod]
    public async Task OwnerDisposal_DisposesCompletedFixtureExactlyOnce()
    {
        var owner = new ClassFixture<CancellableProbe>();
        CancellableProbe.Ready.SetResult();
        var fixture = await owner.GetAsync(context.CancellationToken);

        await owner.DisposeAsync();
        await owner.DisposeAsync();

        Assert.AreEqual(1, fixture.DisposalCount);
    }
}

internal sealed class CancellableProbe : IFixture<CancellableProbe>
{
    internal static TaskCompletionSource Started { get; private set; } = NewCompletion();
    internal static TaskCompletionSource Ready { get; private set; } = NewCompletion();
    internal static CancellationToken CreationToken { get; private set; }
    internal static bool CancellationObserved { get; private set; }
    internal int DisposalCount { get; private set; }

    internal static void Reset()
    {
        Started = NewCompletion();
        Ready = NewCompletion();
        CreationToken = default;
        CancellationObserved = false;
    }

    public static async Task<CancellableProbe> CreateAsync(CancellationToken cancellationToken)
    {
        CreationToken = cancellationToken;
        Started.SetResult();
        try
        {
            await Ready.Task.WaitAsync(cancellationToken).ConfigureAwait(false);
            return new CancellableProbe();
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            CancellationObserved = true;
            throw;
        }
    }

    public ValueTask DisposeAsync()
    {
        DisposalCount++;
        return ValueTask.CompletedTask;
    }

    private static TaskCompletionSource NewCompletion() => new(TaskCreationOptions.RunContinuationsAsynchronously);
}
