using System.Runtime.CompilerServices;
using MSTestExtensionSamples;

[assembly: DoNotParallelize]

namespace MSTestExtensionProbes;

[AttributeUsage(AttributeTargets.Method)]
public sealed class BrokenCaptureTestMethodAttribute(
    [CallerFilePath] string file = "", [CallerLineNumber] int line = -1)
    : DiagnosticTestMethodAttribute(file, line)
{
    protected override string Capture(ITestMethod method) => throw new IOException("capture broke");
}

[AttributeUsage(AttributeTargets.Method)]
public sealed class BrokenOutputTestMethodAttribute(
    [CallerFilePath] string file = "", [CallerLineNumber] int line = -1)
    : DiagnosticTestMethodAttribute(file, line)
{
    protected override void Append(TestResult result, string text) => throw new IOException("output broke");
}

[ComposedTestClass]
public sealed class FailureProbes
{
    private bool _initialized;

    [TestInitialize]
    public void Initialize() => _initialized = true;

    [DiagnosticTestMethod]
    [DataRow(17)]
    public async Task Original_failure_is_reported(int value)
    {
        await Task.Yield();
        Assert.IsTrue(_initialized);
        Assert.AreEqual(17, value);
        Assert.Fail("original-failure-marker");
    }

    [BrokenCaptureTestMethod]
    public void Broken_capture_preserves_failure() => Assert.Fail("capture-original-marker");

    [BrokenOutputTestMethod]
    public void Broken_output_preserves_failure() => Assert.Fail("output-original-marker");

    [DiagnosticTestMethod]
    public void Inconclusive_stays_inconclusive() => Assert.Inconclusive("inconclusive-marker");

    [TestMethod]
    [CapabilityCondition(false, IgnoreMessage = "capability-unavailable-marker")]
    public void False_condition_skips_body() => Assert.Fail("condition body must not execute");
}
