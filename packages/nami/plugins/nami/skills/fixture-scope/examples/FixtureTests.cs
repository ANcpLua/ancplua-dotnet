using System;
using System.Collections.Concurrent;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Nami.FixtureExamples.Fixtures;

public enum FixtureScope
{
    Test,
    Class
}

[AttributeUsage(AttributeTargets.Class, Inherited = false)]
public sealed class UsesFixtureAttribute(FixtureScope scope) : TestClassAttribute
{
    public FixtureScope Scope { get; } = scope;
}

public interface IFixture<TSelf> : IAsyncDisposable where TSelf : class, IFixture<TSelf>
{
    static abstract Task<TSelf> CreateAsync(CancellationToken cancellationToken);
}

// MSTest invokes these inherited hooks. Test authors only choose the scope and fixture type.
public abstract class FixtureTests<TFixture> where TFixture : class, IFixture<TFixture>
{
    private static readonly ConcurrentDictionary<string, Lazy<ClassFixture<TFixture>>> ClassFixtures = new();
    private TFixture? _fixture;
    private bool _ownsFixture;

    // MSTest injects TestContext before TestInitialize; only this infrastructure handles absence.
    public TestContext? TestContext { get; set; }

    protected TFixture Fixture => _fixture
        ?? throw new InvalidOperationException("The fixture is outside its test lifetime.");

    protected CancellationToken CancellationToken => Context.CancellationToken;

    private TestContext Context => TestContext
        ?? throw new InvalidOperationException("MSTest has not initialized the test context.");

    [TestInitialize]
    public async Task PrepareFixtureAsync()
    {
        var scope = GetType().GetCustomAttribute<UsesFixtureAttribute>()?.Scope
            ?? throw new InvalidOperationException("Declare UsesFixture with an explicit scope.");
        _ownsFixture = scope switch
        {
            FixtureScope.Test => true,
            FixtureScope.Class => false,
            _ => throw new InvalidOperationException("Unsupported fixture scope.")
        };

        if (_ownsFixture)
        {
            _fixture = await TFixture.CreateAsync(CancellationToken).ConfigureAwait(false);
        }
        else
        {
            var creation = ClassFixtures.GetOrAdd(Context.FullyQualifiedTestClassName,
                static _ => new Lazy<ClassFixture<TFixture>>(
                    static () => new ClassFixture<TFixture>(), LazyThreadSafetyMode.ExecutionAndPublication));
            _fixture = await creation.Value.GetAsync(CancellationToken).ConfigureAwait(false);
        }
    }

    [TestCleanup]
    public async Task ReleaseFixtureAsync()
    {
        var fixture = _fixture;
        _fixture = null;
        if (_ownsFixture && fixture is not null)
            await fixture.DisposeAsync().ConfigureAwait(false);
    }

    [ClassCleanup(InheritanceBehavior.BeforeEachDerivedClass)]
    public static async Task ReleaseClassFixtureAsync(TestContext context)
    {
        if (ClassFixtures.TryRemove(context.FullyQualifiedTestClassName, out var creation))
        {
            if (creation.IsValueCreated)
                await creation.Value.DisposeAsync().ConfigureAwait(false);
        }
    }
}

internal sealed class ClassFixture<TFixture> : IAsyncDisposable where TFixture : class, IFixture<TFixture>
{
    private readonly CancellationTokenSource _lifetime = new();
    private readonly Task<TFixture> _creation;
    private readonly Lazy<Task> _disposal;

    internal ClassFixture()
    {
        _creation = CreateAsync();
        _disposal = new Lazy<Task>(DisposeCoreAsync, LazyThreadSafetyMode.ExecutionAndPublication);
    }

    internal Task<TFixture> GetAsync(CancellationToken cancellationToken) => _creation.WaitAsync(cancellationToken);

    private async Task<TFixture> CreateAsync() => await TFixture.CreateAsync(_lifetime.Token).ConfigureAwait(false);

    public ValueTask DisposeAsync() => new(_disposal.Value);

    private async Task DisposeCoreAsync()
    {
        try
        {
            await _lifetime.CancelAsync().ConfigureAwait(false);
            TFixture fixture;
            try
            {
                fixture = await _creation.ConfigureAwait(false);
            }
            catch (OperationCanceledException error) when (_lifetime.IsCancellationRequested && error.CancellationToken == _lifetime.Token)
            {
                return;
            }
            await fixture.DisposeAsync().ConfigureAwait(false);
        }
        finally
        {
            _lifetime.Dispose();
        }
    }
}
