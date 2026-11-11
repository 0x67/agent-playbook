# io-uring (Rust)

Loaded via the low-latency SKILL.md routing table. Checked against io-uring 0.7.15 on 2026-11-06. Sources: io-uring 0.7.15 crate source (`src/lib.rs`, `squeue.rs`, `cqueue.rs`, `submit.rs`, `opcode.rs`, `types.rs`, `register.rs`, `examples/tcp_echo.rs`), man pages io_uring_setup(2), io_uring_enter(2), io_uring_register(2), io_uring_register_buf_ring(3), io_uring_prep_recv_multishot(3), kernel `include/trace/events/io_uring.h`.

## When to use it

- `io-uring` is the raw binding: a submission queue (SQ) and completion queue (CQ) shared with the kernel. No runtime, no futures. You own the buffers, the request ids and the event loop.
- Reach for it over epoll (`mio`, `tokio`) only when a profile shows syscalls or buffer handling as the receive-path cost. One `io_uring_enter` submits and reaps a batch, a multishot recv stays armed across many datagrams, and buffer rings let the kernel pick the buffer. A readiness loop plus `recv` is simpler; measure both at the same rate.
- Linux only. The crate issues `libc::SYS_io_uring_*` syscalls, so gate the dependency under `[target.'cfg(target_os = "linux")'.dependencies]` and the module under `#[cfg(target_os = "linux")]`.
- macOS dev: keep a portable backend (`mio` or `std::net::UdpSocket`) behind the same receive trait. Put CQE classification and buffer-id bookkeeping in plain functions so their tests run on any OS.
- `tokio-uring` 0.5 is a runtime on top, but it depends on `io-uring` 0.6, so its types do not mix with 0.7.
- `io_uring_setup` returns `EPERM` when `/proc/sys/kernel/io_uring_disabled` is 2, or 1 for a caller without `CAP_SYS_ADMIN` outside `io_uring_group`. Seccomp profiles can block it too. Map `EPERM` and `ENOSYS` from `build` to "unavailable" and fall back.

## Core API

```rust
use io_uring::{cqueue, opcode, squeue, types, IoUring};

let mut ring: IoUring = IoUring::builder()
    .setup_cqsize(4096)    // must exceed SQ entries; multishot posts many CQEs per SQE
    .setup_coop_taskrun()  // 5.19, no forced interrupt on completion
    .setup_taskrun_flag()  // 5.19, sq.taskrun() flags pending work
    .setup_single_issuer() // 6.0
    .build(256)?;          // SQ entries, power of two
```

- `IoUring::new(n)` is `IoUring::builder().build(n)`. `Builder` setters take `&mut self`. `ring.params()` reports what the kernel granted: `is_feature_nodrop()`, `is_feature_fast_poll()`, `is_feature_recvsend_bundle()`, `is_feature_skip_cqe_on_success()`, `is_setup_sqpoll()`, `sq_entries()`, `cq_entries()`.
- Setup flags in 0.7.15: `setup_sqpoll(idle_ms)`, `setup_sqpoll_cpu(cpu)`, `setup_iopoll()` (`O_DIRECT` files on polling filesystems), `setup_cqsize(n)`, `setup_clamp()`, `setup_attach_wq(fd)`, `setup_r_disabled()` (5.10), `setup_submit_all()` (5.18), `setup_coop_taskrun()` and `setup_taskrun_flag()` (5.19), `setup_single_issuer()` (6.0), `setup_defer_taskrun()` (6.1), `setup_no_sqarray()` (6.6), `dontfork()`.
- Builders: `opcode::X::new(required).optional(v).build()` returns `squeue::Entry`. Chain `.user_data(u64)` and `.flags(squeue::Flags::...)` on the entry. The `fd` argument takes `types::Fd(raw)` or `types::Fixed(index)`.
- Receive opcodes: `Recv::new(fd, buf: *mut u8, len)` with `.flags(i32)` and `.buf_group(u16)` (5.6). `RecvMulti::new(fd, buf_group)` with optional `.len(cap)` (6.0). `RecvMsgMulti::new(fd, msghdr_ptr, buf_group)` (6.0); parse each buffer with `types::RecvMsgOut::parse(buf, &msghdr)` for source address and payload. `RecvBundle` and `RecvMultiBundle` (6.10). `ReadFixed::new(fd, buf, len, buf_index)`. `ReadMulti::new(fd, len, buf_group)` (6.7).

```rust
let recv = opcode::RecvMulti::new(types::Fd(sock_fd), BGID).build().user_data(RECV_TAG);
unsafe { ring.submission().push(&recv)? }; // kernel writes group buffers until the final CQE
ring.submit_and_wait(1)?;
for cqe in ring.completion() {
    let res = cqe.result();                        // < 0 is -errno
    let bid = cqueue::buffer_select(cqe.flags());  // Some(id) when the kernel picked a buffer
    let ended = !cqueue::more(cqe.flags());        // multishot is over, re-arm
}
```

