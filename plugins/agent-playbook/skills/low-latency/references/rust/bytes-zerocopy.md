# bytes and zerocopy (Rust)

Loaded via the low-latency SKILL.md routing table. Checked against bytes 1.12.1 and zerocopy 0.8.63 on 2026-11-06. Sources: bytes 1.12.1 crate source (`src/bytes.rs`, `src/bytes_mut.rs`, `src/buf/`), zerocopy 0.8.63 crate source (`src/lib.rs`, `src/ref.rs`, `src/byteorder.rs`, `src/error.rs`), and a measured decode spike over fixed-layout market-data messages (criterion wall clock on Apple M4 Pro, callgrind instruction counts on x86_64).

## When to use which

- Safe borrowed view: the default for fixed-layout messages decoded while the frame is alive. Wrap `&'a [u8; N]` after one length check and read fields with `from_be_bytes` at constant offsets. No dependency, no `unsafe`.
- A measured spike put the safe view at 0.80 ns/msg against 3.14 for an owned struct copy on a 31-byte message, and 8.87 against 22.2 on a 281-byte message. Callgrind agreed: 169 vs 195 and 805 vs 1103 instructions per decode.
- zerocopy derive overlay: same speed as the safe view (0.78 and 8.79 ns/msg; callgrind counted identical instructions on all 8 message kinds). Choose it for named fields, compile-time layout checks, encoding through the same struct (`IntoBytes`), or a header with a trailing slice. Speed is not a reason to choose it.
- `bytes`: owned buffers that outlive one read call or cross threads and tasks. One `BytesMut` accumulator per connection; frames that leave the thread go out as `Bytes`. Decoding still borrows: `View::parse(&frame[..])`.
- Owned copies (`read_from_bytes`, hand-built structs) only for small values that must outlive the buffer. Never `Box` per message: boxed owned decode measured 23.2 ns/msg and 256 allocations per 256-row burst, against 8.80 ns and 0 for the view. A snapshot that must outlive the frame goes into an arena (10.5 ns/msg, 8 allocations per burst).

## Core API

bytes 1.12.1:

- `BytesMut::with_capacity(n)`, `clear()` (keeps capacity), `extend_from_slice`, `spare_capacity_mut() -> &mut [MaybeUninit<u8>]`, unsafe `set_len`, unsafe `BufMut::advance_mut(n)`.
- `reserve(additional)`: inline no-op while spare capacity covers it. `try_reclaim(additional) -> bool` runs the same reclaim logic and never allocates.
- `split_to(at)` returns `[0, at)`; `self` keeps `[at, len)` and the spare capacity. Panics if `at > len`. `split()` is `split_to(len())`.
- `split_off(at)`: `self` keeps `[0, at)` with capacity cut to `at`; the returned half gets `[at, capacity)`. Panics if `at > capacity`.
- `freeze(self) -> Bytes`: never copies the data. On a split handle it is pointer work only; an unsplit buffer with spare capacity allocates a small shared header.
- `Bytes`: `clone`, `slice(range)`, `slice_ref(&[u8])`, `split_to`, `split_off` are O(1). Also `is_unique()`, `try_into_mut() -> Result<BytesMut, Bytes>`, `from_static` (clone is a no-op), `copy_from_slice` (copies). `Bytes` and `BytesMut` are `Send + Sync`.
- `Buf`: `remaining`, `chunk`, `advance`, `get_u16`/`get_u32`/`get_u64` (big-endian, panic when short), `_le` variants, and `try_get_u32` and friends returning `Result<_, TryGetError>`. `copy_to_bytes(len)` is a `split_to` on `Bytes` and `BytesMut` but a copy on `&[u8]`.
- `BufMut`: `put_u8`, `put_u16`/`put_u32`/`put_u64` (big-endian), `put_slice`, `chunk_mut`.

zerocopy 0.8.63 (derives need feature `derive`):

