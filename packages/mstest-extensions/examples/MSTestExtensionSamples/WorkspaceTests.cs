namespace MSTestExtensionSamples;

[TestClass]
public sealed class WorkspaceTests(TestContext context)
{
    private const string WorkspacePrefix = "mstest-extensions-";
    private const string FileName = "value.txt";
    private const string InitialValue = "fresh";
    private const string FirstRowValue = "alpha";
    private const string SecondRowValue = "beta";
    private string? _directory;
    private int _initializations;

    [TestInitialize]
    public async Task Initialize()
    {
        Assert.AreEqual(1, ++_initializations, "Each data row must have its own test instance.");
        _directory = Directory.CreateTempSubdirectory(WorkspacePrefix).FullName;
        try
        {
            await File.WriteAllTextAsync(Path.Combine(_directory, FileName), InitialValue, context.CancellationToken);
        }
        catch
        {
            Directory.Delete(_directory, recursive: true);
            _directory = null;
            throw;
        }
    }

    [TestCleanup]
    public void Cleanup()
    {
        if (_directory is not null)
        {
            Directory.Delete(_directory, recursive: true);
            Assert.IsFalse(Directory.Exists(_directory));
        }
    }

    [TestMethod]
    [DataRow(FirstRowValue)]
    [DataRow(SecondRowValue)]
    public async Task Each_row_receives_an_isolated_workspace(string value)
    {
        var file = Path.Combine(_directory!, FileName);
        Assert.AreEqual(InitialValue, await File.ReadAllTextAsync(file, context.CancellationToken));
        await File.WriteAllTextAsync(file, value, context.CancellationToken);
        Assert.AreEqual(value, await File.ReadAllTextAsync(file, context.CancellationToken));
    }
}
