#nullable enable
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

// System.Text.Json and C# 15 unions. scripts/verify.py checks these lines and the build diagnostics:
// SYSLIB1227 (ambiguous cases) and SYSLIB1228 (unsupported union shape) are warnings by default and
// fail the build when promoted. RESOLVED_ONLY drops the two unions that report them and builds with
// both promoted; SilencedShape stays ambiguous there because its context declares a generation-time
// classifier. POLYMORPHIC_UNION expects CS0592.
const string BothShapes = """{"Radius":1,"Side":2}""";

Console.WriteLine("--- write: the active case value, no wrapper or discriminator ---");
Console.WriteLine("write int => " + JsonSerializer.Serialize<Reading>(42, ProbeJson.Default.Reading));
Console.WriteLine("write string => " + JsonSerializer.Serialize<Reading>("x", ProbeJson.Default.Reading));
Console.WriteLine("write object => " + JsonSerializer.Serialize<StructuralShape>(new Circle(1), ProbeJson.Default.StructuralShape));
Console.WriteLine("write default => " + JsonSerializer.Serialize(default(Reading), ProbeJson.Default.Reading));

Console.WriteLine("--- read: the default classifier uses the JSON token kind ---");
Console.WriteLine("read 42 => " + Read("42", ProbeJson.Default.Reading));
Console.WriteLine("read \"x\" => " + Read("\"x\"", ProbeJson.Default.Reading));
Console.WriteLine("read null => " + Read("null", ProbeJson.Default.Reading));
Console.WriteLine("read true => " + Read("true", ProbeJson.Default.Reading));
#if !RESOLVED_ONLY
Console.WriteLine("ambiguous object cases => " + Read("""{"Radius":1}""", ProbeJson.Default.AmbiguousShape));
Console.WriteLine("member-provider union => " + Try(() => ProbeJson.Default.ProviderUnion.Kind.ToString()));
Console.WriteLine("member-provider union, reflection => " + Try(() =>
{
    var options = new JsonSerializerOptions { TypeInfoResolver = new DefaultJsonTypeInfoResolver() };
    ProviderUnion circle = new Circle(1);
    return $"kind {options.GetTypeInfo(typeof(ProviderUnion)).Kind}, serialize " + Try(() => JsonSerializer.Serialize(circle, options));
}));
#endif

Console.WriteLine("--- JsonUnionTypeStructuralClassifier: root property names only ---");
Console.WriteLine("structural Radius => " + Read("""{"Radius":1}""", ProbeJson.Default.StructuralShape));
Console.WriteLine("structural Side => " + Read("""{"Side":2}""", ProbeJson.Default.StructuralShape));
Console.WriteLine("structural {} => " + Read("{}", ProbeJson.Default.StructuralShape));
Console.WriteLine("structural tag square with circle fields => " + Read("""{"Kind":"square","Radius":1}""", ProbeJson.Default.TaggedShapes));
Console.WriteLine("structural never-unique case => " + Try(() => ProbeJson.Default.OverlappingShapes.TypeClassifier is null ? "no classifier" : "classifier built"));

Console.WriteLine("--- classifier precedence ---");
var reflectionOptions = new JsonSerializerOptions { TypeInfoResolver = new DefaultJsonTypeInfoResolver() };
reflectionOptions.TypeClassifiers.Add(new PickSquare<PickedByAttribute>());
reflectionOptions.TypeClassifiers.Add(new PickSquare<PickedByOptions>());
Console.WriteLine("attribute over options => " + ReadWith<PickedByAttribute>(BothShapes, reflectionOptions));
Console.WriteLine("options only => " + ReadWith<PickedByOptions>(BothShapes, reflectionOptions));
var contractOptions = new JsonSerializerOptions
{
    TypeInfoResolver = ProbeJson.Default.WithAddedModifier(static info =>
    {
        if (info.Type == typeof(PickedByAttribute))
            info.TypeClassifier = static (ref Utf8JsonReader reader) => typeof(Square);
    }),
};
Console.WriteLine("contract over attribute => " + ReadWith<PickedByAttribute>(BothShapes, contractOptions));
Console.WriteLine("generation-time options => " + Read(BothShapes, GenerationTimeJson.Default.PickedByOptions));
var explicitOptions = new JsonSerializerOptions();
explicitOptions.TypeClassifiers.Add(new PickSquare<PickedByOptions>());
Console.WriteLine("explicit context options => " + Read(BothShapes, new GenerationTimeJson(explicitOptions).PickedByOptions));
Console.WriteLine("silenced ambiguous union => " + Read("""{"Radius":1}""", GenerationTimeJson.Default.SilencedShape));

