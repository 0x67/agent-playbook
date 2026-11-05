# CPU pinning (Rust)

Loaded via the low-latency SKILL.md routing table. Checked against core_affinity 0.8.3 on 2026-11-06. Sources: core_affinity 0.8.3 `src/lib.rs` and docs.rs; Linux kernel docs `admin-guide/kernel-parameters.txt`, `admin-guide/cpu-isolation.rst`, `core-api/irq/irq-affinity.rst`, `admin-guide/mm/numa_memory_policy.rst`, `admin-guide/hw-vuln/l1tf.rst`, `admin-guide/cgroup-v2.rst`, ABI `sysfs-devices-system-cpu` and `sysfs-bus-pci`; man pages sched_setaffinity(2), sched_setscheduler(2), sched(7), pthread_create(3), sched_getcpu(3), proc_pid_task(5), cpuset(7), taskset(1), chrt(1), ps(1), numactl(8); xnu `osfmk/kern/thread_policy.c`, `osfmk/kern/affinity.c`, `osfmk/arm/cpu_affinity.h`.

## When to pin

- Pin when a latency histogram shows tail spikes you can tie to migration, preemption, or a cold cache, on a Linux host you control. The scheduler already keeps a task on the same CPU when practical (taskset(1)), so pinning without a measured problem only adds config.
- Pinning pays when a hot thread (feed handler, matching loop, busy-polling I/O thread) gets a whole core. A thread pinned to a CPU it shares still waits for its turn there.
- A pin changes the thread's CPU mask and nothing else. Interrupts, the timer tick, RCU callbacks, kworkers, and other tasks keep landing on that CPU until the host is set up (see Linux host setup).
- macOS has no hard affinity. Take placement-sensitive numbers on Linux hardware that matches production.

## core_affinity

```rust
pub fn get_core_ids() -> Option<Vec<CoreId>>;
pub fn set_for_current(core_id: CoreId) -> bool;

#[repr(transparent)]
#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct CoreId { pub id: usize }
```

- That is the whole public API: one CPU per call, calling thread only. No mask type, no way to pin another thread, no topology (SMT, NUMA), no priorities.
- `id` is public, so `CoreId { id: 3 }` builds one from config. `set_for_current` does not check it against `get_core_ids()`.
- Linux and Android, `get_core_ids`: calls `sched_getaffinity(0, ...)` on the calling thread and returns every set bit in ascending order. That is the thread's current mask, so under a cpuset or `taskset` it lists only the allowed CPUs, and after a pin it lists only the pinned one. `None` when the syscall fails.
- Linux and Android, `set_for_current`: builds a one-CPU `cpu_set_t` and calls `sched_setaffinity(0, ...)`. `true` means the syscall returned 0. A CPU that is offline or outside the cpuset gives EINVAL (sched_setaffinity(2)); the crate returns `false` and drops errno.
- On glibc targets the `cpu_set_t` it passes covers CPUs 0 to 1023. When the kernel affinity mask is larger, `sched_getaffinity` with that size fails with EINVAL, so `get_core_ids` returns `None`.
- macOS, `get_core_ids`: always `Some` of `0..num_cpus::get()`; it reads no mask. `set_for_current` calls `thread_policy_set` with `THREAD_AFFINITY_POLICY` and passes `id` as an affinity tag. A tag groups threads as a scheduler hint and names no CPU. On Apple silicon xnu answers `KERN_NOT_SUPPORTED` and the call returns `false`; on Intel Macs it can return `true` with nothing pinned.
- Windows: `get_core_ids` reads the process affinity mask, bits 0 to 63 only. `set_for_current` calls `SetThreadAffinityMask(GetCurrentThread(), 1 << id)` and returns `true` on a nonzero result.
- FreeBSD uses `cpuset_setaffinity` on the current thread, NetBSD `pthread_setaffinity_np`. Any other target gets `None` and `false`.
- A new thread inherits a copy of its creator's affinity mask (pthread_create(3)). Pin the main thread and every thread spawned after that starts on the same single CPU.

