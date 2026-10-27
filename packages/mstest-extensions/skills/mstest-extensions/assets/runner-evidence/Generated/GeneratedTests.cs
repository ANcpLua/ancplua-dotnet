using System.Runtime.CompilerServices;

[assembly: DoNotParallelize]

namespace MSTestExtensionEvidence.Generated;

[TestClass]
public sealed class GeneratedTests
{
    private readonly string _constructorStack = Environment.StackTrace;
    private string _invocation = "";

    [TestInitialize]
    public void Initialize()
    {
        _invocation = Guid.NewGuid().ToString("N");
        Evidence.Record("generated-initialize", _invocation);
    }

    [TestMethod, DataRow(long.MinValue), DataRow(long.MaxValue)]
    public void Int64ValuesRemainExact(long value)
    {
        Evidence.Record("generated-body", _invocation, "int64");
        Evidence.Record("generated-int64", _invocation, value.ToString(System.Globalization.CultureInfo.InvariantCulture));
        Assert.That.HasExactInt64(value, value);
    }

    [TestMethod]
    public void GeneratedMetadataOwnsConstructionAndInvocation()
    {
        Evidence.Record("generated-body", _invocation, "metadata");
        Assert.Contains("MSTest.SourceGenerated.MSTestReflectionMetadata", _constructorStack);
        Assert.Contains("MSTest.SourceGenerated.MSTestReflectionMetadata", Environment.StackTrace);
        Assert.DoesNotContain("System.Reflection", _constructorStack);
    }

    [TestMethod]
    public async Task AsyncContinuationFinishesBeforeCleanup()
    {
        Evidence.Record("generated-body", _invocation, "async");
        await Task.Yield();
        Assert.AreNotEqual("", _invocation);
        Evidence.Record("generated-resumed", _invocation);
    }

    [TestMethod]
    public void PublishedRuntimeMatchesTheClaim()
    {
        Evidence.Record("generated-body", _invocation, "runtime");
        var native = bool.Parse(Environment.GetEnvironmentVariable("MSTEST_EVIDENCE_NATIVE")!);
        Assert.AreEqual(native, !RuntimeFeature.IsDynamicCodeSupported);
    }

    [TestMethod]
    public void RejectionKeepsTheOriginalFailure()
    {
        Evidence.Record("generated-body", _invocation, "rejection");
        // Deliberate runner failure: a rounded double must not masquerade as an Int64.
        Assert.That.HasExactInt64((double)9_007_199_254_740_993L, 9_007_199_254_740_993L,
            "typed-value-original-marker");
    }

    [TestCleanup]
    public void Cleanup() => Evidence.Record("generated-cleanup", _invocation);
}