- `ring.submission()` and `ring.completion()` borrow `&mut ring` and publish head or tail on drop. `ring.split()` returns `(Submitter, SubmissionQueue, CompletionQueue)` for a loop that holds all three; then call `sq.sync()` before submitting and `cq.sync()` after.
- `sq.push(&e)` is `unsafe` and returns `Err(PushError)` when full. `push_multiple(&[e])` pushes all or none. Also `is_full()`, `is_empty()`, `len()`, `capacity()`, `cq_overflow()`, `taskrun()`, `need_wakeup()`.
- `submit()` is `submit_and_wait(0)`. `submit_and_wait(n)` enters with `GETEVENTS` and blocks until `n` CQEs are ready. `submitter().submit_with_args(n, &types::SubmitArgs::new().timespec(&ts))` bounds the wait; `.min_wait_usec(us)` needs 6.12 (`is_feature_min_timeout()`).
- CQE: `result() -> i32`, `user_data() -> u64`, `flags() -> u32`. Flag helpers in `cqueue`: `buffer_select`, `more`, `sock_nonempty`, `buffer_more` (incremental rings), `notif`. `cq.fill(&mut [MaybeUninit<cqueue::Entry>])` reaps into a slice.
- Registration on `ring.submitter()`: `register_files(&[RawFd])`, `register_files_update(offset, &fds)`, `register_files_sparse(n)`, `unsafe register_buffers(&[libc::iovec])`, `unsafe register_buf_ring_with_flags(addr, entries, bgid, flags)` and `unregister_buf_ring(bgid)` (5.19), `register_probe(&mut Probe)`, `register_ring_fd()` (5.18), `register_napi(&mut types::Napi)` (6.9), `register_sync_cancel(timeout, CancelBuilder)` (6.0).

## Idioms

- Buffer ring for receive (5.19). Map page-aligned memory for `n` `types::BufRingEntry` slots (`n` a power of two, at most 32768), register it as group `bgid`, and refill it from user space with no SQE per buffer. The tail lives in the `resv` field of entry 0 (`BufRingEntry::tail`).

```rust
unsafe { submitter.register_buf_ring_with_flags(base as u64, n, BGID, 0)? }; // base: *mut BufRingEntry
let tail = unsafe { AtomicU16::from_ptr(types::BufRingEntry::tail(base).cast_mut()) };
for bid in returned.drain(..) {
    let e = unsafe { &mut *base.add(usize::from(local_tail & (n - 1))) };
    e.set_addr(slot_addr(bid)); e.set_len(SLOT_LEN); e.set_bid(bid); // field setters keep entry 0's tail
    local_tail = local_tail.wrapping_add(1);
}
tail.store(local_tail, Ordering::Release); // one publish per batch
```

- `buffer_select(flags)` gives the buffer id; the payload is `slot(bid)[..res]`. Return the id to the ring only after the consumer is done with it. Consumers on other threads send ids back through a queue, and the ring thread republishes them in one batch.
- `flags` for `register_buf_ring_with_flags` is a raw `u16`; the crate does not export the `IOU_PBUF_RING_*` constants. Incremental consumption (`IOU_PBUF_RING_INC`) needs 6.12. `register_buf_ring` is deprecated.
- Legacy provided buffers (5.7): `ProvideBuffers::new(addr, len, nbufs, bgid, bid)` costs one SQE per contiguous run of ids. Use it only where buffer rings are missing, and tag it `squeue::Flags::SKIP_SUCCESS` (5.17) to drop the success CQE.
- One-shot `Recv` from a group needs `.buf_group(bgid).build().flags(squeue::Flags::BUFFER_SELECT)`; `Recv` does not set the flag. `RecvMulti`, `RecvMsgMulti`, `RecvBundle`, `RecvMultiBundle` and `ReadMulti` set it themselves.
- Multishot: one `RecvMulti` stays armed while its CQEs carry `more(flags)`. A CQE without it ends the request; `-ENOBUFS` (the group ran dry) fails it. Refill, then re-arm. Check flags on every CQE, success or error.
- Registered buffers (`register_buffers` plus `ReadFixed`, `buf_index` = iovec index) suit reads where the app picks the buffer at submit time. Buffer rings suit datagram receive, where any free buffer will do. Each registered buffer is anonymous memory, at most 1 GiB, charged to `RLIMIT_MEMLOCK` unless the process has `CAP_IPC_LOCK`.
- Registered files: `register_files(&[fd])` once, then pass `types::Fixed(i)` instead of `types::Fd(fd)`. Swap entries on a live ring with `register_files_update`.
- Batch: push every SQE for one loop turn, then call `submit()` once, then drain the whole CQ. Without SQPOLL, `submit()` always calls `io_uring_enter`, even on an empty SQ. Skip it when `sq.is_empty()`, `!sq.cq_overflow()` and `!sq.taskrun()` all hold, so an idle spin makes no syscall.
- One ring per thread. `submission()` and `completion()` need `&mut IoUring`, and `setup_single_issuer()` makes the kernel enforce one submitter (others get `-EEXIST`). Pin the ring thread; with SQPOLL, pin the poller to another isolated core with `setup_sqpoll_cpu`.
- `register_ring_fd()` takes `&mut Submitter` and only that `Submitter` uses it. `ring.submit()` builds a fresh `Submitter` per call and skips it, so submit through the one from `split()`.
- NAPI busy poll (6.9): `submitter.register_napi(&mut types::Napi::new().set_busy_poll_timeout(us).set_prefer_busy_poll(true))`. Default tracking is `NapiTracking::Dynamic`.
- Startup detection: `probe.is_supported(opcode::Recv::CODE)` checks opcodes, but `RecvMulti` and the bundle variants share `IORING_OP_RECV`, and buffer rings are not opcodes. A buffer-ring registration the kernel lacks fails with `ErrorKind::InvalidInput`. Gate multishot and bundles on kernel version, `params()` bits, or a trial request, and log the chosen path.

