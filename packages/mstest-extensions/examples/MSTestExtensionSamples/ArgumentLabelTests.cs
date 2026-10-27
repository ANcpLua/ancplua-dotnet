namespace MSTestExtensionSamples;

[TestClass]
public sealed class ArgumentLabelTests
{
    [TestMethod]
    [DataRow("é", 2, ArgumentsDisplayName = "inline-label")]
    public void Inline_label_keeps_method_name(string text, int bytes)
    {
        Assert.AreEqual(bytes, System.Text.Encoding.UTF8.GetByteCount(text));
    }

    public static IEnumerable<TestDataRow<(string Text, int Bytes)>> Rows()
    {
        yield return new(("🧪", 4)) { ArgumentsDisplayName = "dynamic-label" };
    }

    [TestMethod]
    [DynamicData(nameof(Rows))]
    public void Dynamic_label_keeps_method_name(string text, int bytes)
    {
        Assert.AreEqual(bytes, System.Text.Encoding.UTF8.GetByteCount(text));
    }
}
