---
name: prose-check
description: Checks written text for AI-like patterns with local linters, at the word, sentence and paragraph level and across sets of UI strings. Runs the vale-ai-tells rules through Vale, or through a built-in Python port when Vale is missing, plus checks for repeated openings and endings, colon reveals, short closers, and one template stamped across many messages. Use when asked to check, review or audit writing for AI tells, after drafting a doc, PR body, Jira comment, Slack message or UI copy, or on /prose-check. Runs offline, so no text leaves the machine or sandbox.
---

# Prose check

The checker only flags. Fixing is a rewrite under the humanizer rules: keep every fact and add none.

## Run it

1. Files: `sh "${CLAUDE_SKILL_DIR}/scripts/run.sh" prose_check.py FILE...`
   - `.md`, `.mdx` and `.txt` are checked as prose.
   - `.html`, `.htm`, `.tsx`, `.jsx`, `.vue` and `.svelte` have their UI strings extracted first, then each string and the whole set are checked.
   - `.pptx` decks give their slide text and speaker notes, numbered by slide, and `.json` files give every string of three or more words, which covers slide and document data.
2. A draft that is not in a file, such as a Jira comment, a Slack message or text the user pasted: write it to a scratch `.md` file and pass that path, or pipe it in with `-` as the path.
3. In claude.ai, `${CLAUDE_SKILL_DIR}` is not filled in. Run `python3 scripts/prose_check.py` from this skill's folder with code execution; it uses the Python port there, with the `regex` module if the sandbox has it.
4. `--engine lite` forces the Python port and `--engine vale` requires Vale. `--json` prints machine-readable output, and the exit code is 1 when anything is flagged.

`run.sh` uses `python3` when it already has the `regex` module, then `uv` with the pinned `regex`, then plain `python3`. The Python port runs the 132 existence, substitution and occurrence rules and skips the 5 sequence rules, which need Vale's part-of-speech tagger. Without `regex`, 14 lookbehind patterns are skipped as well. On the files it was compared on, it reports 97% of Vale's findings.

The plugin's hooks also run this check without being asked. After a Write or Edit to a prose or UI file, the findings in the written lines come back for revision. Before a Slack, Jira, Confluence, Gmail, Notion, Claude Docs, Google Docs or Google Slides send or write, and before a `git commit` or `gh pr`/`gh issue` command with a message body, a flagged message is stopped once with its findings; sending the identical text again goes through, which is the way to send text the user wrote. Before an Artifact publish, the local files are checked, and the publish stops only for findings that file has not shown before.

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
