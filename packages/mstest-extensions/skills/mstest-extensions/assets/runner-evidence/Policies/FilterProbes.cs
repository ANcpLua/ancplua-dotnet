using MSTestExtensionEvidence.Policies;

#pragma warning disable MSTESTEXP // Only this provider and registration opt into the experimental filter API.
[assembly: DoNotParallelize]
[assembly: TestFilterProvider<RecordedFilter>]

namespace MSTestExtensionEvidence.Policies;

public sealed class RecordedFilter : ITestFilter
{
    public TestFilterResult Filter(TestFilterContext context)
    {
        var decision = context.Categories.Contains("drop") ? "drop" :
            context.Categories.Contains("skip") ? "skip" : context.Categories.Contains("throw") ? "throw" : "run";
        Evidence.Record("filter", context.FullyQualifiedName, decision);
        return decision switch
        {
            "drop" => TestFilterResult.Drop,
            "skip" => TestFilterResult.Skip("filter-skip-original-marker"),
            "throw" => throw new InvalidOperationException("filter-throw-original-marker"),
            _ => TestFilterResult.Run,
        };
    }
}

#pragma warning restore MSTESTEXP

[TestClass]
public sealed class FilterRunProbe
{
    public FilterRunProbe() => Evidence.Record("construct", nameof(FilterRunProbe));
    [TestMethod]
    public void RunExecutesTheBody() => Evidence.Record("body", nameof(FilterRunProbe));
}

[TestClass]
public sealed class FilterSkipProbe
{
    public FilterSkipProbe() => Evidence.Record("construct", nameof(FilterSkipProbe));
    [TestMethod, TestCategory("skip")]
    public void SkipHasAReportedReason() => Assert.Fail("A skipped body must not run.");
}

[TestClass]
public sealed class FilterDropProbe
{
    public FilterDropProbe() => Evidence.Record("construct", nameof(FilterDropProbe));
    [TestMethod, TestCategory("drop")]
    public void DropHasNoResult() => Assert.Fail("A dropped body must not run.");
}

[TestClass]
public sealed class FilterThrowProbe
{
    public FilterThrowProbe() => Evidence.Record("construct", nameof(FilterThrowProbe));
    [TestMethod, TestCategory("throw")]
    public void AThrowIsAFailure() => Assert.Fail("A throwing filter must prevent construction and execution.");
}
