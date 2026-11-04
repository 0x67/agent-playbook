Humanizer rules for written output (condensed from skill `humanizer` v3.1.0). They apply to code comments, doc comments, docs, specs, PR bodies, commit messages, Jira comments, Slack and email drafts, and published artifacts. Chat replies to the user are out of scope.

Load the full skill (Skill tool, `humanizer:humanizer`, embedded mode) before writing a PR body, doc, spec, Jira comment, or any prose longer than a short paragraph. Code comments and one-line commit headers can follow this card alone.

Cut on one sighting:
1. Not X but Y contrasts, also split across sentences ("This does not mean X. It means Y.") and clipped tails (", no guessing"). State the point.
2. One-line closers that restate the paragraph, rows of fragments, ALL CAPS emphasis.
3. Sayings that sound deep: "the real question is", "at its core", "X is the language of Y".
4. Staged run-ups: "Let's dive in", "Here's the thing", "Honestly?".
5. Arguing with no one: "To be clear", "I'm not saying", "A tempting approach would be".

Fix when several show up together:
6. Triads by habit. Keep three items only when there are three.
7. The same sentence opening several times in a row.
8. Em dashes and en dashes: none, ever. Use a period, comma, colon, or parentheses. Code, paths, and URLs are untouched.
9. Stacked qualifiers ("could potentially").
10. Hyphenated pairs after the noun ("the doc is well-documented").
11. Hidden actors and missing subjects.
12. Stock words: actually, additionally, align with, crucial, delve, enhance, garner, highlight (verb), intricate, key (adjective), landscape, meticulous, pivotal, quietly, robust (figurative), showcase, testament, underscore, valuable, vibrant.
13. Inflated significance ("marks a pivotal moment"), vague links ("associated with"), -ing riders ("ensuring", "highlighting"), sales language, unnamed experts, "serves as" or "boasts" where is or has fits.
14. Bold labels on every list item, Title Case headings, emoji or arrow decoration, curly quotes.
15. Chatbot residue ("I hope this helps", "Let me know"), knowledge-limit disclaimers, a first sentence that repeats its heading, text about the document itself ("this function was added to replace...").
16. In replies (PR review answers, Jira replies), lead with the decision and skip background the reader already has.

Keep every fact, identifier, path, number, type, and error text. Never rewrite code, commands, paths, or data. The user's formats win over these patterns: docs keep bold section headings with numbered lists, commits are one header line, and no em dashes. A writing sample from the user overrides everything here.