- `FromBytes`: every bit pattern is valid. `IntoBytes`: no padding bytes. `KnownLayout`: layout zerocopy can reason about. `Immutable`: no interior mutability. `Unaligned`: `align_of::<T>() == 1`.
- `T::ref_from_bytes(&[u8]) -> Result<&T, CastError<&[u8], T>>` needs the exact size. `ref_from_prefix` returns `(&T, &[u8])`, `ref_from_suffix` returns `(&[u8], &T)`. Bound: `T: KnownLayout + Immutable`.
- `T::read_from_bytes` and `read_from_prefix` copy `T` out by value (bound `Self: Sized`, error `SizeError`). `mut_from_bytes(&mut [u8])` needs `IntoBytes + KnownLayout`.
- `IntoBytes::as_bytes(&self) -> &[u8]` and `write_to(&self, &mut [u8])`, both with `Self: Immutable`.
- `Ref<B, T>`: `Ref::from_bytes(b) -> Result<Ref<B, T>, CastError<B, T>>`, `Ref::from_prefix(b)` with `Ok((Ref<B, T>, B))`, `Ref::into_ref(r)` (associated fn), `Deref` to `T`. `B` is `&[u8]`, `&mut [u8]`, `cell::Ref<[u8]>` or `cell::RefMut<[u8]>`. There is no impl for `bytes::Bytes`; borrow `&frame[..]`.
- `byteorder`: `U16<O>`, `U32<O>`, `U64<O>`, `I32<O>`, `I64<O>` and more, with `O` as `BigEndian` (aliases `BE`, `NetworkEndian`) or `LittleEndian` (`LE`). Shorthand: `byteorder::big_endian::{U16, U32, U64}`. Methods `.get()`, `.set(n)`, `::new(n)`, const `ZERO`. All align 1 and re-exported at the crate root.
- `CastError` is `ConvertError<AlignmentError, SizeError, Infallible>`. For `T: Unaligned`, `SizeError::from(err)` drops the impossible alignment case.

## Idioms

```rust
// safe view: one length check, then constant-offset reads
pub struct AddOrderView<'a>(&'a [u8; 31]);

impl<'a> AddOrderView<'a> {
    pub fn parse(b: &'a [u8]) -> Option<Self> {
        b.try_into().ok().map(Self)
    }
    #[inline]
    pub fn order_id(&self) -> u64 {
        // const range inside [u8; 31], so the check folds away
        u64::from_be_bytes(self.0[5..13].try_into().unwrap())
    }
}
```

```rust
use zerocopy::byteorder::big_endian::{U32, U64};
use zerocopy::{FromBytes, Immutable, KnownLayout, Unaligned};

#[derive(FromBytes, KnownLayout, Immutable, Unaligned)]
#[repr(C)] // FromBytes compiles without it; the wire layout needs it
pub struct AddOrder {
    pub msg_type: u8,
    pub ts_nanos: U32,
    pub order_id: U64,
    pub side: u8,
    pub qty: U64,
    pub instrument: U32,
    pub price: U32,
    pub flags: u8,
}
const _: () = assert!(core::mem::size_of::<AddOrder>() == 31);

let (msg, rest) = AddOrder::ref_from_prefix(buf).ok()?; // Err only when short
let id: u64 = msg.order_id.get();
```

```rust
use bytes::{Buf, BufMut, Bytes, BytesMut};

// land bytes: reserve first, because split_to never hands the front back
acc.reserve(READ_CHUNK);
let n = transport.recv_into(acc.spare_capacity_mut())?;
// SAFETY: recv_into initialized exactly n bytes of the spare slice
unsafe { acc.advance_mut(n) };

// peel complete frames: 2-byte BE length, then payload
fn next_frame(acc: &mut BytesMut) -> Option<Bytes> {
    let len = u16::from_be_bytes(acc.get(..2)?.try_into().ok()?) as usize;
    if acc.len() < 2 + len {
        return None; // partial frame waits for the next read
    }
    acc.advance(2);
    Some(acc.split_to(len).freeze()) // refcount bump, no copy
}
```

