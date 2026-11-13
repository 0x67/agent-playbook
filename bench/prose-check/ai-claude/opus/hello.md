# Hello, 中国!

Every programmer's first program prints "Hello, World!" It's a good first program because almost nothing can go wrong. This year our team learned that changing one word, so the program prints "Hello, 中国!", exposes a surprising number of assumptions in a mature codebase.

In the spring we began preparing our product for users in mainland China. We expected translation to be most of the work. It turned out to be the easy part. Below are the bugs we found, roughly in the order they bit us, and what we changed.

## 1. Bytes are not characters

The first report came from QA. A CSV export opened in Excel displayed `Hello, ä¸­å›½!`. The file was valid UTF-8. But when a CSV has no byte order mark, Excel guesses its encoding from the system locale, and on a Western Windows machine it guesses Windows-1252. Each three-byte UTF-8 sequence for 中 and 国 was rendered as three separate Latin characters.

The fix was one line: we now prepend a UTF-8 byte order mark (`\uFEFF`) to CSV exports. The bug also prompted an audit of every place we write bytes to the outside world: file exports, email headers, webhook payloads, and a legacy PDF generator that had never embedded a CJK font.

## 2. Length is ambiguous

Our username field allowed 20 characters. The frontend checked `value.length`, and the backend checked byte length against a `VARCHAR` column. For ASCII, these agree. For Chinese, they don't: `"中国".length` is 2 in JavaScript, but the same string is 6 bytes in UTF-8.

Characters outside the Basic Multilingual Plane make it worse. 𠮷, a variant of 吉 that appears in personal names, is stored as a surrogate pair, so JavaScript reports a length of 2 for that single character. A few of our tables also still used MySQL's legacy `utf8` charset, which supports only three-byte sequences and rejected four-byte input.

We made three changes:

- Every text column now uses `utf8mb4`.
- Limits are defined in user-perceived characters (grapheme clusters, counted with `Intl.Segmenter`) and enforced the same way on both ends.
- Our truncation helper now cuts on grapheme boundaries instead of slicing raw indices. The old approach sometimes left half of a surrogate pair, which rendered as �.

## 3. Enter doesn't always mean "submit"

Most Chinese users type with an input method editor (IME). They type pinyin, such as `zhongguo`, then pick 中国 from a candidate list, often confirming with Enter. Our search box fired a query on Enter in `keydown`, so users ended up searching for half-composed pinyin.

The fix is to ignore key events while composition is in progress:

```js
input.addEventListener('keydown', (e) => {
  if (e.isComposing || e.keyCode === 229) return;
  if (e.key === 'Enter') submitSearch();
});
```

`keyCode` is deprecated, but the `229` check covers browsers that fire `compositionend` before the final `keydown`. We added the fix to our shared input component, so every form gets it automatically.

## 4. The same character, different glyphs

Because of Unicode's Han unification, Chinese, Japanese, and Korean share many code points even where their typographic conventions differ. Without a language hint, a browser may render Chinese text with a Japanese font. A native reader can still read it, but it looks subtly wrong. We fixed this by setting `lang="zh-CN"` on the document root and specifying a proper font stack: `"PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif`.

## 5. Sorting and searching

By default, `Array.prototype.sort()` orders strings by UTF-16 code units, which means nothing to a Chinese reader. Switching to `Intl.Collator('zh-CN')` gives pinyin-based ordering that matches what users expect.

Search had a deeper problem. Our full-text index tokenized on whitespace and punctuation, but written Chinese doesn't put spaces between words, so an entire sentence became a single token. We switched those fields to a CJK-aware analyzer that indexes overlapping two-character bigrams. It's less precise than true word segmentation, but it finds what users are looking for.

## What we'd tell our past selves

None of these bugs were exotic. Each came from an assumption: one byte per character, spaces between words, Enter means "done." Those assumptions held for years because our test data never challenged them.

The most effective change wasn't any single fix. It was adding strings like `Hello, 中国!`, `𠮷`, and a handful of emoji to our shared test fixtures, and running pseudo-localized builds in CI. Now the next assumption breaks in a pull request instead of in production.

If your product has only ever said "Hello, World!", try saying hello to someone else. Your codebase will show you what it assumed.
