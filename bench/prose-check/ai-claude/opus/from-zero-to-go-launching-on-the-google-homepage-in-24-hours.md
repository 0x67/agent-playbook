# From zero to Go: launching on the Google homepage in 24 hours

At 9:12 on a Tuesday morning, an email landed in our team channel. Our interactive holiday-card maker would be linked from the Google homepage, starting in 24 hours.

The excitement lasted about a minute. Then someone asked what we were all thinking: *"Can the renderer handle that?"*

It couldn't. Our prototype was a Python script on a single VM that took roughly 800 milliseconds to composite each card. That was fine for a few hundred users a day. It would not survive homepage traffic.

## The decision: rewrite the hot path

We had two options. We could put as many machines as possible behind the existing code, or we could rewrite the one piece that mattered. The rendering service was small, about 400 lines, so we chose to rewrite it.

Two of us had written Go on side projects, but nobody had shipped it to production. We picked it anyway, for four reasons:

- **The standard library already had what we needed.** `image`, `image/draw`, `image/png`, and `net/http` covered most of the service.
- **Concurrency is built in.** Every request gets its own goroutine without any extra work from us.
- **It deploys as one static binary.** There was no dependency tree to debug at 3 a.m.
- **It compiles fast.** On a 24-hour deadline, a quick edit-and-run loop is worth a lot.

## Hours 0–3: Shrink the problem

Before writing any code, we looked for ways to do less work. Users picked a background, a character, and a frame, then typed a name. The same inputs always produced the same image, so the output was **deterministic and cacheable**.

That led to the design:

1. Encode every card as a canonical URL, with sorted parameters and normalized text.
2. Make the renderer completely stateless.
3. Put a CDN in front with long cache lifetimes.

If popular combinations got rendered once and served from the edge thousands of times, the renderer only had to handle the long tail.

## Hours 3–11: Write the boring version

We loaded every asset into memory at startup. Each request then validated its parameters against an allowlist, composited the layers, drew the text, and streamed back a PNG:

```go
var encoder = png.Encoder{CompressionLevel: png.BestSpeed}

func renderCard(w http.ResponseWriter, r *http.Request) {
	spec, err := parseSpec(r.URL.Query())
	if err != nil {
		http.Error(w, "invalid card", http.StatusBadRequest)
		return
	}

	canvas := image.NewRGBA(cardBounds)
	for _, layer := range spec.Layers() {
		draw.Draw(canvas, cardBounds, assets[layer], image.Point{}, draw.Over)
	}
	drawName(canvas, spec.Name)

	w.Header().Set("Content-Type", "image/png")
	w.Header().Set("Cache-Control", "public, max-age=86400, immutable")
	encoder.Encode(w, canvas)
}
```

By hour 11 the whole service was under 300 lines. People new to Go often expect it to feel verbose. What we noticed instead was how little there was to hide behind: each line did one obvious thing.

## Hours 11–18: Break it on purpose

We pointed a load generator at a staging cluster and watched it struggle. Instead of guessing why, we turned on `net/http/pprof` and captured a CPU profile.

The profile surprised us. Compositing was cheap. **PNG compression was eating most of the CPU.** Switching the encoder to `BestSpeed` made files about 15% larger and encoding roughly three times faster, which was an easy trade. We also reused canvases through a `sync.Pool`, which brought garbage-collection pauses down noticeably.

The load test exposed failure modes too:

- **Unbounded input.** A 10,000-character name took a single request several seconds to render. We capped names at 40 characters.
- **Unbounded concurrency.** Under overload, every instance tried to render everything simultaneously and the latency of all requests collapsed together. We added a buffered-channel semaphore so that excess requests got a fast `503`. The frontend handled that `503` by showing a pre-rendered default card. A generic card is a far better experience than a spinner that never resolves.

## Hours 18–24: Make it boring

We spent the last stretch on operational work:

- Built dashboards for request rate, cache hit ratio, p99 latency, and 503 rate.
- Added a kill switch that sent every user to static cards.
- Deployed to three regions.
- Wrote a one-page runbook.
- Rehearsed a rollback.
- Split the night into sleep shifts.

## Launch

Traffic arrived as promised. The CDN hit ratio climbed above 90% within the first hour, and the renderers never went above about 40% CPU.

There was one incident. Users with names in some non-Latin scripts got cards full of empty boxes, because our font had no glyphs for those characters. We added a fallback font, rebuilt the binary, and rolled it out to every region in under five minutes. That was the moment a single static binary paid for itself.

## What we'd tell you

- **Make it cacheable before you make it fast.** The CDN did most of the work on launch day.
- **Profile; don't guess.** Our bottleneck was not where we expected it.
- **Bound everything:** input sizes, concurrency, and time.
- **Design the degraded experience on purpose.** A good fallback beats a perfect feature that times out.
- **A small language lowers the cost of being new.** We went from zero production Go to a homepage launch in a day, mostly because Go and its standard library left us so few decisions to make.

---

*The timeline, figures, and incidents above are illustrative. Replace them with your team's actual details before publishing.*
