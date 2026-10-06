# Math, and the closed set of sentence openers

A note, not a specification.
It starts the record for one question: should more kinds of inline node be allowed to open a sentence, math first among them, and if so, can a rules file add them?
Nothing here is decided.
Claims marked *measured* were run on 2026-10-06 against mdformat 1.0.0 and mdformat-dollarmath 0.0.5; the rest is argument.

______________________________________________________________________

## 1. Where the design stands

`DESIGN.md` §3.3 lets a sentence open, regardless of case, only with a code span, an image, an autolink, or a raw HTML segment that is nothing but tags.
Every other inline node a co-plugin adds, math, a wikilink, a footnote reference, is an atom for §3.2 and opens nothing.
Its text is not read through the capital test either, so `$X$` opens nothing just as `$x$` does.

The list is closed because an open one deletes text.
With mdformat-footnote loaded, a break before `[^x]: not a definition, just text.` puts a footnote definition at a line start, the second render pass reads it as one, and both notes' text is gone.
All four members of the hook-point review reproduced that (`DESIGN-REVIEW-HOOK-POINT-2026-10-06.md`, R9).

The cost is every sentence that opens with co-plugin syntax:

```
The bound holds. $x$ is positive for every input.
```

stays on one line.
The review measured that cost at no changed lines across its corpora, which were technical documentation.
Math-heavy prose, the kind `academic.toml` exists for, was not measured, so the cost there is unknown.

## 2. Can a rule add an opener?

**Not as a `[[rule]]`.**
A rule is consulted only at a gap after an ATerm terminator, matches the text of the words around the gap, and returns `no` or `allow`.
It cannot force a break, it never sees a node's type, and it is not consulted after `!` or `?`.
An opener is a property of the word after any terminator, so it is the wrong shape for the table.

**As a key of a rules file, yes, the way `lowercase_names` already is.**
`lowercase_names` lets a named lowercase word pass the capital test, and it is a file key rather than a rule for the same reasons (§4).
A second key could name node types that open a sentence:

```toml
schema       = 1
opener_types = ['math_inline']
```

The name is a placeholder of this note, not a decision.
It would compose like `lowercase_names`: every file in a composition contributes, a file can add types and none can take one away, and the default names none.
The recorder of §3.1 already knows each atom's node type, so the check costs a set lookup.

A text pattern instead of a node type, say `openers = '\$.*'`, would be more general and riskier: it reads atom text through a pattern, which is what the closed list was made to stop.
Node types are the narrower tool.

**The type names agree across the math plugins read.**
mdformat-dollarmath, mdformat-myst, mdformat-obsidian and mdformat-mkdocs's arithmatex support all render inline math as node type `math_inline` (read from their sources, not run, except dollarmath).

## 3. Is math safe to admit?

The danger an opener brings is not the opening itself but what a line start does to it.
Admitting a type must not let a break put block syntax, or a co-plugin's definition syntax, at the start of a line; §3.5's line-start rules would still apply to it.

*Measured,* with mdformat-dollarmath 0.0.5:

- A break before inline math, `It holds.` then `$x$ is positive.` on the next line, is render-equal to the unbroken paragraph.
- `$$x$$` inside a paragraph never reaches the plugin as inline: dollarmath already makes it a separate display block, with or without this plugin, so a break before it cannot change anything.

So for dollarmath, admitting `math_inline` looks safe.
That is one plugin with default settings; the others, and dollarmath's options, were not run.

## 4. What would have to happen first

1. Measure the cost on math-heavy Markdown: how many sentences open with inline math, and how many of those the closed list holds back.
   If it is small there too, the closed list stays and this note is the record of why.
2. For each math plugin worth supporting, run the gate's line-start and render-equality rows with a break before `math_inline` at a line start, in both load orders.
3. Decide between a file key such as `opener_types` and a fixed list in code.
   A fixed list is simpler but makes the spec name co-plugins; a key keeps that knowledge in rules files, where `academic.toml` could carry it.

The mdformat-gfm bare URL is the other candidate on record: measured at 24 gaps in about 150,000 paragraphs, judged safe by reasoning, and deferred (`FUTURE-WORK.md`).
