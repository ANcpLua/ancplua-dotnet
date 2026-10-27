namespace MSTestExtensionSamples;

[TestClass]
public sealed class SuspensionTests(TestContext context)
{
    [TestMethod]
    [ReadCases]
    [Timeout(10_000, CooperativeCancellation = true)]
    public async Task Copy_resumes_without_disposing_source(ReadCase scenario)
    {
        byte[] bytes = "payload after suspension 🧪"u8.ToArray();
        await using var source = new PausedReadStream(bytes, scenario.ChunkSize);
        using var destination = new MemoryStream();
        var copying = source.CopyToAsync(destination, context.CancellationToken);
        bool wasPending;
        try
        {
            await Task.WhenAny(source.Paused, copying);
            wasPending = source.Paused.IsCompletedSuccessfully && !copying.IsCompleted;
        }
        finally { source.Resume(); }
        await copying;

        Assert.IsTrue(wasPending);
        Assert.AreSequenceEqual(bytes, destination.ToArray());
        Assert.IsTrue(source.CanRead);
    }

    [TestMethod]
    [Timeout(10_000, CooperativeCancellation = true)]
    public async Task Cancellation_joins_the_copy_before_disposal()
    {
        await using var source = new PausedReadStream([1, 2, 3], 1);
        using var destination = new MemoryStream();
        using var cancellation = CancellationTokenSource.CreateLinkedTokenSource(context.CancellationToken);
        var copying = source.CopyToAsync(destination, cancellation.Token);
        bool wasPending;
        OperationCanceledException? observed = null;
        try
        {
            await Task.WhenAny(source.Paused, copying);
            wasPending = source.Paused.IsCompletedSuccessfully && !copying.IsCompleted;
            await cancellation.CancelAsync();
        }
        finally
        {
            source.Resume();
            try { await copying; }
            catch (OperationCanceledException exception) when (exception.CancellationToken == cancellation.Token)
            { observed = exception; }
        }

        Assert.IsTrue(wasPending);
        Assert.IsNotNull(observed);
        Assert.AreEqual(0L, destination.Length);
        Assert.IsTrue(source.CanRead);
    }

    [TestMethod]
    public async Task Failed_observation_still_joins_before_disposal()
    {
        var source = new PausedReadStream([42], 1);
        using var destination = new MemoryStream();
        Task? copying = null;
        var original = new AssertFailedException("observation failed");
        var observed = await Assert.ThrowsExactlyAsync<AssertFailedException>(async () =>
        {
            await using (source)
            {
                copying = source.CopyToAsync(destination, context.CancellationToken);
                try
                {
                    await Task.WhenAny(source.Paused, copying);
                    throw original;
                }
                finally
                {
                    source.Resume();
                    await copying;
                }
            }
        });

        Assert.AreSame(original, observed);
        Assert.IsTrue(copying!.IsCompletedSuccessfully);
        Assert.AreSequenceEqual(new byte[] { 42 }, destination.ToArray());
        Assert.IsTrue(source.Disposed);
    }
}