## Linux host setup

- `isolcpus=[flag-list,]<cpu-list>` takes flags `domain` (default), `nohz`, `managed_irq`. `domain` removes the CPUs from scheduler load balancing until reboot; tasks reach them only through affinity syscalls or cpusets. cpu-isolation.rst recommends cgroup v2 cpuset isolated partitions (`cpuset.cpus.partition` set to `isolated`) because they can change at runtime.
- `nohz_full=<cpu-list>` (needs `CONFIG_NO_HZ_FULL=y`) stops the tick on those CPUs while a single task runs there and offloads their RCU callbacks as `rcu_nocbs=` would. The boot CPU is always kept out. Costs per cpu-isolation.rst: slower syscall, exception, and IRQ entry and exit, a 1 Hz residual tick run by housekeeping CPUs, and no POSIX CPU timers on the isolated CPUs.
- `rcu_nocbs=<cpu-list>` (needs `CONFIG_RCU_NOCB_CPU=y`) runs those CPUs' RCU callbacks in `rcuo` kthreads instead of softirq on the CPU. `rcu_nocb_poll` makes the kthreads poll so the offloaded CPU does not have to wake them, at an energy cost.
- `irqaffinity=<cpu-list>` sets the default IRQ mask, and `/proc/irq/<n>/smp_affinity_list` moves one IRQ; a list with no CPUs is refused. Managed IRQ affinity cannot be changed through `/proc/irq`; `isolcpus=managed_irq,<cpus>` steers them off isolated CPUs on a best-effort basis.
- The global workqueue runs on all CPUs by default. Restrict `/sys/devices/virtual/workqueue/cpumask` to housekeeping CPUs.
- Keep at least one housekeeping CPU, more on large machines, for example one per NUMA node.
- Full example from cpu-isolation.rst, 8 CPUs with CPU 7 isolated: `nohz_full=7 irqaffinity=0-6 isolcpus=managed_irq,7 nosmt`.
- NUMA: the default memory policy is local allocation, which starts at the node of the CPU where the allocation takes place. Put hot threads on their NIC's node (`/sys/bus/pci/devices/<bdf>/numa_node`, `-1` when unknown); `numactl --hardware` lists nodes and their CPUs.
- SMT: `/sys/devices/system/cpu/cpuN/topology/core_cpus_list` (old name `thread_siblings_list`) lists the hardware threads of one core. The `nosmt` boot parameter or `/sys/devices/system/cpu/smt/control` turns SMT off.
- Priorities: SCHED_FIFO and SCHED_RR take 1 (low) to 99 (high) and always preempt SCHED_OTHER. Unprivileged threads need a nonzero `RLIMIT_RTPRIO` or `CAP_SYS_NICE`. From Rust, `libc::sched_setscheduler(0, libc::SCHED_FIFO, &param)` changes the calling thread only.
- Leftover jitter checklist from cpu-isolation.rst: `mlock()` against page faults, careful cpufreq tuning, limits on deep C-states (`processor.max_cstate`, `intel_idle.max_cstate`), and firmware interrupts such as SMIs.

```sh
taskset -c 7 ./app                          # start with a CPU list
taskset -a -pc 2-5 <pid>                    # every thread of a running process
chrt -f 50 ./app                            # SCHED_FIFO, priority 50
numactl --cpunodebind=0 --membind=0 ./app   # CPUs and memory on node 0
echo 0-6 > /proc/irq/<n>/smp_affinity_list  # keep IRQ <n> off CPU 7
```

## Idioms