Console.WriteLine("--- JSON null ---");
CountingClassifier.Calls = 0;
Console.WriteLine($"null with classifier => {Read("null", ProbeJson.Default.CountedShape)}, classifier calls {CountingClassifier.Calls}");
var constructed = new List<string>();
var logging = new JsonSerializerOptions
{
    TypeInfoResolver = ProbeJson.Default.WithAddedModifier(info =>
    {
        if (info.Kind == JsonTypeInfoKind.Union && info.UnionConstructor is { } create)
            info.UnionConstructor = (caseType, value) => { constructed.Add(caseType.Name); return create(caseType, value); };
    }),
};
Console.WriteLine("nullable case flags => " + string.Join(",", ProbeJson.Default.NullableCase.UnionCases!.Select(static c => c.CaseType.Name + (c.IsNullable ? "?" : ""))));
Console.WriteLine($"null with nullable case => {ReadWith<NullableCase>("null", logging)} via [{string.Join(",", constructed)}]");
constructed.Clear();
Console.WriteLine($"null without nullable case => {ReadWith<CountedShape>("null", logging)} via [{string.Join(",", constructed)}]");
Console.WriteLine("required union property with null => " + Try(() =>
    Describe(JsonSerializer.Deserialize("""{"Shape":null}""", ProbeJson.Default.RequiredShape)!.Shape)));

Console.WriteLine("--- a union with [JsonConverter] keeps its converter ---");
Console.WriteLine($"converter contract kind => {ProbeJson.Default.ConverterShape.Kind}");
Console.WriteLine("converter write => " + JsonSerializer.Serialize<ConverterShape>(new Circle(1), ProbeJson.Default.ConverterShape));
Console.WriteLine("converter read => " + Read("""{"tag":"square"}""", ProbeJson.Default.ConverterShape));

static string Try(Func<string> action)
{
    try { return action(); }
    catch (Exception error) { return error.GetType().Name + ": " + error.Message.Split(". ")[0]; }
}

static string Describe(IUnion union) => union.Value is null ? "empty" : union.Value.GetType().Name;
static string Read<T>(string json, JsonTypeInfo<T> info) where T : IUnion => Try(() => Describe(JsonSerializer.Deserialize(json, info)!));
static string ReadWith<T>(string json, JsonSerializerOptions options) where T : IUnion => Try(() => Describe(JsonSerializer.Deserialize<T>(json, options)!));

public record Circle(double Radius);
public record Square(double Side);
public record TaggedCircle(string Kind, double Radius);
public record TaggedSquare(string Kind, double Side);
public record Named(string Name);
public record NamedWithExtra(string Name, int Extra);

public union Reading(int, string);
#if !RESOLVED_ONLY
public union AmbiguousShape(Circle, Square);

[Union]
public readonly struct ProviderUnion : ProviderUnion.IUnionMembers
{
    private readonly object? _value;
    private ProviderUnion(object? value) => _value = value;
    public interface IUnionMembers
    {
        static ProviderUnion Create(Circle value) => new(value);
        static ProviderUnion Create(Square value) => new(value);
        object? Value { get; }
    }
    object? IUnionMembers.Value => _value;
}
#endif
#if POLYMORPHIC_UNION
[JsonPolymorphic]
public union PolymorphicShape(Circle, Square);
#endif

