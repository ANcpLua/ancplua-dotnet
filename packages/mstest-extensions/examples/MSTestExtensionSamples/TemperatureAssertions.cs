namespace MSTestExtensionSamples;

public static class TemperatureAssertions
{
    public static void BeWithin(this Assert _, double actual, double expected, double tolerance)
    {
        if (!double.IsFinite(tolerance) || tolerance < 0)
            throw new ArgumentOutOfRangeException(nameof(tolerance));

        if (!double.IsFinite(actual) || !double.IsFinite(expected)
            || Math.Abs(actual - expected) > tolerance)
        {
            Assert.Fail(FormattableString.Invariant(
                $"Expected {expected} +/- {tolerance}; actual {actual}."));
        }
    }
}

[TestClass]
public sealed class TemperatureAssertionTests
{
    [TestMethod]
    [DataRow(20.0)]
    [DataRow(19.5)]
    [DataRow(20.5)]
    public void Accepts_values_including_the_boundary(double actual)
        => Assert.That.BeWithin(actual, expected: 20, tolerance: 0.5);

    [TestMethod]
    [DataRow(20.6)]
    [DataRow(double.NaN)]
    [DataRow(double.PositiveInfinity)]
    public void Rejects_incorrect_or_nonfinite_values(double actual)
    {
        var failure = Assert.ThrowsExactly<AssertFailedException>(
            () => Assert.That.BeWithin(actual, expected: 20, tolerance: 0.5));
        Assert.Contains("Expected 20 +/- 0.5; actual", failure.Message);
    }

    [TestMethod]
    [DataRow(-1.0)]
    [DataRow(double.NaN)]
    [DataRow(double.PositiveInfinity)]
    public void Rejects_invalid_tolerance(double tolerance)
        => Assert.ThrowsExactly<ArgumentOutOfRangeException>(
            () => Assert.That.BeWithin(20, expected: 20, tolerance));
}
