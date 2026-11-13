# A GIF decoder: an exercise in Go interfaces

Some file formats look like they need a complicated parser. Once you see the right abstraction, the code gets much shorter. The image data section of a GIF file is a good example, and it shows why Go's small interfaces are so useful.

## The problem: compressed data, chopped into pieces

A GIF stores its pixels as palette indices compressed with LZW. The encoder doesn't write that compressed stream as one continuous run of bytes. It splits the stream into **sub-blocks**. Each sub-block starts with a single length byte (1 to 255), followed by that many bytes of data. A zero-length block marks the end:

```
[min code size] [n₁] [n₁ bytes...] [n₂] [n₂ bytes...] ... [0]
```

These sub-block boundaries mean nothing to the compression. An LZW code can start in one sub-block and end in the next. That's the awkward part. The decompressor needs a continuous bit stream, but the file gives us fragments with length headers mixed in.

The obvious solution is to write an LZW decoder that knows about sub-blocks. It would check, while unpacking bits, whether the current block has run out and whether it needs to read another length byte. That works, but it mixes two unrelated jobs. The result is hard to test, and the decoder can't be reused for anything except GIF.

## The Go approach: make the fragments look like a stream

Go's standard library already has an LZW decompressor in `compress/lzw`. Its constructor has this signature:

```go
func NewReader(r io.Reader, order Order, litWidth int) io.ReadCloser
```

It takes an `io.Reader`, which is about as simple as an interface can be:

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}
```

The `lzw` package doesn't care where the bytes come from. So instead of teaching LZW about sub-blocks, we can write a small type that removes the sub-block framing and presents what's left as an ordinary stream:

```go
type blockReader struct {
    r    *bufio.Reader
    n    int  // bytes remaining in the current sub-block
    done bool // saw the zero-length terminator
}

func (b *blockReader) Read(p []byte) (int, error) {
    if b.done {
        return 0, io.EOF
    }
    if len(p) == 0 {
        return 0, nil
    }
    if b.n == 0 {
        size, err := b.r.ReadByte()
        if err != nil {
            return 0, err
        }
        if size == 0 {
            b.done = true
            return 0, io.EOF
        }
        b.n = int(size)
    }
    if len(p) > b.n {
        p = p[:b.n]
    }
    n, err := b.r.Read(p)
    b.n -= n
    if err == io.EOF {
        err = io.ErrUnexpectedEOF
    }
    return n, err
}
```

`blockReader` never declares that it implements `io.Reader`. It has a `Read` method with the right signature, and in Go that is enough. The `lzw` package was written years before this type existed and without any knowledge of GIF, yet it can use `blockReader` directly.

## Putting the pipeline together

With the deframing handled separately, decoding the image data is mostly a matter of connecting existing pieces:

```go
func readImageData(r *bufio.Reader, width, height int) ([]byte, error) {
    litWidth, err := r.ReadByte()
    if err != nil {
        return nil, err
    }
    if litWidth < 2 || litWidth > 8 {
        return nil, fmt.Errorf("gif: invalid LZW code size %d", litWidth)
    }

    lz := lzw.NewReader(&blockReader{r: r}, lzw.LSB, int(litWidth))
    defer lz.Close()

    pixels := make([]byte, width*height)
    if _, err := io.ReadFull(lz, pixels); err != nil {
        return nil, fmt.Errorf("gif: reading image data: %w", err)
    }
    return pixels, nil
}
```

Data flows through four layers:

1. **`bufio.Reader`** wraps the file, so that reading one byte at a time is cheap.
2. **`blockReader`** removes the length prefixes and stops at the terminator.
3. **`lzw.Reader`** decompresses the stream it receives.
4. **`io.ReadFull`** keeps reading until the pixel buffer is full.

Each layer knows only that the layer below it has a `Read` method. None of them knows the whole pipeline.

## Why this pays off

**Testing gets simpler.** You can test `blockReader` by itself with a `bytes.Reader` and hand-written byte slices. That's a good way to check edge cases such as a 255-byte block, an empty image, or a file truncated in the middle of a block. These tests don't involve any compression code.

**The boundaries hold up.** Because `blockReader` returns `io.EOF` at the terminator, the decompressor can't read past the end of the image data into whatever comes next in the file. The `lzw` docs warn that if the reader you pass doesn't also implement `io.ByteReader`, the decompressor may read more data than it needs. Here that extra reading still stops at the terminator. For production use, you'd probably add a `ReadByte` method to `blockReader` anyway, both for speed and to keep reads tightly controlled.

**There are loose ends.** A real decoder also has to deal with encoders that leave extra data after the last pixel. After `ReadFull` returns, you drain any remaining sub-blocks so that the next parsing step starts at the right position in the file. That's a few more lines of code, and it fits easily in this design.

## The broader lesson

Interfaces like `io.Reader` work well because they ask for so little. A single method is easy to implement and easy to wrap. It's also general enough that code written by different people, at different times, for different reasons, can be combined in ways none of them planned.

When a format seems to force you to merge two concerns, ask whether a short adapter could turn one of them into a plain stream. In Go, that adapter often takes about twenty lines.
