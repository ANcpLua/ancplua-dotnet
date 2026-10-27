using System.Reflection;
using Microsoft.VisualStudio.TestTools.UnitTesting.Combinatorial;

namespace MSTestExtensionSamples;

public sealed record ReadCase(string Name, int ChunkSize);

[AttributeUsage(AttributeTargets.Method)]
public sealed class ReadCasesAttribute : Attribute, ITestDataSource
{
    public IEnumerable<object?[]> GetData(MethodInfo methodInfo)
    {
        yield return [new ReadCase("single-byte", 1)];
        yield return [new ReadCase("fragmented", 3)];
        yield return [new ReadCase("whole-buffer", 64)];
    }

    public string GetDisplayName(MethodInfo methodInfo, object?[]? data)
        => $"{methodInfo.Name}({((ReadCase)data![0]!).Name})";
}

[AttributeUsage(AttributeTargets.Parameter)]
public sealed class BufferSizesAttribute : Attribute, ICombinatorialValuesProvider
{
    public object?[] GetValues(ParameterInfo parameter) => [1, 7];
}

[TestClass]
public sealed class DataExtensionTests(TestContext context)
{
    public static IEnumerable<TestDataRow<(string Input, int ExpectedBytes)>> Utf8Cases()
    {
        yield return new(("ASCII", 5)) { DisplayName = "ASCII bytes" };
        yield return new(("é", 2)) { DisplayName = "Multibyte UTF-8" };
    }

    [TestMethod]
    [DynamicData(nameof(Utf8Cases))]
    public void Typed_rows_reach_the_method(string input, int expectedBytes)
        => Assert.AreEqual(expectedBytes, System.Text.Encoding.UTF8.GetByteCount(input));

    [TestMethod]
    [CombinatorialData]
    public async Task Utf8_round_trip_across_buffers_and_bom(
        [BufferSizes] int bufferSize, bool includeBom)
    {
        const string payload = "fragmented 🧪 payload";
        var encoding = new System.Text.UTF8Encoding(includeBom);
        byte[] bytes = [.. encoding.GetPreamble(), .. encoding.GetBytes(payload)];
        await using var source = new PausedReadStream(bytes, bufferSize);
        source.Resume();
        using var reader = new StreamReader(source, encoding, true, bufferSize, leaveOpen: true);

        Assert.AreEqual(payload, await reader.ReadToEndAsync(context.CancellationToken));
        Assert.IsTrue(source.CanRead);
    }

}
