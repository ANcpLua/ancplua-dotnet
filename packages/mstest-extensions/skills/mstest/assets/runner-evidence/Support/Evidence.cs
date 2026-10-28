using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace MSTestExtensionEvidence;

public static class Evidence
{
    private static readonly Lock Gate = new();

    public static void Record(string action, string id = "", string detail = "")
    {
        var path = Environment.GetEnvironmentVariable("MSTEST_EVIDENCE_JOURNAL")
            ?? throw new InvalidOperationException("The evidence verifier must supply its owned journal path.");
        // Keep journal serialization source-generated in the published Native AOT consumer.
        var line = JsonSerializer.Serialize([ action, id, detail,
            Environment.ProcessId.ToString(CultureInfo.InvariantCulture) ], EvidenceJson.Default.StringArray);
        lock (Gate) File.AppendAllText(path, line + "\n");
    }
}

public static class ValueAssertions
{
    public static void HasExactInt64(this Assert _, object? value, long expected, string message = "")
    {
        var actual = Assert.IsInstanceOfType<long>(value, message + " Int64 wire type required.");
        Assert.AreEqual(expected, actual, message + " Int64 value changed.");
    }
}

[JsonSerializable(typeof(string[]))]
internal partial class EvidenceJson : JsonSerializerContext;
