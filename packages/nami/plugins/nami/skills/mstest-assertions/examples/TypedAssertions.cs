using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace AssertionExamples;

// Explicit public contract. Add a field assertion when this contract grows.
// This has no reflection-based graph assertion or expression-tree assertion.
public sealed record Receipt(int Id, string Status, int[] LineIds);

public static class ReceiptAssertions
{
    public static void Matches(Receipt expected, Receipt actual)
    {
        Assert.AreEqual(expected.Id, actual.Id);
        Assert.AreEqual(expected.Status, actual.Status);
        Assert.AreSequenceEqual(expected.LineIds, actual.LineIds);
    }

    // Assert.That is the extension-point singleton here, not That(() => ...).
    public static void HasReceipt(this Assert _, Receipt expected, Receipt actual) => Matches(expected, actual);

    public static void ThroughExtensionPoint(Receipt expected, Receipt actual) =>
        Assert.That.HasReceipt(expected, actual);
}
