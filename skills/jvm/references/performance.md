# JVM Performance

Loaded via `jvm` SKILL.md routing table. Sources: JMH samples (github.com/openjdk/jmh), JDK Flight Recorder and `jcmd` docs, HotSpot GC tuning guide, JEPs 483, 514, 515, 516 (AOT cache), 519 and 534 (compact object headers), 523 (G1 default).

## Measure first

- No optimization without a measurement that shows the problem and a second one that shows the fix. Report both numbers.
- Profile the real workload: JFR in production-like runs, async-profiler for CPU and allocation flame graphs. Microbenchmarks only for a hot method already found by profiling.
- Release builds, warm JVM, production flags and heap size. The first seconds of a run measure the JIT, not the code.

## JFR

```sh
java -XX:StartFlightRecording=duration=120s,filename=app.jfr,settings=profile -jar app.jar
jcmd <pid> JFR.start duration=60s filename=app.jfr settings=profile   # attach to a running JVM
jfr print --events jdk.ExecutionSample app.jfr | head                 # or open in JDK Mission Control
jcmd <pid> Thread.dump_to_file -format=json threads.json             # includes virtual threads (21+)
```

- JFR overhead is low enough for production with the `default` settings.
- Look at: hot methods, allocation by site, GC pauses, lock contention (`jdk.JavaMonitorEnter`), virtual thread pinning (`jdk.VirtualThreadPinned`), socket and file I/O.

## JMH

```java
@State(Scope.Benchmark)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(2)
public class ParseBench {
    private String input;

    @Setup
    public void setup() {
        input = "2026-11-05T10:15:30Z";
    }

    @Benchmark
    public Instant parse() {
        return Instant.parse(input);
    }
}
```

- Return the result or sink it into a `Blackhole`; otherwise dead-code elimination measures nothing.
- Inputs from `@State` fields, not constants the JIT can fold.
- Several forks; compare with error bars, not single numbers. `-prof gc` shows allocation per operation.
- JMH in its own source set or module (`me.champeau.jmh` Gradle plugin, or the Maven archetype); never in unit tests.

## Memory and GC

| Collector | Use | Notes |
|---|---|---|
| G1 | default; balanced throughput and pause | default in all environments from 27; before 27 the JVM picks Serial in constrained environments (a single CPU or under 1792 MB of memory), which includes many small containers |
| ZGC | large heaps, low pause targets | generational only from 24; `-XX:+UseZGC` |
| Parallel | batch throughput, pauses do not matter | |
| Shenandoah | low pause, where the JDK build includes it | generational mode is a product option from 25 |

- Containers: the JVM reads cgroup limits. Size the heap as a share of the container (`-XX:MaxRAMPercentage=75`) instead of a fixed `-Xmx` that ignores the limit, and leave room for metaspace, thread stacks, and direct buffers.
- Allocation rate drives GC cost more than heap size. Find the top allocation sites before tuning flags.
- Compact object headers shrink every object header (product option `-XX:+UseCompactObjectHeaders` in 25 and 26, on by default from 27); helps heaps full of small objects.
- Memory leaks: heap dump (`jcmd <pid> GC.heap_dump file.hprof`), then dominator tree in Eclipse MAT. Usual causes: unbounded caches and maps, listeners never removed, `ThreadLocal` on pooled threads.

## Code-level habits

- Collections: presize when the size is known (`new ArrayList<>(n)`, `HashMap.newHashMap(n)` on 19+). `ArrayList` over `LinkedList` nearly always. `EnumMap`/`EnumSet` for enum keys.
- Boxing in hot paths (`List<Integer>`, `Map<Long, ...>`, streams of boxed values): use primitive streams (`IntStream`, `mapToLong`) or primitive collections where profiling shows it.
- Streams cost more than loops for small inputs and in very hot code; fine elsewhere. Parallel streams only for large, CPU-bound, splittable work, and never with blocking calls.
- String building: `StringBuilder` in loops; `+` is fine in a single expression (compiled to `invokedynamic` concat).
- Regex: compile `Pattern` once into a `static final` field; `String.split`, `replaceAll`, and `matches` compile on every call (except single-character `split`).
- Logging: parameterized messages and level guards for expensive arguments (`if (log.isDebugEnabled())` or a supplier).
- Reflection and proxies in hot paths cost; frameworks cache them, your code should too.
- Exceptions are slow when they capture stack traces; they are for failures, not control flow.

## Startup and warm-up

- AOT cache (24+): a training run records loaded and linked classes, later runs start faster. On 25+, one step: `java -XX:AOTCacheOutput=app.aot -jar app.jar` for the training run, then `java -XX:AOTCache=app.aot -jar app.jar`. 25 adds method profiles, 26 lets the cache work with any GC.
- Class Data Sharing archives (`-XX:ArchiveClassesAtExit`) on releases before 24.
- GraalVM native image where startup and memory matter more than peak throughput and the code avoids unsupported reflection; Spring Boot supports it through its AOT processing.

## Virtual threads

- They raise throughput for blocking I/O, not CPU work. A CPU-bound service sees no gain.
- Pinning (21 to 23: blocking inside `synchronized`; all releases: native frames) shows as `jdk.VirtualThreadPinned` in JFR.
- Thread-per-request with virtual threads moves the bottleneck to pools and rate limits downstream: size database pools and add semaphores deliberately.