- One hot thread per isolated core. It busy-polls and owns the core; logging, metrics, admin, and async runtimes run on housekeeping CPUs.
- Read `get_core_ids()` once on the main thread before anything is pinned and pass the list down. Inside a pinned thread it returns that one core.
- Pin as the first statement of the thread body, then allocate the thread's buffers, rings, and caches. Under local allocation their pages come from the pinned core's node, and they warm that core's cache.
- Core lists live in config. At startup, fail when an id is missing from `get_core_ids()`, when two hot threads share a core or a pair of SMT siblings, or when a hot core is also a housekeeping core.
- Check the `bool`. In production a failed pin is a startup error. On dev machines make pinning a config switch and log the outcome with the core id.

```rust
let allowed = core_affinity::get_core_ids().ok_or(PinError::NoMask)?; // main thread, before any pin
let core = CoreId { id: cfg.feed_core };
if !allowed.contains(&core) { return Err(PinError::NotAllowed(core.id)); }
let feed = std::thread::Builder::new().name("feed".into()).spawn(move || {
    if !core_affinity::set_for_current(core) { return Err(PinError::Refused(core.id)); }
    let mut ring = Ring::with_capacity(cfg.ring_len); // allocated after the pin
    run_feed(&mut ring);
    Ok(())
})?;
```

## Sharp edges

- macOS and other dev machines: `get_core_ids()` lists every CPU, and `set_for_current` returns `false` on Apple silicon, or `true` on Intel with only a hint set. Code that ignores the `bool` and logs "pinned" pins nothing, and laptop numbers say nothing about pinned tails.
- SMT siblings are separate CPU ids on one physical core and share its L1 data cache (l1tf.rst). `get_core_ids()` carries no topology, so two hot threads on sibling ids still contend for one core. Check `core_cpus_list`; cpu-isolation.rst advises avoiding SMT so a sibling cannot "preempt" the hot hardware thread.
- Two hot threads pinned to one core time-share it, and `nohz_full` keeps the tick running there because preempting between tasks needs it.
- Busy-spin on a non-isolated core: the CPU stays in load balancing, so other tasks get placed on it and the tick keeps firing. Under SCHED_FIFO the spinner can instead lock other threads out of that CPU (sched(7)); the default budget of `sched_rt_runtime_us` 950000 per `sched_rt_period_us` 1000000 reserves 5% for non-RT tasks.
- Containers and cgroups: the cpuset limits `get_core_ids()` to `cpuset.cpus.effective`, and a pin outside it fails with EINVAL. A core list written for the bare host can name CPUs the container lacks, so validate inside the container. The kernel also narrows masks to the cpuset without telling the caller (sched_setaffinity(2)).
- `taskset -p` changes only the main thread because affinity is per thread. `taskset -a -p` changes every thread and overwrites pins the program set itself.
- Pinning the main thread before a runtime or thread pool starts puts all its workers on that one core through the inherited mask.

## Verify

- Linux, in process: right after `set_for_current(core)`, `get_core_ids()` should return exactly `[core]` because it reads the thread's own mask. `libc::sched_getcpu()` returns the CPU the thread is on now. Log both for each hot thread at startup. On macOS neither proves anything.
- `taskset` exit status 0 means the mask was set; the thread may not have moved yet (taskset(1)). Read `psr` once load is running.

```sh
ps -L -o tid,psr,comm -p <pid>                     # psr: CPU each thread last ran on
taskset -pc <tid>                                   # one thread's mask
grep Cpus_allowed_list /proc/<pid>/task/<tid>/status
cat /sys/devices/system/cpu/isolated /sys/devices/system/cpu/nohz_full
grep -E 'CPU|<irq>:' /proc/interrupts               # per-CPU IRQ counts, sample twice under load
```

- Residual noise on an isolated CPU: cpu-isolation.rst enables the `sched_switch` and `irq_vectors` trace events and reads `/sys/kernel/tracing/per_cpu/cpuN/trace`; `rtla osnoise` summarizes the same noise.
- Record per-message latency in a histogram (p50, p99, p99.9, max) under the same replayed load before and after each change: pin, isolate, IRQ move, SMT off (`measure.md`). Keep a change only when the tail improves on production-like hardware.
