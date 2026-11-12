---
name: prose-check
description: Checks written text for AI-like patterns with local linters, at the word, sentence and paragraph level and across sets of UI strings. Runs the vale-ai-tells rules through Vale, or through a built-in Python port when Vale is missing, plus checks for repeated openings and endings, colon reveals, short closers, and one template stamped across many messages. Use when asked to check, review or audit writing for AI tells, after drafting a doc, PR body, Jira comment, Slack message or UI copy, or on /prose-check. Runs offline, so no text leaves the machine or sandbox.
---

# Prose check

The checker only flags. Fixing is a rewrite under the humanizer rules: keep every fact and add none.

## Run it

1. Files: `python3 "${CLAUDE_SKILL_DIR}/scripts/prose_check.py" FILE...`
   - `.md`, `.mdx` and `.txt` are checked as prose.
   - `.html`, `.htm`, `.tsx`, `.jsx`, `.vue` and `.svelte` have their UI strings extracted first, then each string and the whole set are checked.
2. A draft that is not in a file, such as a Jira comment, a Slack message or text the user pasted: write it to a scratch `.md` file and pass that path, or pipe it in with `-` as the path.
3. In claude.ai, `${CLAUDE_SKILL_DIR}` is not filled in. Run `scripts/prose_check.py` from this skill's folder with code execution; it uses the Python port there.
4. `--engine lite` forces the Python port and `--engine vale` requires Vale. `--json` prints machine-readable output, and the exit code is 1 when anything is flagged.

The Python port runs the 132 existence, substitution and occurrence rules and skips the 5 sequence rules, which need Vale's part-of-speech tagger. On the files it was compared on, it reports 97% of Vale's findings.

## Read the findings

Each line is `L<line> <rule>: <message>`.

1. CamelCase rules come from vale-ai-tells and each catches one pattern, such as `NegatedSubject` ("Nothing was written") or `ContrastiveFormulas` ("not X, but Y"). The message says how to fix it.
2. snake_case rules come from the cross-sentence checks:
   - `repeated_openings`, `repeated_endings`, `repeated_sentences`, `same_sentence_shape`: one template stamped across many strings or sentences.
   - `colon_reveals`: a short label and a colon in front of a full sentence ("Draft: these bars are set aside").
   - `contrasts`: "not X but Y" and ", not Y" tails.
   - `anaphora_runs`, `short_closers`, `flat_rhythm`: paragraph shape.

## Fix and report

1. Rewrite the flagged lines with the humanizer rules.
2. A finding can stay when the pattern fits the text, such as a real three-step procedure or a UI label that needs its colon. List each finding you kept, with the reason.
3. Run the check again on the edited text and report what remains, grouped as words, sentences, and paragraphs or sets of strings.
