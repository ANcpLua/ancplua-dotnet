using System.Collections.Immutable;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace AssertionExamples;

// Managed-host examples. Tests intentionally catch assertion failures to prove
// the boundary between contracts; application tests should assert their result directly.
[TestClass]
public sealed class EqualityExamples
{
    [TestMethod]
    public void SequenceOrderAndDuplicateCountsAreIndependent()
    {
        int[] expected = [1, 1, 2];
        int[] reordered = [2, 1, 1];
        int[] wrongMultiplicity = [1, 2, 2];

        Assert.AreSequenceEqual(expected, reordered, SequenceOrder.InAnyOrder);
        Assert.ThrowsExactly<AssertFailedException>(
            () => Assert.AreSequenceEqual(expected, reordered));
        Assert.ThrowsExactly<AssertFailedException>(
            () => Assert.AreSequenceEqual(expected, wrongMultiplicity, SequenceOrder.InAnyOrder));
    }

    [TestMethod]
    public void CustomElementComparerChangesTheSequenceContract()
    {
        string[] expected = ["alpha", "beta"];
        string[] actual = ["ALPHA", "BETA"];

        Assert.AreSequenceEqual(expected, actual, StringComparer.OrdinalIgnoreCase);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.AreSequenceEqual(expected, actual));
    }

    [TestMethod]
    public void ImmutableArrayValueEqualityIsNotElementEquality()
    {
        ImmutableArray<int> expected = ImmutableArray.Create(1, 2);
        ImmutableArray<int> actual = ImmutableArray.Create(1, 2);

        Assert.IsFalse(expected.Equals(actual));
        Assert.IsFalse(expected == actual);
        Assert.AreSequenceEqual(expected, actual);
    }

    [TestMethod]
    public void PreservingAssigneeValueDoesNotRequireTheSameInstance()
    {
        var expected = new Assignee("thread-1");
        var reconstructed = new Assignee("thread-1");

        // A value-preservation contract allows reconstruction of an equal value.
        Assert.AreEqual(expected, reconstructed);
        Assert.AreNotSame(expected, reconstructed);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.AreSame(expected, reconstructed));
    }

    [TestMethod]
    public void UnionPayloadTypeIsDifferentFromTheBoxedWrapperType()
    {
        OperationResult result = new OperationFailure("invalid input");

        var failure = Assert.IsInstanceOfType<OperationFailure>(result.Value);
        Assert.AreEqual("invalid input", failure.Reason);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.IsInstanceOfType<OperationFailure>(result));
    }

    [TestMethod]
    public void CardinalityAssertionsDoNotAssertElementValues()
    {
        int[] empty = [];
        int[] values = [10, 20];
        Assert.IsEmpty(empty);
        Assert.IsNotEmpty(values);
        Assert.HasCount(2, values);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.AreSequenceEqual(new[] { 10, 99 }, values));
    }

    [TestMethod]
    public void ContainsSingleReturnsTheOnlyItem()
    {
        var expected = new Item("one", true);
        Item[] items = [expected];
        Item actual = Assert.ContainsSingle(items);
        Assert.AreSame(expected, actual);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.ContainsSingle(Array.Empty<Item>()));
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.ContainsSingle(new[] { expected, expected }));
    }

    [TestMethod]
    public void ContainsSinglePredicateCountsMatchesNotTheWholeCollection()
    {
        Item[] items = [new("done", false), new("pending", true), new("other", false)];
        Item pending = Assert.ContainsSingle(item => item.Pending, items);
        Assert.AreEqual("pending", pending.Id);
        Assert.HasCount(3, items);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.ContainsSingle(item => item.Pending,
            new[] { new Item("one", true), new Item("two", true) }));
    }

    [TestMethod]
    public void DeepComparisonChecksValuesAndSequenceOrder()
    {
        var expected = new Graph { Name = "order", Values = [1, 2] };
        var same = new Graph { Name = "order", Values = [1, 2] };
        var reordered = new Graph { Name = "order", Values = [2, 1] };
        Assert.AreEquivalent(expected, same, strict: true);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.AreEquivalent(expected, reordered));
    }

    [TestMethod]
    public void StrictComparisonRejectsExtraMembersButDoesNotRequireTheSameType()
    {
        object expected = new Projection { Id = 7 };
        object extra = new Expanded { Id = 7, Note = "additional" };
        object sameShape = new OtherProjection { Id = 7 };

        Assert.AreEquivalent(expected, extra);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.AreEquivalent(expected, extra, strict: true));
        Assert.AreEquivalent(expected, sameShape, strict: true);
    }

    [TestMethod]
    public void StrictDictionaryComparisonRejectsExtraKeys()
    {
        var expected = new Dictionary<string, int> { ["id"] = 7 };
        var actual = new Dictionary<string, int> { ["id"] = 7, ["revision"] = 2 };
        Assert.AreEquivalent(expected, actual);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.AreEquivalent(expected, actual, strict: true));
    }

    [TestMethod]
    public void StaticEquatableTypeCanStopEvenStrictDeepComparison()
    {
        var expected = new Entity(7, "before");
        var actual = new Entity(7, "after");
        Assert.AreEquivalent(expected, actual, strict: true); // Entity equality is deliberately ID-only.
        Assert.ThrowsExactly<AssertFailedException>(
            () => Assert.AreEquivalent<object>(expected, actual, strict: true));
    }

    [TestMethod]
    public void RecordEqualityCanStopTraversalBeforeCollectionMembers()
    {
        var expected = new Snapshot([1, 2]);
        var actual = new Snapshot([1, 2]);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.AreEquivalent(expected, actual, strict: true));
        Assert.AreSequenceEqual(expected.Values, actual.Values);
    }

    [TestMethod]
    public void OperatorEqualityIsNotAutomaticallyEqualsEquality()
    {
        var expected = new OperatorValue(7, "before");
        var actual = new OperatorValue(7, "after");
        Assert.IsTrue(expected == actual); // This test explicitly specifies the overloaded operator.
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.AreEqual(expected, actual));
    }

    [TestMethod]
    public void TypeAssertionReturnsTheProvenInstance()
    {
        var expected = new Graph { Name = "typed", Values = [7] };
        object actual = expected;
        Graph typed = Assert.IsInstanceOfType<Graph>(actual);
        Assert.AreSame(expected, typed);
        Assert.AreEqual("typed", typed.Name);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.IsInstanceOfType<string>(actual));
    }

    [TestMethod]
    public void StringAssertionsPreserveTheChosenComparison()
    {
        const string actual = "Agent-READY-v3";
        Assert.StartsWith("agent", actual, StringComparison.OrdinalIgnoreCase);
        Assert.EndsWith("V3", actual, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("ready", actual, StringComparison.OrdinalIgnoreCase);
        Assert.ThrowsExactly<AssertFailedException>(
            () => Assert.Contains("ready", actual, StringComparison.Ordinal));
    }

    [TestMethod]
    public void NumericAssertionsKeepExpectedBoundsFirst()
    {
        const int actual = 42;
        Assert.IsGreaterThan(41, actual);
        Assert.IsInRange(40, 50, actual);
        Assert.IsPositive(actual);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.IsInRange(40, 50, 51));
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.IsPositive(0));
    }

    [TestMethod]
    public void ExceptionAssertionsDistinguishExactAndDerivedTypes()
    {
        Action operation = () => throw new ArgumentNullException("value");
        var error = Assert.ThrowsExactly<ArgumentNullException>(operation);
        Assert.AreEqual("value", error.ParamName);
        Assert.Throws<ArgumentException>(operation);
        Assert.ThrowsExactly<AssertFailedException>(() => Assert.ThrowsExactly<ArgumentException>(operation));
    }

    private sealed record Item(string Id, bool Pending);
    private sealed record Assignee(string ThreadId);
    private sealed record OperationSuccess(int Value);
    private sealed record OperationFailure(string Reason);
    private readonly union OperationResult(OperationSuccess, OperationFailure);
    private sealed record Snapshot(int[] Values);
    private sealed class Graph
    {
        public string Name { get; init; } = "";
        public int[] Values { get; init; } = [];
    }
    private sealed class Projection { public int Id { get; init; } }
    private sealed class OtherProjection { public int Id { get; init; } }
    private sealed class Expanded
    {
        public int Id { get; init; }
        public string Note { get; init; } = "";
    }
    private sealed class Entity(int id, string label) : IEquatable<Entity>
    {
        public int Id { get; } = id;
        public string Label { get; } = label;
        public bool Equals(Entity? other) => other is not null && Id == other.Id;
        public override bool Equals(object? other) => other is Entity value && Equals(value);
        public override int GetHashCode() => Id;
    }
    private sealed class OperatorValue(int id, string label)
    {
        public int Id { get; } = id;
        public string Label { get; } = label;
        public static bool operator ==(OperatorValue? left, OperatorValue? right) =>
            ReferenceEquals(left, right) || left is not null && right is not null && left.Id == right.Id;
        public static bool operator !=(OperatorValue? left, OperatorValue? right) => !(left == right);
        public override bool Equals(object? other) => other is OperatorValue value && Id == value.Id && Label == value.Label;
        public override int GetHashCode() => HashCode.Combine(Id, Label);
    }
}
