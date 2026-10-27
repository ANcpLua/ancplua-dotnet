using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

[assembly: DoNotParallelize]

namespace MSTestExtensionEvidence.Hosting;

public static class TestHost
{
    public static Task<IHost> CreateHost()
    {
        var builder = Host.CreateApplicationBuilder();
        builder.Logging.ClearProviders();
#pragma warning disable MSTESTEXP // This optional consumer opts into MSTest's experimental hosting integration.
        builder.Services.AddMSTestTestClassInjection();
#pragma warning restore MSTESTEXP
        builder.Services.AddHostedService<RootLifetime>();
        builder.Services.AddScoped<InvocationLease>();
        Evidence.Record("host-created");
        return Task.FromResult(builder.Build());
    }
}

public sealed class RootLifetime : IHostedService, IDisposable
{
    public Task StartAsync(CancellationToken cancellationToken)
    {
        Evidence.Record("host-started");
        return Task.CompletedTask;
    }
    public Task StopAsync(CancellationToken cancellationToken)
    {
        Evidence.Record("host-stopped");
        return Task.CompletedTask;
    }
    public void Dispose() => Evidence.Record("host-disposed");
}

public sealed class InvocationLease : IAsyncDisposable
{
    public string Id { get; } = Guid.NewGuid().ToString("N");
    public bool Disposed { get; private set; }
    public int Value { get; set; }
    public InvocationLease() => Evidence.Record("scope-created", Id);
    public async ValueTask DisposeAsync()
    {
        await Task.Yield();
        Disposed = true;
        Evidence.Record("scope-disposed", Id);
    }
}

[TestClass]
public sealed class InvocationScopes(InvocationLease lease, IServiceProvider services, TestContext context)
{
    private static int _retry;

    [TestInitialize]
    public void Initialize()
    {
        Assert.IsFalse(lease.Disposed);
        Assert.AreEqual(0, lease.Value);
        Assert.AreSame(lease, services.GetRequiredService<InvocationLease>());
        Evidence.Record("scope-initialize", lease.Id, context.TestDisplayName ?? "");
    }

    [TestMethod, DataRow(2), DataRow(5)]
    public void RowsReceiveDistinctScopes(int increment)
    {
        lease.Value = increment;
        Evidence.Record("scope-body", lease.Id, increment.ToString(System.Globalization.CultureInfo.InvariantCulture));
    }

    [TestMethod, Retry(1)]
    public void RetryReceivesANewScope()
    {
        lease.Value = 7;
        var attempt = Interlocked.Increment(ref _retry);
        Evidence.Record("scope-body", lease.Id, "retry-" + attempt);
        if (attempt == 1) Assert.Fail("hosting-retry-original-marker");
        Assert.AreEqual(2, attempt);
    }

    [TestCleanup]
    public void Cleanup()
    {
        Assert.IsFalse(lease.Disposed);
        Assert.IsTrue(lease.Value is 2 or 5 or 7);
        Evidence.Record("scope-cleanup", lease.Id);
    }
}