## Sharp edges

- Buffer lifetime: opcodes take raw pointers (`*mut u8`, `*const libc::msghdr`), and `push` is `unsafe` because the kernel uses that memory until the request's final CQE, long after `push` returns. A `Vec` that reallocates or a buffer dropped while its recv is armed is a use-after-free. Registered buffers and buffer rings must stay valid until unregistered or the ring is gone.
- Drop does not cancel. `Drop for IoUring` unmaps the rings and closes the fd, nothing more. Cancel first with `AsyncCancel::new(ud)`, `AsyncCancel2::new(CancelBuilder::user_data(ud).all())` (5.19) or `register_sync_cancel(Some(timeout), CancelBuilder::any())` (6.0). Reap until every armed request posts its final CQE, then free memory. If that wait times out, leak the memory.
- CQ overflow: size the CQ for every completion that can be outstanding. With `IORING_FEAT_NODROP` (5.5) the kernel holds overflowed CQEs and sets `sq.cq_overflow()`. They move back only on an enter, which `submit*` issues with `GETEVENTS` when it sees the flag, so a loop that never enters strands them. `EBUSY` means overflow could not be flushed: reap, then retry. `EBADR` (5.19) means a CQE was lost even with NODROP. `cq.overflow()` counts lost CQEs.
- SQPOLL: the kernel thread never sleeps while I/O stays busy, so each SQPOLL ring burns a core. After `idle_ms` without work it sets `need_wakeup()`, and `submit*` wakes it. While it is awake, `submit()` makes no syscall. Privileges: 5.11 accepts `CAP_SYS_NICE`, 5.13 needs none. Before 5.11 every fd had to be registered (`is_feature_sqpoll_nonfixed()`).
- Task-run modes: `setup_coop_taskrun()` drops the forced interrupt, so completion work waits for the next kernel entry. A spin loop that skips enters also needs `setup_taskrun_flag()` and must enter when `sq.taskrun()` is set. `setup_defer_taskrun()` needs `setup_single_issuer()` and runs completion work only on an enter with `GETEVENTS` from the submitting thread. A loop that only peeks at the CQ stalls. `submit*` adds `GETEVENTS` on its own when `sq.taskrun()` is set.
- Kernel gates: every flag and opcode above has a minimum kernel. Check `params()` feature bits and `Probe` on the target host, not the build host.
- user_data: the kernel copies it from SQE to CQE unchanged. Multishot CQEs all repeat it, and `AsyncCancel` matches only the first request with it. Encode request kind plus slot index (plus a generation if slots are reused) so a late CQE from a cancelled request cannot pass as its replacement. `register_buffers2` tags arrive as CQEs with `user_data` set to the tag; keep the two ranges disjoint.
- `register_files` waits for the ring to go idle; use `register_files_update` on a live ring.
- `PushError` means the SQ is full: submit, then push again. `EAGAIN` (kernel out of resources) and `EINTR` from an enter are retryable after reaping.

## Verify

- Run ring tests on Linux, on a kernel at least as new as the newest feature you gate on. Mark them `#[ignore]` and run `cargo test -- --ignored` in a Linux CI job. A setup `EPERM` there must fail the job, not skip silently.
- Miri cannot execute the `io_uring_setup` syscall the crate makes through `libc::syscall`. Keep CQE classification, buffer-id accounting and ring index math in pure functions, and run those under Miri and property tests.
- `strace -f -c -e trace=io_uring_enter,io_uring_register ./app` counts enters. A batching loop shows far fewer enters than messages; an awake SQPOLL loop shows almost none.
- `perf stat -e 'io_uring:io_uring_submit_req,io_uring:io_uring_complete,io_uring:io_uring_queue_async_work,io_uring:io_uring_cqe_overflow' -p PID -- sleep 10`. `io_uring_cqe_overflow` must stay at zero. Nonzero `io_uring_queue_async_work` on a socket path means requests went to async workers.
- Record per-message latency into an HdrHistogram and compare p50, p99, p99.9 and max against the epoll backend at a fixed rate (`measure.md`). Export `-ENOBUFS` CQEs, CQ overflow and enters per message as counters.
- A ring parked in `submit_and_wait` counts as iowait and in `/proc/pressure/io` with no I/O outstanding. `EnterFlags::NO_IOWAIT` (6.15, `is_feature_no_iowait()`) through raw `Submitter::enter` stops that.
