using System.Runtime.CompilerServices;

namespace MSTestExtensionSamples;

public static class FailureDiagnostics
{
    public static void TryWrite(Action<string> write, Func<string> capture)
    {
        try
        {
            write(capture());
        }
        catch (Exception)
        {
            // Optional diagnostics cannot change a test's result.
        }
    }
}

[AttributeUsage(AttributeTargets.Method)]
public class DiagnosticTestMethodAttribute(
    [CallerFilePath] string declaringFilePath = "",
    [CallerLineNumber] int declaringLineNumber = -1)
    : TestMethodAttribute(declaringFilePath, declaringLineNumber)
{
    public override async Task<TestResult[]> ExecuteAsync(ITestMethod testMethod)
    {
        var results = await base.ExecuteAsync(testMethod);
        foreach (var result in results)
        {
            if (result.Outcome == UnitTestOutcome.Failed)
                FailureDiagnostics.TryWrite(text => Append(result, text), () => Capture(testMethod));
        }
        return results;
    }

    protected virtual string Capture(ITestMethod method)
        => $"diagnostic: {method.TestClassName}.{method.TestMethodName}";

    protected virtual void Append(TestResult result, string text)
        => result.LogOutput += text + Environment.NewLine;
}

[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method, Inherited = false)]
public sealed class CapabilityConditionAttribute(bool available, ConditionMode mode = ConditionMode.Include)
    : ConditionBaseAttribute(mode)
{
    public override string GroupName => nameof(CapabilityConditionAttribute);
    public override bool IsConditionMet => available;
}