[JsonUnion(TypeClassifier = typeof(JsonUnionTypeStructuralClassifier))]
public union StructuralShape(Circle, Square);
[JsonUnion(TypeClassifier = typeof(JsonUnionTypeStructuralClassifier))]
public union TaggedShapes(TaggedCircle, TaggedSquare);
[JsonUnion(TypeClassifier = typeof(JsonUnionTypeStructuralClassifier))]
public union OverlappingShapes(Named, NamedWithExtra);

[JsonUnion(TypeClassifier = typeof(PickCircle<PickedByAttribute>))]
public union PickedByAttribute(Circle, Square);
public union PickedByOptions(Circle, Square);
public union SilencedShape(Circle, Square);

[JsonUnion(TypeClassifier = typeof(CountingClassifier))]
public union CountedShape(Circle, Square);
[JsonUnion(TypeClassifier = typeof(PickCircle<NullableCase>))]
public union NullableCase(Circle, Square?);

[JsonConverter(typeof(ShapeTagConverter))]
public union ConverterShape(Circle, Square);

public sealed class RequiredShape
{
    public required StructuralShape Shape { get; init; }
}

public sealed class PickCircle<T> : JsonTypeClassifierFactory<T>
{
    public override JsonTypeClassifier CreateJsonClassifier(JsonTypeClassifierContext context, JsonSerializerOptions options) =>
        static (ref Utf8JsonReader reader) => typeof(Circle);
}

public sealed class PickSquare<T> : JsonTypeClassifierFactory<T>
{
    public override JsonTypeClassifier CreateJsonClassifier(JsonTypeClassifierContext context, JsonSerializerOptions options) =>
        static (ref Utf8JsonReader reader) => typeof(Square);
}

public sealed class CountingClassifier : JsonTypeClassifierFactory<CountedShape>
{
    public static int Calls;

    public override JsonTypeClassifier CreateJsonClassifier(JsonTypeClassifierContext context, JsonSerializerOptions options) =>
        static (ref Utf8JsonReader reader) => { Calls++; return typeof(Circle); };
}

public sealed class ShapeTagConverter : JsonConverter<ConverterShape>
{
    public override ConverterShape Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        using var document = JsonDocument.ParseValue(ref reader);
        return document.RootElement.GetProperty("tag").GetString() == "square" ? new Square(0) : new Circle(0);
    }

    public override void Write(Utf8JsonWriter writer, ConverterShape value, JsonSerializerOptions options)
    {
        writer.WriteStartObject();
        writer.WriteString("tag", value.Value is Square ? "square" : "circle");
        writer.WriteEndObject();
    }
}

[JsonSerializable(typeof(Reading))]
#if !RESOLVED_ONLY
[JsonSerializable(typeof(AmbiguousShape))]
[JsonSerializable(typeof(ProviderUnion))]
#endif
[JsonSerializable(typeof(StructuralShape))]
[JsonSerializable(typeof(TaggedShapes))]
[JsonSerializable(typeof(OverlappingShapes))]
[JsonSerializable(typeof(PickedByAttribute))]
[JsonSerializable(typeof(CountedShape))]
[JsonSerializable(typeof(NullableCase))]
[JsonSerializable(typeof(ConverterShape))]
[JsonSerializable(typeof(RequiredShape))]
internal partial class ProbeJson : JsonSerializerContext;

// Any generation-time classifier silences SYSLIB1227 for every union in the context, including
// SilencedShape, which no listed factory can classify.
[JsonSourceGenerationOptions(TypeClassifiers = [typeof(PickCircle<PickedByOptions>)])]
[JsonSerializable(typeof(PickedByOptions))]
[JsonSerializable(typeof(SilencedShape))]
internal partial class GenerationTimeJson : JsonSerializerContext;
