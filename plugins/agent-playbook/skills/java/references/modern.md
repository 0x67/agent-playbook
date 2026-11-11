# Modern Java by Release

Loaded via `java` SKILL.md routing table. Sources: OpenJDK release pages (openjdk.org/projects/jdk/17 through /27) and JEPs, JDK API "Since" tags checked with `javac --release`. Checked 2026-11.

## Rule

- The repo's release is the ceiling: Gradle toolchain `languageVersion` or `options.release`, Maven `maven.compiler.release`, Kotlin `jvmTarget`. No API or syntax above it; `javac --release N` rejects most API leaks, but only when the build actually passes `--release` (`jvm` skill, `build.md`).
- The release is only half of it. Every tool in the build must support it too: check the version compatibility table in the `jvm` skill (`references/build.md`). When either rules a feature out, use `Below the feature's release`.
- Preview features (`--enable-preview`) only when the build already enables them, for that exact JDK; class files compiled with preview features run only on that JDK release. Incubator modules (`jdk.incubator.*`) likewise.
- Raising the release is a repo decision (runtime images, libraries' consumers, CI). Ask before raising it in someone else's project. LTS releases: 17, 21, 25. Libraries usually target the oldest LTS their users run; services can track the newest LTS.
- New code uses the newest idiom the release allows. Existing code: modernize in a separate commit (OpenRewrite recipes or IDE inspections), then review the diff.

## Ladder

| Release | Unlocks (final features; previews excluded) |
|---|---|
| 17 LTS (baseline) | everything from 9 to 16: `var`, `List.of`/`Map.of`/`List.copyOf`, `Optional.orElseThrow()`/`isEmpty`/`stream`, `HttpClient`, `String.isBlank`/`strip`/`lines`/`repeat`/`formatted`/`indent`, `Files.readString`/`writeString`, `Predicate.not`, `Collectors.teeing`, switch expressions, text blocks, records, pattern matching `instanceof`, `Stream.toList()`/`mapMulti`, helpful NullPointerException messages. New in 17: sealed classes, `RandomGenerator`, `HexFormat`, strong encapsulation of JDK internals (`--illegal-access` gone), context-specific deserialization filters |
| 18 | UTF-8 default charset (JEP 400), `jwebserver` simple web server, `@snippet` in Javadoc, `Math.ceilDiv` and friends, finalization deprecated for removal |
| 19 | `ExecutorService.close()` (try-with-resources), `Future.resultNow()`/`exceptionNow()`/`state()`, presized `HashMap.newHashMap(n)`/`HashSet.newHashSet(n)`/`LinkedHashMap.newLinkedHashMap(n)` |
| 20 | no new final language features; `new URL(String)` constructors deprecated (use `URI.create(...).toURL()`) |
| 21 LTS | pattern matching for `switch` (JEP 441), record patterns (440), virtual threads (444): `Thread.ofVirtual()`, `Executors.newVirtualThreadPerTaskExecutor()`, `Thread.Builder`; sequenced collections (431): `getFirst`, `getLast`, `reversed`, `addFirst`, `SequencedMap.firstEntry`; generational ZGC (439); `Math.clamp`, `StringBuilder.repeat`, `String.splitWithDelimiters`, `Character.isEmoji`, `HttpClient.close()`; key encapsulation mechanism API; warnings for dynamically loaded agents (451) |
| 22 | unnamed variables and patterns `_` (456), Foreign Function and Memory API (454), launching multi-file source programs (458), G1 region pinning for JNI critical regions |
| 23 | Markdown doc comments `///` (467), ZGC generational mode by default (474), `sun.misc.Unsafe` memory-access methods deprecated. String templates were withdrawn after two previews (21, 22) |
| 24 | stream gatherers (485): `stream.gather(Gatherers.windowFixed(n))`; Class-File API (484); virtual threads no longer pin inside `synchronized` (491); ahead-of-time class loading and linking (483); Security Manager permanently disabled (486); JNI use warnings (472); non-generational ZGC removed; ML-KEM and ML-DSA post-quantum algorithms (496, 497); `jlink` without JMOD files (493) |
| 25 LTS | scoped values (506); flexible constructor bodies, statements before `super(...)` (513); module import declarations (511); compact source files and instance `main` with `java.lang.IO` (512); key derivation function API (510); AOT cache ergonomics `-XX:AOTCacheOutput` (514) and AOT method profiling (515); compact object headers as a product option `-XX:+UseCompactObjectHeaders` (519); generational Shenandoah (521); JFR method timing (520) and CPU-time profiling on Linux (509, experimental); 32-bit x86 port removed |
| 26 | HTTP/3 in `HttpClient` (517, opt-in per client or request; HTTP/2 stays the default); AOT object caching with any GC (516); warnings when deep reflection mutates `final` fields (500); Applet API removed (504); G1 throughput improvements (522) |
| 27 | G1 is the default collector in all environments (523); compact object headers on by default (534); hybrid post-quantum key exchange for TLS 1.3 (527); JFR in-process data redaction (536) |

Still preview or incubating in 27: structured concurrency (seventh preview), lazy constants (third preview; called stable values in 25), primitive types in patterns, `instanceof`, and `switch` (fifth preview), PEM encodings (third preview), Vector API (twelfth incubator). Their APIs change between releases.

## Below the feature's release

When the release or a tool rules a feature out, write it this way instead.

| Feature (release) | On an older release |
|---|---|
| UTF-8 default charset (18) | pass `StandardCharsets.UTF_8` to every reader, writer, `getBytes`, and `new String(bytes, ...)` |
| `ExecutorService` in try-with-resources (19) | `shutdown()` in `finally`, `awaitTermination` with a timeout, then `shutdownNow()` |
| `HashMap.newHashMap(n)` (19) | `new HashMap<>((int) Math.ceil(n / 0.75))` |
| `Future.resultNow()` (19) | `get()` after `isDone()`, handling `ExecutionException` |
| pattern `switch` (21) | `if`/`else if` chain of `instanceof` patterns ending in `throw new AssertionError(x)`, or a visitor on the sealed type |
| record patterns (21) | `instanceof Point p`, then `p.x()` |
| virtual threads (21) | a bounded platform pool sized to the blocking resource, or an async client |
| `getFirst`/`getLast`/`reversed` (21) | `list.get(0)`, `list.get(list.size() - 1)`, a reversed copy; `Deque`/`NavigableSet` methods |
| `Math.clamp` (21) | `Math.max(min, Math.min(max, value))` |
| `StringBuilder.repeat` (21) | `sb.append(s.repeat(n))` (`String.repeat` is 11) |
| `HttpClient.close()` (21) | one shared client for the application's lifetime, never one per request |
| unnamed `_` (22) | a name such as `ignored` |
| Markdown doc comments (23) | `/** */` with HTML tags |
| stream gatherers (24) | a loop, or a custom `Collector`; sliding windows over indices with `IntStream.range` |
| `synchronized` without pinning (24) | on 21 to 23 virtual threads, `ReentrantLock` around blocking calls inside critical sections |
| scoped values (25) | pass context as a parameter, or `ThreadLocal` set and `remove()`d in `try/finally` |
| statements before `super(...)` (25) | a `private static` helper that validates and returns the argument, called inside `super(...)` |
| instance `main`, `IO.println` (25) | `public static void main(String[] args)`, `System.out.println` |
| `StructuredTaskScope` (preview) | `ExecutorService` in try-with-resources, `Future.get` on each task, cancel the rest on the first failure |

## Replacement table

Old idioms to replace in new or touched code on 17+:

| Old | Modern |
|---|---|
| `Date`, `Calendar`, `SimpleDateFormat`, `Timestamp` arithmetic | `Instant`, `LocalDate`, `ZonedDateTime`, `Duration`, `DateTimeFormatter` |
| POJO with hand-written `equals`/`hashCode`/`toString`, Lombok `@Value` | `record` |
| `instanceof` then cast | `if (o instanceof Foo f)` |
| `switch` statement with `break` | switch expression with `->` |
| string concatenation across lines | text block |
| `Collections.unmodifiableList(new ArrayList<>(x))` | `List.copyOf(x)` |
| `Arrays.asList(a, b)` for a fixed list | `List.of(a, b)` |
| `.collect(Collectors.toList())` | `.toList()` when an unmodifiable result is fine |
| `Optional.get()` | `orElseThrow()` |
| `new Integer(x)`, `new Double(x)` (deprecated for removal) | `Integer.valueOf(x)`, autoboxing |
| `Vector`, `Hashtable`, `StringBuffer` | `ArrayList`, `HashMap`/`ConcurrentHashMap`, `StringBuilder` |
| `File` | `Path` and `Files` |
| `new URL(String)` | `URI.create(s).toURL()` |
| `finalize()` | try-with-resources, or `Cleaner` as a safety net |
| `javax.servlet`, `javax.persistence` | `jakarta.*` |
| shared `Random` across threads | `ThreadLocalRandom.current()` or a `RandomGenerator` per thread |
| `sun.misc.Unsafe` memory access, JNI glue | `VarHandle`, Foreign Function and Memory API (22+) |
| `Thread` subclasses and manual thread start | an executor; virtual threads on 21+ |
