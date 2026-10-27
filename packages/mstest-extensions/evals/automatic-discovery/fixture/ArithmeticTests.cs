[assembly: Parallelize(Scope = ExecutionScope.MethodLevel)]

namespace Diagnostics.Tests;

[TestClass]
public sealed class ArithmeticTests
{
    [TestMethod]
    [DataRow(2, 3, 5)]
    [DataRow(-1, 1, 0)]
    public void Sum(int left, int right, int expected)
    {
        Assert.AreEqual(expected, left + right);
    }
}
