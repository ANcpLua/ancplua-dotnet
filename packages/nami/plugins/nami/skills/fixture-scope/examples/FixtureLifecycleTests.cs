using System;
using System.Collections.Concurrent;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Nami.FixtureExamples.Fixtures;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Nami.FixtureExamples;

[UsesFixture(FixtureScope.Class)]
public sealed class ClassScopedFixtureTests : FixtureTests<ClassProbe>
{
    [TestMethod]
    [DataRow(0)]
    [DataRow(1)]
    [DataRow(2)]
    [DataRow(3)]
    [DataRow(4)]
    [DataRow(5)]
    [DataRow(6)]
    [DataRow(7)]
    [DataRow(8)]
    [DataRow(9)]
    public void TenInvocations_ShareOneFixture(int row)
    {
        Assert.IsInRange(0, 9, row);
        Assert.AreEqual(ClassProbe.Assigned.GetOrAdd(nameof(ClassScopedFixtureTests), Fixture.Id), Fixture.Id);
    }
}

[UsesFixture(FixtureScope.Class)]
public sealed class AnotherClassScopedFixtureTests : FixtureTests<ClassProbe>
{
    [TestMethod]
    public void AnotherClass_GetsItsOwnFixture()
    {
        Assert.AreEqual(ClassProbe.Assigned.GetOrAdd(nameof(AnotherClassScopedFixtureTests), Fixture.Id), Fixture.Id);
    }
}

[UsesFixture(FixtureScope.Test)]
public sealed class TestScopedFixtureTests : FixtureTests<TestProbe>
{
    [TestMethod]
    [DataRow(0)]
    [DataRow(1)]
    [DataRow(2)]
    public void EachInvocation_HasItsOwnFixture(int row)
    {
        Assert.IsInRange(0, 2, row);
        Assert.AreEqual(1, Interlocked.Increment(ref Fixture.Uses));
    }
}

[TestClass]
public sealed class FixtureLifecycleTests
{
    [AssemblyInitialize]
    public static void ResetObservations(TestContext _)
    {
        ClassProbe.Created = 0;
        ClassProbe.Disposed = 0;
        ClassProbe.Assigned.Clear();
        TestProbe.Created = 0;
        TestProbe.Disposed = 0;
        InputFixture.CreatedPaths.Clear();
    }

    [TestMethod]
    public void AccessOutsideLifetime_FailsInTheInfrastructure()
    {
        var host = new UninitializedHost();
        var error = Assert.ThrowsExactly<InvalidOperationException>(host.ReadFixture);
        Assert.AreEqual("The fixture is outside its test lifetime.", error.Message);
    }

    [TestMethod]
    public async Task MissingScope_FailsBeforeCreatingAResource()
    {
        var host = new UninitializedHost();
        var error = await Assert.ThrowsExactlyAsync<InvalidOperationException>(host.PrepareFixtureAsync);
        Assert.AreEqual("Declare UsesFixture with an explicit scope.", error.Message);
    }

    [AssemblyCleanup]
    public static void AllScopes_ReleaseTheirResources()
    {
        Assert.AreEqual(ClassProbe.Created, ClassProbe.Disposed, "Class-owned fixtures must be disposed after their class.");
        Assert.AreEqual(ClassProbe.Assigned.Count, ClassProbe.Created, "Each class must create exactly one fixture.");
        Assert.AreEqual(ClassProbe.Assigned.Count, ClassProbe.Assigned.Values.Distinct().Count(), "Different classes must not share a fixture.");
        Assert.AreEqual(TestProbe.Created, TestProbe.Disposed, "Invocation-owned fixtures must be disposed after each invocation.");
        Assert.IsEmpty(InputFixture.CreatedPaths.Where(File.Exists), "The example's shared file must be deleted after its class.");
        Assert.IsLessThanOrEqualTo(1, InputFixture.CreatedPaths.Count, "Both example tests must share one file.");
    }

    private sealed class UninitializedHost : FixtureTests<TestProbe>
    {
        internal TestProbe ReadFixture() => Fixture;
    }
}

public sealed class ClassProbe : IFixture<ClassProbe>
{
    internal static int Created;
    internal static int Disposed;
    internal static ConcurrentDictionary<string, Guid> Assigned { get; } = new();
    public Guid Id { get; } = Guid.NewGuid();

    public static Task<ClassProbe> CreateAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var fixture = new ClassProbe();
        Interlocked.Increment(ref Created);
        return Task.FromResult(fixture);
    }

    public ValueTask DisposeAsync()
    {
        Interlocked.Increment(ref Disposed);
        return ValueTask.CompletedTask;
    }
}

public sealed class TestProbe : IFixture<TestProbe>
{
    internal static int Created;
    internal static int Disposed;
    internal int Uses;

    public static Task<TestProbe> CreateAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        Interlocked.Increment(ref Created);
        return Task.FromResult(new TestProbe());
    }

    public ValueTask DisposeAsync()
    {
        Interlocked.Increment(ref Disposed);
        return ValueTask.CompletedTask;
    }
}
