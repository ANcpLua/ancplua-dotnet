using System.IO;
using System.Threading.Tasks;
using Nami.FixtureExamples.Fixtures;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Nami.FixtureExamples;

[UsesFixture(FixtureScope.Class)]
public sealed class InputTests : FixtureTests<InputFixture>
{
    [TestMethod]
    public async Task DateiEnthaeltErwartetenText()
    {
        Assert.AreEqual("Beispiel", await File.ReadAllTextAsync(Fixture.Path, CancellationToken));
    }

    [TestMethod]
    public void DateiIstNichtLeer()
    {
        Assert.IsGreaterThan(0L, new FileInfo(Fixture.Path).Length);
    }
}