- `recv_into` above stands for any transport call that writes into `&mut [MaybeUninit<u8>]`. With a transport that hands out `&[u8]`, use `extend_from_slice` (one copy).
- Allocate the accumulator once, sized for the largest frame plus one read, and keep it for the connection's life.
- Frame stays on this thread: decode from `&acc[..total]`, then `acc.advance(total)`. No split, no refcount, no promotion allocation.
- Frame crosses a thread: `split_to(len).freeze()` and send the `Bytes`. The consumer decodes from `&frame[..]`.
- Encode into one reused buffer: `send.clear()`, then `put_u16`, `put_u8`, `put_slice`. Once warm, nothing allocates.

## Sharp edges

- `split_to` vs `split_off`: both O(1) on `BytesMut` and `Bytes`. The cost difference is capacity. `split_to` leaves spare capacity with the accumulator; `split_off` cuts `self` to `at` and gives the tail capacity away, so the next `reserve` must reclaim or allocate. Peel frames off the front with `split_to`.
- The first split of a fresh `BytesMut` allocates a small shared header (vec to shared promotion). A measured spike deframed a whole stream into a fresh `BytesMut` with exactly 2 allocations: one grow and one promotion. Every later split only bumped the refcount.
- `split_to` and `advance` never return the consumed front. Spare capacity shrinks as bytes land, so call `reserve` before `spare_capacity_mut`. Without it the slice reaches length 0 and the transport reads 0 bytes, which many loops treat as EOF.
- `reserve` past spare capacity on a unique buffer reuses its block: it takes back trailing room, or shifts live bytes to the front when the consumed front is at least as large as the live data. Otherwise it grows like `Vec`. While any split frame or frozen `Bytes` from the block is alive, it allocates a new buffer of `max(len + additional, original capacity capped at 64 KiB)` and copies the live bytes. Drop frames before the next read, or expect allocate plus copy.
- `Bytes::clone` is an atomic refcount increment, and drop is a decrement. `from_static` clones are free. The first clone of a `Vec`-backed `Bytes` allocates the shared header.
- Any live handle keeps the whole underlying block allocated. A small frame kept for minutes pins the full accumulator block; keep it with `Bytes::copy_from_slice`.
- Alignment: native `u32`/`u64` fields give the struct align 4 or 8. Frames land at arbitrary offsets, so `ref_from_bytes` returns `AlignmentError` depending on where the frame sat. Use `byteorder` fields and derive `Unaligned`; the derive then refuses any field with alignment above 1.
- Endianness: native integer fields read in host order. `NativeEndian` is a cfg alias that changes with the target. Name the wire order (`BigEndian` or `LittleEndian`) explicitly. `.get()` on a big-endian field calls `from_be_bytes`, the same work as the safe view.
- Layout: `#[derive(FromBytes)]` does not require `#[repr(C)]`, and without it field order is the compiler's choice. Pin `size_of` per struct. `#[derive(IntoBytes)]` rejects padding at compile time, which doubles as a padding check.
- Panics: `split_to`, `advance` and `Buf::get_*` panic on short input. With `panic = "abort"` a malformed packet kills the process. Check lengths first or use `try_get_*`.
- Unsafe raw-pointer views (`ptr::read_unaligned` without a length check) are not faster. In the measured spike they tied the safe view on wall clock (0.80 vs 0.80 ns, 8.82 vs 8.87 ns) and ran more instructions on 5 of 8 kinds (820 vs 805 on the 281-byte message). There is no performance case for `unsafe` here.

## Verify

- Layout pins next to each overlay: `const _: () = assert!(size_of::<T>() == N);`, `align_of::<T>() == 1`, and `core::mem::offset_of!(T, field) == K` for fields the spec lists. These are contract gates.
- Parity test: the view, the overlay and the spec agree field by field on captured message bytes, one test per message kind.
- Zero-copy proof: a counting global allocator with exact `assert_eq!` counts, never a `<=` bound. A view decode over a borrowed frame should count 0.
- Fuzz the deframer and every `parse` with cargo-fuzz. Feed arbitrary chunk splits (size 1 upward) so frames span reads, and check that a truncated tail stays in the buffer and is never emitted.
- Benchmarks read every field and fold the values into a checksum passed to `black_box`; lazy views otherwise look free. Report ns/msg and allocations per message, and add callgrind instruction counts on noisy hosts (`measure.md`).
- Run the `set_len` and `advance_mut` sites under Miri with a mock transport.
