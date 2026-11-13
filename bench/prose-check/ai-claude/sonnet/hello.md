# Hello, 中国!

*How we prepared our platform to serve users in mainland China, and what we learned about latency, compliance, and text along the way.*

When we first looked at our traffic dashboards, one number stood out: requests from mainland China had a p95 latency of over 2.4 seconds, nearly five times what we saw in Europe or North America. Users were reaching us, but not happily. This post covers how we approached the problem, the technical decisions we made, and the surprises that came with them.

## Why this was harder than adding a region

On paper, serving China looks like any other multi-region expansion: add a point of presence, route traffic, done. In practice, three things make it different.

**Network topology.** Traffic crossing the border passes through international gateways that introduce variable latency and packet loss. Even when the physical distance is modest, say from Hong Kong to Shanghai, the path can be unpredictable. Throughput varies by time of day, and long-lived connections can be reset.

**Regulatory requirements.** Hosting content within mainland China generally requires an ICP filing, and handling personal data triggers obligations under laws such as PIPL. These are not engineering problems, but they shape our architecture: where data lives, which services can call which, and how we audit access.

**Ecosystem differences.** Many of the third-party services we depend on, including some analytics tools, font CDNs, and package registries, are slow or unreachable from within China. Anything on our critical path that relied on them became a liability.

## Our approach

We settled on three principles: keep the critical path local, make everything else degrade gracefully, and isolate China-specific data.

### 1. A separate deployment, not a bigger one

Rather than stretching our existing global cluster, we stood up an independent deployment inside mainland China with its own database, cache, and object storage. A thin replication layer syncs non-personal configuration data from our global systems. Personal data stays in-region by default.

This cost us some simplicity. We now have two deployment targets and must keep them in lockstep. We addressed this by making our infrastructure definitions region-parameterized, so the same code produces both environments with different variables.

### 2. Removing hidden external dependencies

We audited every outbound request our frontend made on page load. The results were humbling: 14 third-party domains, 6 of which were unreliable from China. We:

- Self-hosted fonts and static assets
- Replaced a blocked analytics script with a first-party event pipeline
- Mirrored our npm and container image dependencies for in-region builds
- Added timeouts and fallbacks to every remaining third-party call

Page load time dropped by more than half from this step alone, before we touched any servers.

### 3. Treating text as a first-class concern

The title of this post is a hint. Supporting Chinese properly goes well beyond translating strings.

- **Encoding.** We found two legacy services that assumed Latin-1 in log processing and silently corrupted non-ASCII characters. We moved everything to UTF-8 and added a test suite with multi-byte fixtures, including emoji and characters outside the Basic Multilingual Plane.
- **Fonts.** A complete CJK font can exceed 10 MB. We used subsetting and `unicode-range` splitting so browsers fetch only the glyphs they need.
- **Search and sorting.** Chinese text has no spaces between words, so our default tokenizer produced useless search results. We integrated a dictionary-based segmenter and added pinyin support for sorting and lookup.
- **Layout.** Line-breaking rules differ, and our truncation logic that cut strings at a fixed byte length occasionally split a character in half. We switched to grapheme-aware truncation.

## Results

After rollout, p95 latency for users in mainland China fell from 2.4 seconds to 480 milliseconds. Error rates on long-lived connections dropped by roughly 70 percent, and search relevance complaints from Chinese-language users essentially disappeared.

## What we'd do differently

- **Start the compliance process earlier.** Filing timelines were the longest part of the project and ran in parallel with engineering far less than they should have.
- **Audit dependencies sooner.** The hidden third-party calls were the cheapest wins, and we could have found them months earlier.
- **Test from inside the network.** Synthetic monitoring from outside China told us very little. We now run probes from multiple in-region vantage points.

## What's next

We're extending the same pattern to other regions with distinct data and network constraints. The region-parameterized infrastructure and the text-handling test suite are both paying off beyond China.

If you've tackled a similar expansion, we'd love to hear what worked for you. And to our new users in China: 你好, 欢迎!
