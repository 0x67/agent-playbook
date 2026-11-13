# prose-check corpus benchmark

**What it measures**

1. Findings per 1,000 words from Vale and from the Python port of `prose-check`, plus the cross-sentence checks, on human and Claude-written text.
2. Port parity: the share of Vale's non-sequence rule findings that the port also reports.
3. Speed: seconds per 100,000 words for each engine.
4. Separation: the AUC of a per-document score (findings per 100 words), which is the chance that a random AI document scores above a random human one.

Results are in `results.json` and summarized in [docs/benchmarks.md](../../docs/benchmarks.md#large-corpora).

**What is committed and what is fetched**

1. `blogs/<platform>.json`: URL manifests for the engineering blogs of discord, notion, slack, spotify and stripe. Each lists posts published before 2022-11-30 with url, date, title and the file name to write. The posts are copyrighted by their publishers, so only URLs are committed.
2. `ai-claude/{sonnet,opus}`: 80 posts written by Claude Sonnet 5.5 and Opus 5.5. This is our own output and is committed. Generation cost $3.93 (see `ai-claude/costs.json`).
3. Fetched by `fetch-open.py`, not committed:
   - The Rust Book at the last commit of 2021 (MIT or Apache-2.0).
   - The Go blog at the last commit of 2021 (CC BY 4.0).
   - HC3 human and ChatGPT answers at a pinned revision, checked by sha256 (CC BY-SA 4.0).
   - The vale-ai-tells v1.37.0 fixtures (MIT).

**Excluded platforms**

1. Netflix: serves a Cloudflare challenge, and its robots.txt disallows AI crawlers by name.
2. Dropbox: AWS WAF began challenging after 33 pages.
3. Uber: the live site serves a bot challenge (def.uber.com/challenge).
4. Cloudflare: no manifest exists. The URL scan had not finished, so the platform is not in this run.

**Rebuild steps**

The runs used Vale 3.26.0, `regex` 2026.11.9 (installed by `run.sh` through `uv`) and Python 3.13. Put `vale` and `uv` on `PATH` first.

1. Fetch the open corpora: `python3 -I bench/prose-check/fetch-open.py CORPUS_DIR`. This writes `human/`, `hc3/` and `fixtures/`.
2. Rebuild the blog corpora at one request per second, cached: `python3 -I bench/prose-check/fetch-blogs.py CORPUS_DIR/blogs discord notion slack spotify stripe`.
3. Optional: regenerate the Claude posts with `bench/prose-check/generate-ai.py CORPUS_DIR/human/go-blog bench/prose-check/ai-claude`. The committed 80 posts cost $3.93, and existing posts are kept. The committed corpus already works, so skip this step to reproduce the results.
4. Run `sh bench/prose-check/run.sh CORPUS_DIR`. It takes a few minutes, prints the table and the AUC lines, and writes `results.json`.
