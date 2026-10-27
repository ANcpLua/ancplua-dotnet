using System;
using System.Collections.Concurrent;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Nami.FixtureExamples.Fixtures;

public sealed class InputFixture : IFixture<InputFixture>
{
    internal static ConcurrentBag<string> CreatedPaths { get; } = new();
    private readonly string _directory;

    private InputFixture(string directory)
    {
        _directory = directory;
        Path = System.IO.Path.Combine(directory, "input.txt");
    }

    public string Path { get; }

    public static async Task<InputFixture> CreateAsync(CancellationToken cancellationToken)
    {
        var directory = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "fixture-example-" + Guid.NewGuid().ToString("N"));
        var fixture = new InputFixture(directory);
        try
        {
            Directory.CreateDirectory(directory);
            await File.WriteAllTextAsync(fixture.Path, "Beispiel", cancellationToken).ConfigureAwait(false);
            CreatedPaths.Add(fixture.Path);
            return fixture;
        }
        catch
        {
            await fixture.DisposeAsync().ConfigureAwait(false);
            throw;
        }
    }

    public ValueTask DisposeAsync()
    {
        if (Directory.Exists(_directory)) Directory.Delete(_directory, recursive: true);
        return ValueTask.CompletedTask;
    }
}
