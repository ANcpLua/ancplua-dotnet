using System;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

internal static class JsonExamples
{
    internal static void Verify()
    {
        var info = PaymentJsonContext.Default.Payment;
        Payment card = new CardPayment { Last4 = "4242" };
        Payment transfer = new TransferPayment { Iban = "AT611904300234573201" };

        Require(JsonSerializer.Serialize(card, info) == """{"kind":"card","last4":"4242"}""", "Card is written as its case value");
        Require(JsonSerializer.Serialize(transfer, info) == """{"kind":"transfer","iban":"AT611904300234573201"}""",
            "Transfer is written as its case value");
        Require(JsonSerializer.Serialize(default(Payment), info) == "null", "Default union is written as null");
        Console.WriteLine("json-tagged-union-writes-case-values-verified");

        Require(Read("""{"kind":"card","last4":"4242"}""") is CardPayment { Last4: "4242" }, "Tag first");
        Require(Read("""{"last4":"4242","kind":"card"}""") is CardPayment { Last4: "4242" }, "Tag last");
        Require(Read("""{"\u006bind":"transfer","iban":"X"}""") is TransferPayment { Iban: "X" }, "Escaped tag name");
        Require(Read("null") is null, "JSON null reads as the default union");
        Console.WriteLine("json-tagged-union-reads-by-tag-verified");

        foreach (var json in new[]
        {
            """{"kind":"wallet"}""",                            // unknown tag
            """{"last4":"4242"}""",                             // missing tag
            """{"kind":"card","kind":"card","last4":"1"}""",    // repeated tag
            """{"kind":1,"last4":"1"}""",                       // non-string tag
            """{"kind":"card","iban":"X"}""",                   // tag of one case, fields of another
            """{"kind":"card"}""",                              // required field missing
            """[]""",
            "\"card\"",
        })
        {
            RequireJsonException(json);
        }
        Console.WriteLine("json-tagged-union-rejects-invalid-tags-verified");

        Payment[] payments = [card, transfer, card];
        var bytes = JsonSerializer.SerializeToUtf8Bytes(payments, PaymentJsonContext.Default.PaymentArray);
        var streaming = new PaymentJsonContext(new JsonSerializerOptions
        {
            DefaultBufferSize = 16,
            UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
        });
        using var stream = new MemoryStream(bytes);
        var copy = JsonSerializer.DeserializeAsync(stream, streaming.PaymentArray).AsTask().GetAwaiter().GetResult()
            ?? throw new InvalidOperationException("Streamed array was null.");
        Require(copy.Length == 3 && Equals(copy[0].Value, card.Value) && Equals(copy[1].Value, transfer.Value)
            && Equals(copy[2].Value, card.Value), "Streamed array");
        Require(JsonSerializer.Serialize(copy, PaymentJsonContext.Default.PaymentArray) == Encoding.UTF8.GetString(bytes),
            "Streamed array writes the same bytes");
        Console.WriteLine("json-tagged-union-streaming-round-trip-verified");
    }

    private static object? Read(string json) => JsonSerializer.Deserialize(json, PaymentJsonContext.Default.Payment).Value;

    private static void RequireJsonException(string json)
    {
        try { _ = Read(json); }
        catch (JsonException) { return; }
        throw new InvalidOperationException("Expected JsonException for " + json);
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
