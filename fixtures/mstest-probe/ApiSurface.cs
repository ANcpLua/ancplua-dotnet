// Every MSTest API that skills/mstest names must compile here against MSTest.Sdk 4.5.1.
using Microsoft.VisualStudio.TestTools.UnitTesting.Combinatorial;

[assembly: Parallelize(Scope = ExecutionScope.MethodLevel)]

namespace MSTestProbe;

[TestClass]
public sealed class ApiSurface(TestContext context)
{
    public static IEnumerable<(int, string)> Tuples => [(1, "a")];

    public static IEnumerable<TestDataRow<int>> Rows =>
    [
        new(1) { DisplayName = "one", TestCategories = ["fast"] },
        new(2) { ArgumentsDisplayName = "two" },
        new(3) { IgnoreMessage = "probe: an ignored row is reported as skipped" },
    ];

    [GlobalTestInitialize]
    public static void GlobalInit(TestContext testContext) { }

    [GlobalTestCleanup]
    public static void GlobalCleanup(TestContext testContext) { }

    [TestMethod, DataRow(1, "a", DisplayName = "row")]
    public void DataRows(int i, string s) { Assert.AreEqual(1, i); Assert.AreEqual("a", s); }

    [TestMethod, DynamicData(nameof(Tuples))]
    public void DynamicTuples(int i, string s) => Assert.HasCount(1, s);

    [TestMethod(UnfoldingStrategy = TestDataSourceUnfoldingStrategy.Unfold), DynamicData(nameof(Rows))]
    public void DynamicRows(int i) => Assert.IsPositive(i);

    [TestMethod, CombinatorialData]
    public void Combinations(bool flag, [CombinatorialValues(1, 2)] int n, [CombinatorialRange(0, 2)] int r) =>
        Assert.IsLessThanOrEqualTo(2, n);

    [TestMethod, Timeout(2000, CooperativeCancellation = true)]
    public async Task Cooperative() => await Task.Delay(1, context.CancellationToken);

    [TestMethod, OSCondition(OperatingSystems.Linux | OperatingSystems.OSX | OperatingSystems.Windows)]
    public void Os() { }

    [TestMethod, CICondition(ConditionMode.Exclude)]
    public void NotOnCi() { }

    [TestMethod, Retry(3)]
    public void Retried() { }

    [TestMethod, ResourceLock(WellKnownResources.EnvironmentVariables)]
    public void Locked() => Assert.IsNotNull(context.TestTempDirectory);

    [TestMethod]
    public async Task Assertions()
    {
        object o = "s";
        var s = Assert.IsInstanceOfType<string>(o);
        var ex = Assert.ThrowsExactly<InvalidOperationException>(() => throw new InvalidOperationException("m"));
        Assert.Throws<Exception>(() => throw new ArgumentException());
        await Assert.ThrowsExactlyAsync<InvalidOperationException>(() => Task.FromException(new InvalidOperationException()));
        List<int> list = [1];
        Assert.HasCount(1, list);
        Assert.IsNotEmpty(list);
        Assert.IsEmpty(new List<int>());
        Assert.Contains(1, list);
        Assert.DoesNotContain(2, list);
        var only = Assert.ContainsSingle(list);
        Assert.ContainsAll(new[] { 1 }, list);
        Assert.AreEquivalent(new List<int> { 1 }, list);
        Assert.AreSequenceEqual(new[] { 1 }, list);
        Assert.Contains("s", s);
        Assert.StartsWith("s", s);
        Assert.DoesNotStartWith("x", s);
        Assert.EndsWith("s", s);
        Assert.MatchesRegex("^s$", s);
        Assert.DoesNotMatchRegex("^x$", s);
        Assert.IsInRange(0, 2, only);
        Assert.IsGreaterThan(0, only);
        Assert.IsNegative(-1);
        Assert.That.IsProbeValue(only);
        context.WriteLine(ex.Message);
        _ = context.Properties.ContainsKey("x");
        _ = context.FullyQualifiedTestClassName;
    }
}

public sealed class OnlyOnFridays() : ConditionBaseAttribute(ConditionMode.Include)
{
    public override string GroupName => nameof(OnlyOnFridays);
    public override bool IsConditionMet => DateTime.UtcNow.DayOfWeek == DayOfWeek.Friday;
}

public static class ProbeAssertions
{
    public static void IsProbeValue(this Assert assert, int value)
    {
        if (value != 1)
        {
            Assert.Fail($"probe value must be 1, was {value}");
        }
    }
}
