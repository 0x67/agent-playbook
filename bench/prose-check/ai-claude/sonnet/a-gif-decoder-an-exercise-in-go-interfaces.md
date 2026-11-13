# A GIF decoder: an exercise in Go interfaces

Go's interfaces are easy to describe and surprisingly hard to appreciate until you've used them on a real problem. Recently we needed to decode GIF images in a service that processes user uploads, and the exercise turned into a tidy demonstration of why small interfaces, composition, and implicit satisfaction work so well together. This post walks through the design ideas that make Go's `image/gif` package a good case study, and what we took from it.

## The problem

A GIF file is a stream of blocks: a header, a logical screen descriptor, an optional global color table, then a sequence of extensions and image frames, terminated by a trailer byte. Each frame may have its own local palette, its own delay, and a disposal method that says what to do with the canvas before drawing the next frame.

A decoder has to read bytes, interpret that structure, and produce something the rest of your program can use. The interesting question is: what should "something" and "bytes" look like in code?

## Input: accept the smallest interface that works

The decoder's entry point looks like this:

```go
func DecodeAll(r io.Reader) (*GIF, error)
```

It takes an `io.Reader`, not a file path, not a `[]byte`, not an `*os.File`. That one choice means the same function decodes from a file, an HTTP request body, a network socket, a `bytes.Buffer` in a unit test, or a `gzip.Reader` wrapping any of the above.

Internally, GIF parsing wants to read single bytes and fixed-size chunks efficiently. Rather than demand a richer type from the caller, the package defines a tiny private interface:

```go
type reader interface {
    io.Reader
    io.ByteReader
}
```

If the caller's reader already satisfies it (a `*bufio.Reader` does), it is used directly. If not, the decoder wraps it:

```go
if rr, ok := r.(reader); ok {
    d.r = rr
} else {
    d.r = bufio.NewReader(r)
}
```

This is a pattern worth stealing: **accept the minimal interface publicly, upgrade privately via a type assertion**. Callers get a simple contract; the implementation still gets the capabilities it needs.

## Output: image.Image and friends

On the output side, each frame is an `*image.Paletted`, which implements `image.Image`:

```go
type Image interface {
    ColorModel() color.Model
    Bounds() Rectangle
    At(x, y int) color.Color
}
```

Three methods. Anything that implements them can be passed to the PNG encoder, a resizing library, or a thumbnailer, none of which know or care that the pixels came from a GIF. The GIF package never imports the PNG package, and vice versa. They meet only at the interface.

That's the payoff of implicit satisfaction: `image/gif` doesn't declare "I implement `image.Image`." It just has the right methods. Decoupling falls out for free.

The same applies to colors. A GIF palette is a `color.Palette`, a slice of `color.Color` values. Because `color.Color` is also a small interface (`RGBA() (r, g, b, a uint32)`), a palette entry can be any color type, and conversion between models goes through one common currency.

## Composition for the compressed stream

GIF pixel data is LZW-compressed and chopped into sub-blocks of up to 255 bytes, each prefixed by a length byte. The LZW decompressor from `compress/lzw` wants an `io.Reader` of compressed bytes. But the raw stream isn't that; it's interleaved with length prefixes.

The solution is a small adapter type, a `blockReader`, that implements `io.Reader` by stripping the framing:

```go
type blockReader struct {
    d    *decoder
    i, j uint8
    err  error
    buf  [256]byte
}
```

Wire it up and the pipeline reads naturally:

```go
lzwr := lzw.NewReader(&blockReader{d: d}, lzw.LSB, int(litWidth))
io.ReadFull(lzwr, m.Pix)
```

Three layers, each unaware of the others: block framing, LZW decompression, and a destination pixel buffer. Every seam is `io.Reader`. Testing each layer in isolation is trivial because you can feed any of them any reader.

## Testing benefits

Because everything is an interface at the boundary, tests need no fixtures on disk. We feed the decoder a `strings.NewReader` of hand-built bytes, or an `iotest.OneByteReader` to confirm it handles short reads, or an `iotest.TimeoutReader` to confirm errors propagate. The standard library's `testing/iotest` package exists precisely because `io.Reader` is so universal.

## What we took away

1. **Accept interfaces, return concrete types.** `DecodeAll` takes an `io.Reader` and returns a `*GIF`, so callers get full access to the data without type assertions.
2. **Keep interfaces small.** One to three methods is the sweet spot. Small interfaces are easy to satisfy and easy to fake.
3. **Define interfaces where they're consumed.** The private `reader` interface lives in the decoder, not in some shared package.
4. **Adapters are cheap.** When a boundary doesn't quite match, write a small type that does. In Go this is often ten lines.

None of this is exotic. That's the point. A GIF decoder is a few hundred lines of fairly dull binary parsing, and the interfaces are what keep it composable, testable, and independent of everything around it. If you want to see Go interfaces earning their keep, read the source of `image/gif` alongside `image/png`; the contrast in what they *don't* know about each other is the lesson.
