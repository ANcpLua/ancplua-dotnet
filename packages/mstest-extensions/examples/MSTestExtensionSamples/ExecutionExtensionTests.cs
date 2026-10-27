namespace MSTestExtensionSamples;

[TestClass]
public sealed class ExecutionExtensionTests(TestContext context)
{
    private bool _initialized;

    [TestInitialize]
    public void Initialize() => _initialized = true;

    [DiagnosticTestMethod]
    [DataRow(17)]
    [CapabilityCondition(true)]
    public async Task Wrapper_preserves_initialization_and_data(int argument)
    {
        await Task.Yield();
        Assert.IsTrue(_initialized);
        Assert.AreEqual(17, argument);
        Assert.IsNotNull(context.TestName);
    }

    [TestMethod]
    [DataRow(true, false)]
    [DataRow(false, true)]
    [DataRow(true, true)]
    public void Broken_optional_diagnostics_preserve_the_original_failure(bool brokenCapture, bool brokenSink)
    {
        var original = new AssertFailedException("original failure");
        var observed = Assert.ThrowsExactly<AssertFailedException>(() =>
        {
            try { throw original; }
            finally
            {
                FailureDiagnostics.TryWrite(
                    _ => { if (brokenSink) throw new IOException("sink failure"); },
                    () => brokenCapture ? throw new IOException("capture failure") : "snapshot");
            }
        });
        Assert.AreSame(original, observed);
    }

    [TestMethod]
    [CapabilityCondition(false, ConditionMode.Exclude)]
    public void Exclude_mode_is_applied_by_the_framework()
        => Assert.IsFalse(new CapabilityConditionAttribute(false, ConditionMode.Exclude).IsConditionMet);
}
