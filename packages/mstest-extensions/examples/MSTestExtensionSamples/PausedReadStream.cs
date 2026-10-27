namespace MSTestExtensionSamples;

public sealed class PausedReadStream(byte[] bytes, int chunkSize) : Stream
{
    private int _position;
    private bool _disposed;
    private readonly TaskCompletionSource _paused = new(TaskCreationOptions.RunContinuationsAsynchronously);
    private readonly TaskCompletionSource _resumed = new(TaskCreationOptions.RunContinuationsAsynchronously);

    public Task Paused => _paused.Task;
    public bool Disposed => _disposed;
    public void Resume() => _resumed.TrySetResult();
    public override bool CanRead => !_disposed;
    public override bool CanSeek => false;
    public override bool CanWrite => false;
    public override long Length => throw new NotSupportedException();
    public override long Position { get => throw new NotSupportedException(); set => throw new NotSupportedException(); }

    public override async ValueTask<int> ReadAsync(Memory<byte> buffer, CancellationToken cancellationToken = default)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        _paused.TrySetResult();
        await _resumed.Task.WaitAsync(cancellationToken);
        ObjectDisposedException.ThrowIf(_disposed, this);
        var count = Math.Min(Math.Min(buffer.Length, chunkSize), bytes.Length - _position);
        bytes.AsMemory(_position, count).CopyTo(buffer);
        _position += count;
        return count;
    }

    public override Task<int> ReadAsync(byte[] buffer, int offset, int count, CancellationToken cancellationToken)
        => ReadAsync(buffer.AsMemory(offset, count), cancellationToken).AsTask();

    protected override void Dispose(bool disposing)
    {
        _disposed = true;
        Resume();
        base.Dispose(disposing);
    }

    public override int Read(byte[] buffer, int offset, int count) => throw new NotSupportedException();
    public override void Flush() => throw new NotSupportedException();
    public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
    public override void SetLength(long value) => throw new NotSupportedException();
    public override void Write(byte[] buffer, int offset, int count) => throw new NotSupportedException();
}
