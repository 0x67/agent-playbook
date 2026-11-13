# Code of Conduct Updates

When we first wrote our engineering Code of Conduct, it fit on a single page. That was intentional. We wanted something people would actually read, remember, and use. Over the past few years, our team has grown, our work has become more distributed, and the ways we collaborate have changed. Code review happens asynchronously across time zones, incident response involves dozens of people in a shared channel, and AI-assisted tooling now sits in many of our workflows. Our Code of Conduct needed to keep up.

Today we're sharing what changed, why we changed it, and how we plan to keep it a living document.

## Why Now?

A code of conduct that never changes usually means one of two things: either it's perfect, or nobody is looking at it. We suspected the latter.

Earlier this year, we ran an anonymous survey and held a series of listening sessions across engineering. Three themes came up repeatedly:

1. **Feedback tone in code review.** People wanted high standards without the sharp edges. Terse comments that felt neutral to the author of a comment could land as dismissive for the recipient.
2. **Clarity during incidents.** Under pressure, blame sneaks in. Engineers told us they weren't always sure what "blameless" meant in practice.
3. **Reporting felt unclear.** Many people said they weren't sure where to go if something felt wrong, or what would happen afterward.

These weren't surprising, but seeing them in writing made them hard to ignore.

## What's Changed

### 1. Code review expectations are now explicit

We added a section on review etiquette that describes behaviors rather than abstract ideals. A few highlights:

- **Critique the code, not the person.** Say "this function has three responsibilities" rather than "you wrote this confusingly."
- **Explain the why.** A comment like "use a map here" is more useful with a sentence about the performance or readability reason behind it.
- **Label your intent.** We encourage prefixes such as `nit:`, `question:`, or `blocking:` so authors know what requires action.
- **Respond within reason.** Reviewers should acknowledge requests promptly, and authors should assume good faith while waiting.

### 2. Blameless incident culture, defined

Instead of simply stating that we're blameless, we now describe what that looks like. During an incident, we ask "what conditions allowed this to happen?" rather than "who did this?" Postmortems focus on systems, processes, and missing safeguards. We also added guidance for incident channels: keep speculation labeled as speculation, avoid pile-ons, and thank people who surface bad news early.

### 3. Guidance for AI-assisted work

Many of us now use AI tools to write code, draft documentation, and summarize discussions. The updated Code of Conduct says that **you are accountable for what you ship**, regardless of how it was produced. That means reviewing generated code before submitting it, never pasting confidential data or customer information into unapproved tools, and being honest with teammates when a substantial piece of work was machine-generated. We're not trying to discourage these tools. We're trying to make sure trust stays intact.

### 4. A clearer reporting path

We rewrote the reporting section to answer the questions people actually asked: Who can I contact? Can I report anonymously? What happens next? There are now multiple channels, including your manager, a designated engineering ombudsperson, and an anonymous form. We've also committed to acknowledging every report within two business days and to protecting anyone who raises a concern in good faith from retaliation.

### 5. Plainer language

We removed legalistic phrasing and replaced it with direct language. If a sentence required a lawyer to interpret it, we rewrote it. A code of conduct should be understood by a new hire on their first day.

## How We Made These Changes

The updates were drafted by a working group of engineers from different teams, levels, and regions, with support from People Operations. We shared a draft internally for two weeks of open comment and received over 150 suggestions. Roughly a third resulted in edits. Some of the most valuable feedback came from newer employees who pointed out assumptions that longtime staff no longer noticed.

## What Happens Next

A document only matters if people live it. In the coming weeks, we'll be:

- Running short, scenario-based workshops in each engineering group.
- Adding a summary of the Code of Conduct to our onboarding materials.
- Linking relevant guidance directly from our pull request templates and incident runbooks.

We'll also review the Code of Conduct every six months. Changes will be tracked in a public changelog within the document so anyone can see what was modified and why.

## Share Your Thoughts

This is a living document, and it works best when it reflects the people who use it. If you have questions, suggestions, or disagreements, bring them to your team lead, the working group, or the anonymous feedback form. We'd rather hear a hard truth than have a policy that looks good on paper.

Good engineering is about more than shipping reliable systems. It's about building them together, in a way that makes people want to keep doing the work.
