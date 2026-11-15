using System;
using System.Text.Json;
using System.Text.Json.Serialization;

// A wire contract whose objects carry a "kind" tag. System.Text.Json writes the
// active case value as-is: each case declares its tag as a constant, get-only
// property, so the tag is written and ignored on read. Reading needs the
// classifier below, because both cases are JSON objects; without it the source
// generator reports SYSLIB1227 and reading throws JsonException.
public sealed record CardPayment
{
    [JsonPropertyName("kind")]
    public string Kind => "card";

    [JsonPropertyName("last4")]
    public required string Last4 { get; init; }
}

public sealed record TransferPayment
{
    [JsonPropertyName("kind")]
    public string Kind => "transfer";

    [JsonPropertyName("iban")]
    public required string Iban { get; init; }
}

[JsonUnion(TypeClassifier = typeof(PaymentKindClassifier))]
public readonly union Payment(CardPayment, TransferPayment);

// Selects the case from the tag value, never from which other fields happen to
// be present. Returning null makes the serializer throw JsonException, so an
// unknown, missing, repeated or non-string tag is rejected. JSON null never
// reaches the classifier: it becomes default(Payment), which writes as null.
public sealed class PaymentKindClassifier : JsonTypeClassifierFactory<Payment>
{
    public override JsonTypeClassifier CreateJsonClassifier(
        JsonTypeClassifierContext context, JsonSerializerOptions options) => Classify;

    // The serializer reads the selected case from the start of the value after
    // this method returns, so it can read through the whole object.
    private static Type? Classify(ref Utf8JsonReader reader)
    {
        if (reader.TokenType != JsonTokenType.StartObject)
            return null;

        Type? selected = null;
        while (reader.Read() && reader.TokenType == JsonTokenType.PropertyName)
        {
            var isTag = reader.ValueTextEquals("kind"u8);
            if (!reader.Read())
                return null;
            if (!isTag)
            {
                // TrySkip, not Skip: during streaming reads the reader is not
                // a final block, where Skip throws.
                if (!reader.TrySkip())
                    return null;
                continue;
            }

            if (selected is not null || reader.TokenType != JsonTokenType.String)
                return null;
            selected = reader.ValueTextEquals("card"u8) ? typeof(CardPayment)
                : reader.ValueTextEquals("transfer"u8) ? typeof(TransferPayment)
                : null;
            if (selected is null)
                return null;
        }

        return selected;
    }
}

// Disallow rejects a payload that combines one case's tag with another case's
// fields. The source-generated metadata needs no reflection at run time.
[JsonSourceGenerationOptions(UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow)]
[JsonSerializable(typeof(Payment))]
[JsonSerializable(typeof(Payment[]))]
internal partial class PaymentJsonContext : JsonSerializerContext;
