# mdformat-sentence

A design for a small mdformat plugin.

This document is written one sentence per line, which is the output this plugin produces.
It is the dogfood, and it is also the argument.
Read it at any window width and the line breaks do not move.

[Semantic Line Breaks](https://sembr.org) is a convention for breaking source lines at meaning boundaries, so that a diff shows what changed rather than where the text reflowed.
Its specification gives thirteen rules at RFC 2119 levels of obligation.
This plugin takes the sentence rule and nothing below it, which §5 sets out against the full list.

______________________________________________________________________

## 1. What this is, and what it is not

**The whole promise, in one sentence:** a line break after every sentence, nowhere else, ever, at any width.

**The output does not depend on `--wrap`.**
Line positions are a pure function of the text.
Adding a word to the second sentence of a paragraph changes exactly the line that word is on, and no other line, at any width, forever.
That is the diff-stability property Semantic Line Breaks exists for, and no width-driven implementation can offer it — as soon as a break position is chosen by "the rightmost candidate that still fits in 80 columns", an edit upstream can change which candidate wins and cascade down the paragraph.

**Absent by construction, not defaulted off.**
This is the canonical list, and every later section that declines something cites it rather than re-arguing the case.

- **Width, column and line-length.**
  Not a default, not an option, not a tie-breaker.
  A 400-character sentence occupies a 400-character line.
- **Word lists and clause machinery.**
  No conjunctions, no clause punctuation, no break words, no parenthetical strategy, no merge pass and no minimum line length.
- **Spec rules 5 and 12.**
  Rule 12 is a line-length recommendation and there is no length here; rule 5 cannot be done without a parser, and §5.1 makes that case.
  This is a strict subset of correct Semantic Line Breaks, not a competing interpretation of them.

**Who it is for, and what the shipped default is tuned for are different questions.**
The plugin serves any Markdown whose author wants one sentence per line, and research papers are squarely inside that.
Only the shipped *default rule set* is narrow: it is tuned for English prose of the kind this repository and its corpus are made of, because that is what there was to measure against (§3.3).
An audience whose abbreviations differ does not need a different plugin, it needs a different rules file, and §4 ships a second one for academic prose.

The whole configuration surface is one option and one rules file, both about sentence *detection* (§4).

## 2. Name, packaging and the seam

Distribution `mdformat-sentence`, module `mdformat_sentence`, entry-point id `sentence`.
The name was unregistered on PyPI as of 2026-09-12, verified against the JSON API, as was the plural `mdformat-sentences`.
Singular over plural is a coin flip in this ecosystem rather than a convention: `mdformat-footnote`, `mdformat-admon`, `mdformat-deflist` and `mdformat-wikilink` are singular, `mdformat-tables`, `mdformat-simple-breaks` and `mdformat-gfm-alerts` are plural.

```toml
[project.entry-points."mdformat.parser_extension"]
sentence = "mdformat_sentence"
```

Dependencies: mdformat only, `>=1.0,<2`.
`requires-python >= 3.10`, because mdformat 1.0.0 declares it.
License MIT, matching mdformat and every plugin in its curated list.

Every fact in §2.1 to §2.4 was verified by execution against mdformat 1.0.0.

### 2.1 The entry point id, and why it is the binding constraint

The id is what `--extensions` accepts, what keys `[plugin.sentence]` in `.mdformat.toml`, and what `mdformat.text(..., extensions={"sentence"})` names.
It follows the ecosystem convention of the distribution name with underscores, as `mdformat-simple-breaks` registers `simple_breaks` and `mdformat-frontmatter` registers `frontmatter`.

**An id collision is silent.**
mdformat loads plugins with `loaded_ifaces[ep.name] = ep.load()`, a plain dict assignment in `mdformat/plugins.py`, so two distributions registering the same id overwrite each other with no warning and no error.
The id, not the PyPI name, is the identifier that has to be unique.
`sentence` does not collide with `mdformat-sembr`'s `sembr`, and both can be installed together.

**`--extensions` is a whitelist, not an addition.**
`enabled_parserplugins` is *all* installed plugins when `--extensions` is absent, and *only* the named ones when it is present.
So `--extensions sentence` silently disables GFM.
That is the trap behind §6.2's rule that every baseline must name `extensions=set()` explicitly, and it is worth a line in the README.

### 2.2 The hook point is `POSTPROCESSORS["inline"]`

Not a `paragraph` renderer override, and not a `paragraph` postprocessor.

The relevant mdformat 1.0.0 pipeline, in order, from `mdformat/renderer/_context.py`:

1. `text()` escapes inline markup, then, if `context.do_wrap` and the node is inside a paragraph, replaces every run of `[ \t\n]+` with `WRAP_POINT` (`\x00`).
1. `softbreak()` becomes `WRAP_POINT`.
   `hardbreak()` becomes a backslash *and* a newline, glued to the preceding segment with no wrap point between them.
1. `link()` and `image()` replace every interior `WRAP_POINT` with a space, so a whole link or image is one unbreakable atom.
1. **The plugin runs here**, because `RenderTreeNode.render` applies postprocessors immediately after the renderer for that node type.
1. `paragraph()` splits the inline text on `\n`, word-wraps each section independently through `textwrap`, then walks every resulting line and escapes anything that would become block syntax at line start.
1. `blockquote()`, `bullet_list()` and `ordered_list()` prefix and indent every line, with `context.indented()` keeping `env["indent_width"]` accurate.

So a plugin at this seam turns selected `WRAP_POINT`s into `\n`, and §3.4 narrows the job further: this one turns every gap it does not break into a literal space as well.

Guard: return unchanged unless `node.parent is not None and node.parent.type == "paragraph"`.
An inline node's parent is the block that owns it, so the test is exact rather than heuristic.
No inline node with a null parent is reachable in mdformat 1.0.0, so the first conjunct is defensive, and it is how `mdformat-gfm` writes the same guard.

Why this seam and no other:

- A `WRAP_POINT` is mdformat's own assertion that the position may become a newline without changing the render, so breaking only there makes spec rule 2 structural rather than something this plugin has to police.
- Breaks inserted here become sections in step 5, so line-start escaping and blockquote and list indentation apply to them for free.
- Postprocessors chain, so this composes with other plugins instead of fighting them over the `paragraph` renderer.
- `CHANGES_AST = False` is correct, and `_cli.py` gates `--validate` on `not changes_ast` while `validate` defaults to `True`, so declaring it means mdformat checks the render-equality invariant on our behalf.
  Three caveats: `--check` never reaches the validation branch at all, because `_cli.py` compares strings and returns first; `changes_ast` is OR-ed across every enabled plugin, so one plugin declaring `True` silently disables validation for all of them; and the Python API never validates.
  It is a strong default rather than a guarantee, and it is blind to the whitespace class regardless (§3.5).
- Hooking `paragraph` instead, as `mdformat-sembr` does, puts the plugin downstream of wrapping and line-start escaping, so it has to re-derive what this seam gives it for free.

**No `WRAP_POINT` survives this plugin.**
§3.4 resolves every gap to a newline or a literal space, so mdformat's own word wrap is left with nothing to act on, and no part of this design may assume that it will act.

### 2.3 Four facts about the seam

**`mdformat.text()` renders twice.**
`_api.py` re-renders its own output whenever `wrap != "keep"`, because escaping depends on wrapping.
A non-idempotent plugin therefore produces visibly unstable output rather than a subtle drift, and the plugin must tolerate seeing its own output as input.
It does, for the reason given in §3.4.

**`WRAP_POINT` and `PRESERVE_CHAR` are the same byte, `\x00`.**
They never collide because they are alive in disjoint phases: `PRESERVE_CHAR` exists only inside `_prepare_wrap`, which runs in step 5, after us.
At plugin time every `\x00` is unambiguously a wrap point.

**No literal `\x00` can reach the plugin from the source.**
CommonMark requires U+0000 to be replaced with U+FFFD and markdown-it does so, so parsing `"a\x00b"` yields the content `'a\ufffdb'`.
That is what makes `\x00` safe to use as a delimiter.

**A run of consecutive `WRAP_POINT`s collapses to one space.**
`_prepare_wrap`'s regex matches `\x00+` as a unit, so `re.compile(r"\x00+")` is the correct splitter and §3.1's segmentation loses nothing by using it.

### 2.4 Only the argparse `dest` is namespaced

mdformat builds each plugin's argument group and then rewrites the destinations, in `mdformat/_cli.py`:

```python
group = parser.add_argument_group(title=f"{plugin_id} plugin")
plugin.add_cli_argument_group(group)
for action in group._group_actions:
    action.dest = f"plugin.{plugin_id}.{action.dest}"
```

So `dest="require_sentence_capital"` lands at `options["mdformat"]["plugin"]["sentence"]["require_sentence_capital"]`, and the visible flag text is whatever string the plugin passes to `add_argument`.
That is why §4 can spell the flags short, and why changing the CLI prefix later costs nothing else.

**`default` must be `None` or `argparse.SUPPRESS`.**
The same loop emits a `DeprecationWarning` otherwise, warning that the plugin's default will always override any value configured in TOML.
A plugin that writes `action="store_false", default=True` silently defeats its own TOML config.
Use `action="store_const", const=False, default=None` and resolve the default inside the plugin rather than in argparse.

### 2.5 The three wrap modes

| `--wrap` | `do_wrap` | behavior |
| --- | --- | --- |
| `keep` (mdformat's default) | `False` | **Inert.** No wrap points exist, so there is nothing to act on. |
| `no` | `True` | Sentence per line. The intended mode. |
| any integer | `True` | **Identical output to `no`.** The width is deliberately not honored. |

The third row is the surprising one and it is deliberate.
A user who passes `--wrap 80` alongside this plugin is asking for two incompatible things, and this plugin resolves the conflict in favor of its own promise rather than silently producing something that is neither.
§3.4 explains the mechanism, §6.1 makes it a test, and the README must say it in the first paragraph.

`do_wrap` is `isinstance(wrap_mode, int) or wrap_mode == "no"`, which is what makes the first row inert and the third row indistinguishable from the second.

**The default is the inert row, and the intended row is destructive.**
This is the most surprising thing about installing the plugin and it belongs in the README as well as here.

`keep` is mdformat's default, and mdformat's own documentation gives hand-written Semantic Line Breaks as the reason it is the default.
So the out-of-the-box experience of installing this plugin is that nothing happens, and a user has to set `wrap = "no"` before it does anything at all.

Setting it discards every line break the author made by hand.
Under `--wrap no` mdformat collapses each paragraph to a single line before this plugin sees it, so a paragraph a writer had broken at three clause boundaries arrives as one line and leaves broken at sentences only.
Verified by execution against mdformat 1.0.0, with no plugin installed: the collapse is mdformat's, not ours, but the mode is the one this plugin asks for.
A writer who already hand-writes full Semantic Line Breaks therefore loses rules 5 and 6 the moment they adopt this plugin, and the only mode that keeps their work is the one in which the plugin does nothing.
That is a real cost, it is not recoverable from the output, and it must be said before someone runs the formatter over a corpus they hand-broke.

**The plugin warns when it was asked for by name and given a mode it cannot act in.**
It stays silent on the default configuration, because warning there would fire constantly for people doing nothing wrong.
It does warn when `--extensions` explicitly names it alongside a wrap mode that makes it inert, which is closer to a contradiction: the user asked for this plugin by name and for a configuration in which it can do nothing.

The signal is available and the test is one condition.
`DEFAULT_OPTS["extensions"]` is `None`, so a non-`None` `options["mdformat"]["extensions"]` means someone typed the flag:

```python
ext = context.options["mdformat"].get("extensions")
if ext is not None and "sentence" in ext and not context.do_wrap:
    LOGGER.warning("mdformat-sentence does nothing under --wrap keep; use --wrap no")
```

`mdformat.renderer.LOGGER` is the channel.
`_cli.py` attaches a handler that prefixes `Warning: ` and writes to stderr, and that handler is CLI-only, but a library caller is not silent: with no handler configured, `logging.lastResort` writes the message to stderr unprefixed.
Verified by execution.

**This warning is nonetheless a CLI and TOML feature, because its guard cannot be true anywhere else.**
`mdformat.text(md, extensions={"sentence"})` passes the set as its own argument to `build_mdit` and never writes it into `options["mdformat"]`, so `.get("extensions")` is `None` for every library caller, however explicitly they named the plugin.
Measured in `notes/experiments/wrapkeep.py`.
The paragraph above is therefore about where mdformat's warnings land in general, not about a message this plugin can actually deliver to an API caller.

One thing the implementation must handle, and one that looks like a second and is not.
It fires per paragraph, not per file, so it needs a once-per-render latch rather than one warning per inline node.
§2.3's double render does *not* double it: the guard above is `not context.do_wrap`, true only under `keep`, and `_api.py` re-renders only when `wrap != "keep"`, so the pass that would repeat a warning is never the pass that raises this one.
Measured in `notes/experiments/wraparg.py` §4: three paragraphs give three seam calls under `--wrap keep` and six under `--wrap no`, and it is only the three that can warn.

**What the plugin cannot see is whether `keep` was chosen or merely defaulted.**
`_cli.py` builds `{**DEFAULT_OPTS, **toml_opts, **cli_core_opts}` and argparse drops unset values, so an omitted `--wrap`, an explicit `--wrap keep`, and `wrap = "keep"` in TOML all arrive identical.
Only `mdformat.text()` leaks the difference, because `build_mdit` assigns the caller's mapping with no defaults merged and the key is simply absent.
CI runs the CLI, so the warning keys off `--extensions` rather than off wrap.

______________________________________________________________________

## 3. Algorithm

Normative.

### 3.1 Segmentation

```
for each section in inline_text.split("\n"):     # hard breaks; newlines inside inline HTML
    segs  = re.split(r"\x00+", section)
    state = scan(segs)                            # §3.3's cross-segment facts
    emit  = [segs[0]]
    for i in range(len(segs) - 1):
        emit.append("\n" if is_sentence_break(segs, i, state) else " ")
        emit.append(segs[i + 1])
    yield "".join(emit)
join sections with "\n"
```

Three things about that loop carry the whole design.

**Segments are the atoms and gaps are the only legal break positions.**
No other position is ever a break.
An authored soft line break is not one of them either: `text()` turns it into a wrap point like any other space (§2.2), so it arrives here as a gap and not as a section boundary.
`node.children` still marks it as a `softbreak`, so keeping it is mechanically possible; this design declines to (§2.5), and `notes/PRESERVE-MODE.md` records the alternatives and why an opt-in add-only mode is the one that survives.

**`scan` also reads the node, for type and nothing else.**
It walks `node.children`, renders each through `child.render(context)` and accumulates lengths, which gives the start offset and type of every child in `inline_text`; the sum equals `len(inline_text)` exactly, and a mismatch is a §3.6 failure.
That is what §3.3's opaque-atom check reads, since whether a segment begins a code span, an image or an autolink is a fact about a node rather than about text.
Child offsets add type information at existing positions and never add a position.
mdformat has already collapsed each link, image and code span into a single segment with literal interior spaces, so punctuation cannot detach from its token — `Lorem (ipsum sit). Dolor amet.` segments as `['Lorem', '(ipsum', 'sit).', 'Dolor', 'amet.']` and `sit).` is one atom.

**Every gap that is not a sentence break becomes a literal space, never a wrap point.**
Call this *pinning*, applied to every gap without exception.
A literal space is carried through `textwrap` as a preserved character and restored verbatim, so a pinned gap is unbreakable by mdformat's own word wrap as well as by us.
That single decision is what makes the output width-independent, and it is why this plugin emits no `\x00` at all.

**`is_sentence_break` sees the whole segment list.**
It cannot be a function of two adjacent segments, for the reasons in §3.3: bracket depth accumulates from the start of the section, the French closer rule looks one segment back, and the opener rule defers forward.
`scan` computes those once per section.

### 3.2 Masking

Within a segment, find the spans below and discard them, then count what is left: masking yields a number per segment, not a string.
The number is that segment's bracket delta over the unmasked remainder, `[` and `(` counting +1 and `]` and `)` counting -1.
The patterns, verified by execution against the eleven forms below the block:

```
code span            (?<!\\)(?<!`)(`+)(?!`)(?:[^`]|`(?!\1(?!`)))*?(?<!`)\1(?!`)
link/image dest      \[(?:[^\[\]]|\[[^\[\]]*\])*\]
                     \((?:[^()\\\s]|\\.|\((?:[^()\\]|\\.)*\))*(?:\s+"[^"]*")?\)
reference label      \[(?:[^\[\]]|\[[^\[\]]*\])*\]\[[^\]]*\]
autolink / raw HTML  (?<!\\)<(?:[/!?]?[A-Za-z][^<>]*
                     |[A-Za-z][A-Za-z0-9+.\-]*:[^<>\s]*|[^<>\s@]+@[^<>\s]+)>
```

Each pattern is one line; the link-destination and autolink patterns are split above only to fit the page.
The eleven forms they were checked against are `[t](u)`, `![t](u)`, `[![t](u)](v)`, `[![t](u)][r]`, `[t](u/a_(b))`, `[t](u "title")`, `[t][r]`, `[t]`, `[a [b] c](u)`, two links in one segment, and `` `code` ``.
Each contributes a delta of zero, which is the only property the depth counter needs, but not every one masks away completely: eight do, `![t](u)` leaves a bare `!`, two links in one segment leave the text between them, and `[t]` matches no pattern and survives whole, balanced.
A second consumer of masking would have to handle those three residues itself.

Masking has exactly one consumer here: bracket-depth counting (§3.3), where an unmasked `)` inside a URL drives depth negative and corrupts every later gap in the section.
The two link patterns start at the opening `[`, not at the `]`, and that is load-bearing rather than cosmetic: masking only `](dest)` leaves the link's `[` counted with nothing left to close it, so depth never returns to zero and every gap after the first link in a section is wrongly held to be inside brackets.
Masking the whole link is what makes §3.3's discriminator — a complete bracket group within one segment is link syntax — true of the mechanism and not just of the intent.
The link-text part admits one level of nested brackets, and that is not decoration: `[![badge](img)](target)` is the ordinary badge idiom, and a link-text pattern of `[^\]]*` stops at the image's `]`, masks `[![badge](img)` and leaves a bare `](target)` behind, which drives depth below zero and puts every following gap one level too shallow — so the next prose citation is read as unbracketed and split.
**Depth is also clamped at zero.**
No masking rule is going to catch every construct, and a counter that can go negative turns one missed atom into a wrong answer for the rest of the section, whereas a clamped one loses only the segment it missed.

Masking does not feed sentence detection, because §3.3's closer set already excludes backtick, `)` and `]`, so a terminator inside a code span or a link destination fails the terminator test unmasked.
The autolink and raw-HTML pattern needs no equivalent argument: its terminator is an ASCII `>`, and the closer set's guillemets are `»` and `›`.

**Masking does not preserve length**, because no rule reads a position inside a masked segment.
Every other rule in §3.3 reads the *raw* segment: the terminator test by the sentence above, the capital rule by skipping the opener set, which carries `[`, `(` and backslash for exactly this reason, and the block-construct rule because `<div>` and `<table>` match the raw-HTML pattern above — a masked reading would blank away the one guard `is_md_equal` cannot replace.
§3.6 indexes the *i*th run of `\x00` in the input, an ordinal rather than an offset.

**The clamp applies to the running total once per segment** — `depth = max(0, depth + delta)` — and not after each bracket character.
The two differ: at carry-in zero a segment containing `)(` leaves depth at 1 per character and 0 per segment.
Depth is consulted only at a gap, which is where the per-segment form clamps, and per character would need two numbers per segment rather than one, the net and the minimum prefix sum.

### 3.3 Sentence detection

This is the entire substance of the plugin.

**A sentence end is a terminator followed by zero or more closers, at segment end.**

```
terminators  UAX #29 STerm ∪ ATerm, 170 codepoints
closers      " ' ’ ” » › « ‹ “ ‘      plus  * _ ~
openers      " ' “ ‘ « ‹ » › ¿ ¡ „ ‚  plus  * _ ~ [ ( \
```

**The terminators are a Unicode property rather than a list.**
`.` `!` `?` `。` `！` `？` arrive with Armenian `։`, Arabic `؟`, the Devanagari danda and 163 others, and no script has to be noticed and added by hand.
ATerm is four dot-like marks, `.` `․` `﹒` `．`; STerm is the other 166.

**`…` is deliberately not among them**, because UAX #29 files it as `Other` and careful usage agrees: an ellipsis marks omission or trailing off rather than an end.
`A moment… Nobody moved.` stays on one line, and so does `A moment... Nobody moved.`, because a shipped rule joins after **exactly three** periods (§4).
Every other count is a sentence end: two periods and four are typing rather than an ellipsis, and `A moment…. Nobody moved.` is an ellipsis that then closes a sentence.
One case is out of reach rather than decided.
`A moment…… Nobody moved.` carries no terminator at all, so no candidate gap exists there, and §3.3's rules act only at candidate gaps.

**The closer set is not UAX #29 `Close`, and must not become it.**
`Close` is 195 codepoints and contains every bracket, so adopting it re-arms all three of the cases below, and the set here is not even a subset of it, since `*`, `_` and `~` are `Other`.
It is a purpose-built set instead: the marks that can follow a terminator *and still leave the sentence ended*.

`“` and `‘` are in both sets deliberately: they open in English and close in German.
So are the guillemets, and for the same reason: French and Swiss German write «…» while German and Austrian usage reverses them to »…«, so each of the four marks both opens and closes depending on the language.
Leaving `«` out of the closers is what would silently drop every sentence end in `»Ist das ein Test?« Dann ging er.`
Inside a segment the overlap costs nothing, because a closer is tested after a terminator and an opener before a capital, and neither test is reached from the position the other is asked about.
**A mark standing alone as its own segment is the one place where it does cost something, and set membership must not decide it there** — see the two structural rules below, which decide by what precedes the mark instead.

**Clause punctuation is not a closer, and that is what handles `e.g.,`**
A terminator followed by `,` `;` or `:` is not a sentence end, because the test scans back over *closers* only and none of those three is one, so the scan meets a character that is neither closer nor terminator and fails.
`e.g.,` and `i.e.,` are the common cases and they are very common in technical prose; `etc.;` in a semicolon-separated list and `Ph.D.,` in a byline are the same shape.
No rule is needed for them, and none is added.

The point of stating it is that the behavior rests entirely on an *absence*.
Anyone who later adds clause punctuation to the closer set, which is a tempting thing to try when working on rule 5, silently turns every `e.g.,` into a sentence-end candidate.
The closer set is for marks that can follow a terminator *and still end the sentence*; a comma after a period means the abbreviation was not a sentence end at all.
UAX #29 encodes the same idea as a `SContinue` set of 31 codepoints, and none is needed here: the scan crosses closers only, so everything else stops it, which covers those 31 and every other mark besides.

The closer set **excludes** `)`, `]`, `}` and backtick.
This is the root fix for a family of bugs rather than a patch for any one of them.
Three consequences:
`` Install the `foo.` Then run… `` does not break after the code span;
`See the [docs](https://ex.com/a.b.) The next…` does not break after the link;
`An array like (1, 2, 3.) Then…` does not break after the parenthetical.
The cost is that a sentence genuinely ending inside parentheses — `He left. (He came back.) Then…` — is not detected, and that is accepted: detecting it means putting `)` in the closer set, which re-arms all three cases above.

Before testing for a terminator, strip a trailing run of footnote references: `(\[\^[^\]\s]+\])+$`.
A reference glues to the word it annotates, so `The matter at hand.[^1] This is…` yields the single segment `hand.[^1]`, which ends in `]` and would otherwise match nothing.
Use that narrow grammar rather than adding `]` to the closer set, so a bare `[1]` or a citation like `[Smith 2020]` still opens no sentence.

**Which checks apply, by terminator.**

| terminator | the rules table | `require_sentence_capital` |
| --- | --- | --- |
| ATerm | yes | yes |
| STerm | no | yes |

Only ATerm consults the table, because an abbreviation is a word cut short by a period and none ends in `!`, `?` or `。`.
Opening the table to STerm would do harm rather than merely nothing: `at` has lost its terminator, so a rule cannot tell `B.` from `B!`, and the shipped initial rule would join `Plan B! Then we go.`
Folding the CJK terminators into STerm costs nothing: a CJK opening is alphabetic and not lowercase, so it passes the capital test anyway, and their wrap point exists only where the author separated the sentences with a space.
**A `!` or `?` is not unambiguous, so STerm takes the capital test too.**
Brand names end in them, `Panic! at the Disco` and `Yahoo! bought it`, and a question can belong to a quoted phrase rather than to the sentence carrying it, `A "Is this a test?" guide to the whole subject…`.
Every one of those continues with a lowercase word, so the capital test joins them all, and it does so wherever the closer stands: French spaces it off, `« Vraiment ? » dit-il en partant.`, and the lowercase `dit-il` holds the line together just the same.
The cost is the one ATerm already pays, that a sentence opening lowercase after `!` or `?` is not broken, and `require_sentence_capital = false` removes it for both.
What remains out of reach is a capitalized follower, `Yahoo! Finance reported it.`, which breaks, and no rule can say otherwise while the table is closed to STerm; `at_full`, held free in §3.3's naming, is the route if it ever matters.

**Rules are an ordered decision table, and the last match wins.**
A rules file contributes an ordered list of `[[rule]]` tables, and the lists of every file it includes are spliced in ahead of its own (§4).
At a candidate gap every rule whose patterns match is considered, and the last one decides.
Ordering is what makes a rule overridable without knowing how it was written: a later rule matching `st` settles `st`, whatever pattern an earlier rule used to reach it.
Last rather than first, because a macro's later definition already overrides its earlier one, and a file cannot be half assignment and half matcher without being a trap.

Each rule carries up to three patterns, one per position, each `fullmatch`ed against a single segment.

| key | matches |
| --- | --- |
| `at` | the terminator-bearing segment, stripped as below |
| `before_full` | the segment before that one, raw |
| `after_full` | the segment after the gap, raw |

**Only `at` is stripped, and the `_full` suffix on the other two says so.**
They are the segments as they arrive, which is what makes *unpunctuated* expressible: `before_full = '$upper$letter*'` says a capitalized word carrying no punctuation, which `Paris,` and `at` and `1890` each fail for a different reason.
A stripped `before` and `after`, and a raw `at_full`, are the three names the convention leaves free for when something needs them.
No separate condition is needed for it, and none is offered.

**`before_full` is the empty string when the candidate opens the section**, and that is what makes *nothing precedes* sayable without a keyword for it.
`before_full = ''` matches there and nowhere else, while any pattern requiring a character fails there.
The section is §3.1's unit, the inline text between hard breaks, so this is a section start rather than a document one.
`after_full` is never empty, because a gap has a segment on each side by definition.

**A `before_full` condition simply does not match at a section start**, so a rule carrying one stays silent there and whatever the table had already decided stands.
For the `st` discriminator below that is the safe direction: `St. Louis is a city.` opens its section, the discriminator says nothing, and the unconditional rule for `st` keeps the line whole.
A rule whose verdict is `no` and whose condition is on `before_full` has the opposite exposure, and its author should carry an example for the section-start case.

**Positions are counted from the terminator rather than from the gap**, which is what carries the second-order lookback below.
Where a spaced-off closer stands as its own segment, as French writes `« Ceci est important. »`, the terminator test steps back past it and `at` and `before_full` step back with it, so `at` is `important` and not `»`.
The consequence worth stating is that the closer segment is then invisible to every pattern, and no rule can ask whether one was there.

**What `at` sees is the stripped candidate**, and every shipped rule depends on it.
Before matching, the candidate loses its trailing terminator and the closers behind it, its footnote references by the grammar above, and any leading run of the opener set, so `(Fig.` and `hand.[^1]` both arrive as the bare word.
The last hyphen-separated component is tested as well, so `Wrangell-St.` matches via `st`.
That is why the shipped rules are written `mr|mrs|ms|dr` with no dots: a pattern reaching for punctuation has nothing to match against.

**Every pattern matches case-sensitively, and a pattern wanting otherwise says so** with `re`'s own scoped flag: `at = '(?i:fig|vol|ch|sec)'`.
Nothing is folded by key or by position, because a rule that folds where it was not asked to is worse than one that does not fold where it should be.

A folded `$lower.*` matches any letter at all, so an index rule under blanket folding suppresses every break rather than only the ones opening lowercase.
`$roman` fails the same way and more quietly: it is homo-case for the measured reason below, and folded `[IVXLCDM]+` matches `Vic` and `Di` in full.
Neither can happen when folding is asked for one pattern at a time.
The converse mistake is cheap: an `at` pattern that forgets the flag matches nothing that is capitalized, and the rule's mandatory example (§4) fails.

Case-insensitivity is therefore `re`'s, which is **simple** case folding rather than full.
`Straße` does not match a `strasse` pattern and `ﬁ` does not match `fi`, where `str.casefold` would join both; in the other direction `re` equates Turkish `I` with `ı` and `İ` with `i`, which `casefold` keeps apart and which no language-blind choice gets right.
Nothing in this design calls `str.lower` or `str.casefold` for matching, and `str.lower` would be the wrong one of the two in any case: it is the only one of the three that separates Greek `ς` from `σ`.

**`break` is the verdict**, and it has two values.

| value | meaning |
| --- | --- |
| `no` | this gap is not a sentence boundary |
| `allow` | the veto is lifted, and the checks below decide |

`allow` is not itself a break.
It returns the gap to ordinary detection, which may still decline it, and it is the value that lets a later rule undo an earlier one.
A gap no rule matches is `allow`, which is what makes the table a list of exceptions rather than a whitelist.
Any other value is a load error naming the two, and `break = false` is a load error rather than a synonym for `no`, because a TOML boolean is a different type and not a third verdict.

**The table is consulted only at candidate gaps**, which are the gaps following a terminator.
No rule can create a boundary where the text has none, so nothing in a rules file breaks after `clause;`.

Patterns are ordinary `re` syntax with our own classes injected, so `{1}`, alternation and quantifiers come for free and there is no vocabulary to grow.
The classes are spelled `$name` and expand to explicit ranges at build time:

```
sets       $upper $lower $oletter $numeric $mark $sterm $aterm $scontinue $close
sequence   $grapheme
```

The sets are UAX #29 Sentence_Break property values of the same names, so `$upper` folds titlecase in and leaves both Georgian scripts out, exactly as the standard defines.

**The tables are generated and vendored, not looked up.**
Python's `unicodedata` does not expose Sentence_Break at all, so there is nothing to look up at runtime, and while `uniseg` and `regex` both carry the property, §2's dependency line is mdformat only.
So `SentenceBreakProperty.txt` is vendored at a pinned UCD version, a generator turns it into the ranges above, and the source file and the generated module are both committed.
A test regenerates from the vendored copy and diffs it, which needs no network, and a Unicode upgrade becomes one replaced file whose consequences arrive as a reviewable diff.
It also decouples the tables from the user's Python, which matters because the interpreter's own lag: Python 3.11 carries UCD 14.0.0.
Lowercase POSIX spellings are a **load error**, not a synonym: UAX #29 `Numeric` is 775 codepoints against POSIX `digit`'s ten, and a user who writes `[:digit:]` meaning `0-9` should be told rather than silently given seventy-seven times what they asked for.
A rules file may define its own macros in a `[macros]` table, referencing earlier ones, which is the notation CLDR and ICU already use for this job.
Built-in names cannot be shadowed, so `$upper` means one thing everywhere.

A set expands bare inside a bracket and grouped outside it; a sequence and a macro are always grouped, and both are a load error inside a bracket.
Both rules exist because naive substitution is silently wrong: `$roman.*` expanded without grouping compiles as `[IVXLCDM]+|[ivxlcdm]+.*`, where the `.*` binds to the second alternative alone and the first matches a bare roman numeral anywhere.

**Patterns carry no anchors, because every one of them is `fullmatch`ed.**
`^` and `$` are zero-width, so an anchored alternative such as `^$numeric` demands a token of exactly one digit and matches nothing else.
Anchoring is implied by the matcher, which makes writing it a silent narrowing rather than a load error.

**The checks, which a verdict of `allow` defers to:**

- **Abbreviations.**
  The shipped table is English and small: `mr mrs ms dr prof sr jr st vs` unconditionally, and `fig no vol ch sec` under the conditions below.
  `etc`, `inc`, `ltd` and `cf` are deliberately **absent**: they commonly end sentences, and with `etc` present `Use commas, semicolons, etc. The next sentence…` loses a real boundary.
  A user's file removes any of them with a later rule whose verdict is `allow` (§4), which needs no knowledge of how the shipped table grouped them.

- **Dotted initialisms**, a shipped rule rather than a list: `at = '(?:$letter+\.)+$letter+'`.
  This is `U.S.`, `U.K.`, `Ph.D.`, `a.m.`, `e.g.`, `i.e.` and German `z.B.` in one line, with no entry for any of them, and it needs no `(?i:…)` because `$letter` already spans both cases.
  It is written against the stripped candidate, so `Ph.D.` arrives as `Ph.D` and the pattern asks for letters between the dots and a letter at the end.
  That is what makes it safe, and the alternative wording, ends in a dot and contains two or more, is wrong three ways: it claims every run of periods indiscriminately where the ellipsis rule below counts them, and it claims version numbers and IP addresses.
  It also cannot collide with the hyphen refinement above, since a hyphen is not a letter, and it leaves quoted filenames alone, since a backtick is not a letter either.
  Its cost is a bare unquoted filename: `Edit config.test.js. Then run the tests.` joins, and a user who hits that writes one `allow` rule.

- **Single capital initials**, also a shipped rule: `at = '$upper$mark*'`.
  `J. K. Rowling`.
  The predicate is exactly one letter that is UAX #29 `Upper`, plus any combining marks, so a decomposed `É` counts as one letter and `Mr` does not match.
  Its known cost is unchanged: `He got an A. Then he left.` loses that break, because a lone capital before a period has the same shape whether it is an initial or a word.

- **`require_sentence_capital`** (default true): the next sentence must open with a digit, or with an alphabetic character that is not lowercase.
  The alphabetic conjunct is load-bearing: a bare *not lowercase* is a wider set that admits `#`, `>` and `-`, and the paragraph below turns on the difference.
  Digits matter: `1976 was hot.` is a sentence opening.
  **Writing the case half as *not lowercase* rather than as *uppercase* is what carries the caseless scripts.**
  CJK, Arabic, Hebrew, Devanagari, Thai and Ethiopic are alphabetic and neither upper nor lower, so each passes without a clause of its own, while `a` and `ω` still fail.
  An *uppercase* test admits only the scripts that have case, which would leave Arabic and Hebrew prose unbreakable and the option the only way out.
  Both Georgian scripts pass too, because UAX #29 places Mkhedruli and Mtavruli in `OLetter` rather than in `Lower` and `Upper`: Georgian does not open sentences with Mtavruli, so the standard declines to treat it as a capital.
  Opening markup is skipped first, using the opener set above.

- **An opaque inline atom opens a sentence**, whatever it contains.
  A segment beginning a code span, an image or an autolink counts as a sentence opening regardless of case, because it renders as a thing rather than as prose and case does not apply to it.
  Without this, `` Install the package. `pip install foo` does the rest. `` never breaks, and neither does any sentence opening with an image or a URL.
  Formatted text is **not** included: link text and emphasis are words, so `[the docs](u) explain it.` keeps the ordinary treatment of skipping the markup and testing the word, and declines to break for the same reason a bare lowercase word would.
  The cost is that a conditional abbreviation followed by an opaque atom now breaks: `` See fig. `x` for details. `` goes wrong, which was previously right only because the backtick failed the capital test.
  A rule that cares can add an opaque-atom alternative to its own `after_full` pattern.

**The most copied alternative in this ecosystem is declined, for the reason the capital rule already turns on.**
`jlevy/flowmark`'s `SENTENCE_END_RE` requires the run before the terminator to be two or more letters ending in a *lowercase* one, `\b\p{L}+[\p{Ll}]`, which disposes of `e.g.`, `i.e.`, `U.S.`, `A.M.` and `Ph.D.` with no list at all.
Read from source and run against each: every one of them is already covered by the dotted-initialism rule above, so here it would buy nothing, while still leaving `Dr.`, `Fig.`, `etc.`, `vs.` and `Mr.` to the table, which is the part that is hard.
What it costs settles it.
`\p{Ll}` has no members in Arabic, Hebrew, CJK or Devanagari, so requiring a lowercase tail leaves every sentence in those scripts unbreakable, and it also drops sentences ending in an acronym, a numeral or a code span: `He works for NASA.`, `The total was 42.` and `` Run `make test`. `` all stop being sentence ends.
Its companion constant, a fifteen-character minimum sentence length, is width machinery and §1 declines it on sight.

**Where the line between the table and the code sits.**
Everything that decides by looking at one candidate, one segment back and one segment forward is a rule in the table, and is therefore overridable.
Everything else is code, and is not.

| check | in the table | why |
| --- | --- | --- |
| abbreviations, dotted initialisms, single initials | **yes** | three positions and nothing else |
| `require_sentence_capital` | its lowercase half could be | kept as one option because it is inherited whole (§4) |
| an opaque atom opens a sentence | no | tests the node's type, which no text pattern sees |
| quotation open versus close | no | needs the segment before the segment before |
| bracket depth | no | accumulated across a section, and a safety rule |
| block constructs, masking, the footnote strip | no | safety rules, and a rules file must not be able to defeat them |

The safety row is the one that is deliberate rather than merely difficult.
A block-construct rule that a file could countermand would let a rules file break the render, which §6.2's gate cannot catch, so no verdict reaches it.

**What an abbreviation rule is actually for.**
**Partly measured.**
The repository corpus exercises none of these tokens, but Google Books English 2019 does; `notes/experiments/ngram.py` reproduces the figures, and the method's one real limitation is recorded at the end of this block.

A rule only ever does work when the next token is capitalized or a digit, because the break before a lowercase word is suppressed already — by `require_sentence_capital` at its default, and by the conditional class's own lowercase clause whatever that option is set to.
That reframes the question for every one of them, from *is it also a word* to *what does it suppress that the capital rule does not already*, and it sorts them into three jobs and one mistake.

| tokens | job | also a word, or sentence-final | form |
| --- | --- | --- | --- |
| `mr mrs ms dr prof sr jr st` | precede a capitalized name | `st` only, as *Street* | unconditional |
| `vs` | introduces the term that follows | no | unconditional |
| `fig no vol ch sec` | precede an index | `fig`, `no`, `sec` | **conditional** |

Measured, as the share of each token's ten commonest continuations that are numerals:

| token | numeral share of the top ten | commonest continuations |
| --- | ---: | --- |
| `et al` | **100%** | 1990, 1991, 1992, 1989, 1993 |
| `Vol` | 100% | 1, 2, 3, II, I |
| `Fig` | 97% | 1, 2, 3, 4, 5 |
| `Ch` | 92% | 1, D, 3, 2, 4 |
| `Sec` | 20% | also, Entry, `_END_`, of, 1 |
| `vs` | 13% | the, time, 1, a, non |
| `fig` | 12% | **tree, trees, leaf, leaves** |
| `No` / `no` | **0%** | one, matter, doubt / longer, one, more |
| `St` | 0% | John, Paul, Louis, Petersburg, Mary |
| `Dr` | 0% | John, David, Johnson, J., Peter |

**The index class is where a condition earns its place.**
Each of these precedes a number rather than a name, and three of them are also ordinary English: a `fig` is a fruit, `no` is a negation, a `sec` is a moment.
`He ate a fig.`, `The answer was no.` and `Wait a sec.` all end sentences, and all three lose that boundary if the rule is unconditional, which is what rumdl and `mdformat-sembr` both do.

So these suppress a break only when the follower matches one of two shipped patterns, **whole** `(?:$numeric)+|(?:$roman)` or **mixed** `(?:$roman)|(?:$numeric).*|.*(?:$numeric)`, or when it opens with a lowercase letter.
`fig vol ch sec` take **whole**; `no` takes **mixed**, which also admits designators like `6c` and `C-3` and page ranges like `12-14`.
`$roman` is homo-case for a measured reason: a case-folded `[IVXLCDM]+` matches `Vic` and `Di` in full, since those are all roman letters, and a capitalized word after `Fig.` or `Vol.` would be swallowed as a numeral.
**mixed** costs two false joins in technical prose, `UTF-8` and `Python3`, both of which match its ends-with-a-digit half.
`No. 5`, `Fig. 3`, `Vol. II`, `Ch. IV` and `Vol. I` hold; `He ate a fig. Then he left.` breaks.

**The lowercase half is deliberately redundant with `require_sentence_capital`.**
At the option's default the capital rule has already suppressed those breaks and the clause does nothing.
With the option turned off it is the only thing between `Smith et al. showed that…` and a break, and likewise for `vol. iii` and `ch. iv`, whose lowercase roman numerals the index token does not admit.
The class carries its own guard for the same reason the block-construct rule below does: a safety property a user-facing flag can switch off is not one the rest of the design can rely on.

A digit-only test would be wrong, because roman numerals are ordinary for volumes, chapters and sections and digits alone would split `Vol. II`.
Measured: `Ch` has the single letter `D` among its five commonest continuations, so single-character labels are real and not a corner case.

**The run is deliberately not required to be two or more characters**, although that would fix one bad case: a bare `I` is the English pronoun, so `No. I think so.` is suppressed and stays on one line.
That is a *missed* break, and the alternative error is worse.
Requiring two characters splits `Vol. I of the series` after `Vol.`, which severs a noun phrase and puts `I` at the head of a line.
Neither error touches the rendered document, because every break is at a wrap point and the render is identical either way; what differs is the source.
A held-back break leaves a long line, which reads as prose; a wrong break leaves a fragment, which reads as a mistake.
Single-letter labels outside `IVXLCDM`, such as `Sec. A`, are not covered and will break, which is the same trade taken the same way.

**`vs` stays unconditional** although it too precedes a name rather than an index, because it is not an English word in any inflection and cannot end a sentence.

**`al` is not in the default set, and the measurement is why it looks necessary.**
`et al.` is followed by a citation year often enough that a rule for it appears to earn its place: every one of its ten commonest continuations is a year, and measuring the bare token instead gives 44% because `al Qaeda` and `al dente` are not this abbreviation.
Digits are sentence openings, so the capital rule does not suppress before one, and without a rule `Smith et al. 1990 showed…` breaks wrongly.

It stays out of the default anyway, because the shape that matters is already handled.
`(Smith et al. 1990)` and `[@Smith2020, p. 12-14]` both sit inside brackets, and the bracket-depth rule below counts `(` as well as `[`.
What an `al` rule uniquely buys is the unparenthesized author-year form, which is one discipline's house style rather than general English.
So it ships in `academic.toml` instead (§4), in a form tighter than any index condition:

```toml
[[rule]]
before_full = '(?i:et)'
at          = '(?i:al)'
after_full  = '$numeric{4}'
break       = 'no'
```

That suppresses `Smith et al. 1990` and nothing else, where an index condition also wrongly suppresses `et al. II`.

**`st` is a known ambiguity, and the default resolves it one way while a rule resolves it the other.**
`St. Louis` and `Main St. Then he left.` both put a capital after the period, so neither the capital rule nor an index test separates them.
The measurement is reassuring but not decisive: `St` is followed by `John`, `Paul`, `Louis`, `Petersburg` and `Mary`, with the *Street* sense nowhere in the top continuations, so unconditional is the right default for prose like this corpus.
Books under-represent addresses, though, and a discriminator does exist in what *precedes* the token, since *Saint* leads a name while *Street* trails one:

```toml
[[rule]]
before_full = '$upper$letter*'
at          = '(?i:st)'
break       = 'allow'
```

A document full of addresses adds that; the shipped set does not, because its failure is a class rather than a corner.
It separates `Main St. Then he left.` and `Elm St. Later he moved.` from `at St. Louis`, `of St. Mary` and `In 1890 St. Louis`, and it decides `Mount St. Helens` and `Paris St. Denis` the wrong way, because those put a capitalized unpunctuated word before a saint.

**What the measurement cannot show, and why.**
The wildcard returns only the ten commonest continuations and omits punctuation from them, so every figure above is a share of that top ten rather than of all occurrences.
A 0% row means no numeral is among the ten, not that none ever follows, and the 100% row means every one of the ten is a year, not that a year always follows.
`et al. showed that…` never enters the denominator.
Google's tokenizer splits the abbreviation period off and treats it as a sentence terminator, so `Fig . 1` has a frequency of exactly zero while `Fig 1` is ordinary, and every n-gram following a period is `_END_`.
The corpus has therefore already decided the question this section is about, and decided it wrongly for abbreviations.
The figures above are from the period-less forms, which measure *index use versus word use* — the axis that sorts the table — and say nothing directly about how often each token ends a sentence.
`Sec` is the one row carrying a direct signal: `_END_` is Google's sentence-end marker, so `Sec` demonstrably ends sentences, which is why its rule is conditional.
`fig` is the clearest case the method does reach: capitalized `Fig` is 97% numerals while lowercase `fig` is 46% `tree`, so the label and the fruit separate cleanly on case, which the shipped rule's `(?i:…)` deliberately declines to exploit.

**None of this departs from rumdl's reasoning, only from its implementation.**
rumdl admits a token only if it is "almost always followed by something, not sentence-final", and files this class under "Reference abbreviations — followed by what they refer to".
The conditions above make that criterion operational instead of assuming it holds for the bare token.

**A sentence never opens with a block-construct marker, and this applies to every terminator.**
If the next segment would start `#`, `>`, `-`/`*`/`+`, a bare `\d+[.)]`, a setext or thematic run at line start, or an HTML block opener, the gap is not a sentence boundary.
The HTML entry is the one it is easy to omit, because mdformat's remedy for it is not an escape character.
`paragraph()` prefixes four spaces to any line matching an `HTML_SEQUENCES` opener that can interrupt a paragraph, so `Do not use it. <div> is a block element.` broken at the sentence end comes back as `'Do not use it.\n    <div> is a block element.\n'`.
Verified by execution against mdformat 1.0.0, with `<div>`, `<table>` and `<!-- -->`.
`is_md_equal` passes on all three, so §6.2's render-equality gate cannot catch this one and the rule is the only guard.

**Why it passes is worth stating, because it is not that the check is weak.**
Nothing is wrong with the render.
The four spaces are mdformat repairing it: they keep the `<div>` a lazy continuation line inside the paragraph, where it stays inline HTML, so the HTML differs from the unbroken source only in that one space became a newline, and `is_md_equal` reduces every whitespace run to a single space before comparing.
Break the same gap without the indent and the check does fire, because `<div>` at line start becomes an HTML block and the paragraph ends early.
What survives the repair is damage to the *source*: four spaces this plugin never asked for, on a line it promised would gain nothing but a newline.
A gate that compares rendered HTML is structurally blind to that, whatever else it is good for.

This rule is **unconditional and independent of `require_sentence_capital`**, and that matters.
It is the only thing preventing a break from putting a construct at a line start where mdformat would escape it, and because this plugin has no `avoid_escapes` option (§4.1), it is the only protection there is.
Requiring an alphabetic character rather than merely a non-lowercase one happens to suppress the same cases, but a user who sets `require_sentence_capital = false` would otherwise re-arm all of them.

**Quotation marks are language-specific.**
Two structural rules follow, neither of them about any one language:

- A segment consisting only of quotation or markup characters is read as *closing* when the segment before it ends in a terminator, and as *opening* otherwise.
  Membership in the two sets above cannot decide it, because every guillemet and both of `“` `‘` are in both sets; what the mark is doing is determined by what it follows, not by which language wrote it.
- A segment read as closing is never a break candidate, and when the segment to the left is such a mark, the terminator test looks one segment further back.
  French spaces its closer off — `« Ceci est important. »` — which puts the closer in a segment of its own and breaks the naive rule twice, once by orphaning the mark onto the next line and once by failing to see the terminator.
- A segment read as *opening* defers the capital test to the next segment rather than failing it.
  Returning "no opener found" is not the same as "no sentence opens here".
  This is the rule that keeps `Il a dit. « Ceci est important. »` breaking after `dit.`: the lone `«` follows no terminator, so it is opening markup and the capital test moves on to `Ceci`.

**The cascade has two results; the opener scan has three.**
Every check in this section either vetoes a break or abstains, and none can force one, because `break` takes only `no` and `allow` (§4) and the table is consulted only at candidate gaps.
So the cascade is a conjunction: a gap breaks when nothing has objected, the order the checks run in is free, and an opaque atom satisfying the capital test does not override the block-construct rule vetoing the same gap.
A `Break / NoBreak / unmatched` result for the cascade would therefore carry an arm that nothing ever returns, which is an invitation rather than a clarification.

The opener scan is the one place the third state is real.
Looking forward past opening markup for a character to test, it can find one that passes, find one that fails, or reach the end of the segment having found none, and the third is not the second: the quotation rule above turns on exactly that difference.
A scan that reaches the end of the paragraph still having found none reports failure, because no sentence opens there at all.

Isolation, which is the usual argument for the three-valued form, is already had another way here.
A rule in the table is isolated by its mandatory examples (§4), and the checks that stay in code are isolated by §6.2's hand-written fixture pairs.
Adding a forcing verdict would give the cascade a genuine third result, and this is the paragraph to revisit if one ever arrives.

**No boundary inside brackets.**
Depth counts `[` as well as `(`, as §3.2's per-segment deltas accumulated across the section and clamped at zero after each.
A citation like `[@Smith2020, p. 12-14]` is prose brackets and its `p.` is not a sentence end; without the guard it splits.
The discriminator between prose brackets and link syntax is the seam itself: mdformat collapses wrap points inside a link, so a *complete* bracket group within one segment is link syntax, while a group arriving in pieces across segments is prose.

### 3.4 Emission and the width-independence property

Every gap resolves to exactly one of two characters:

```
sentence break, and edge-safe (§3.5)  ->  "\n"
everything else                       ->  " "
```

No `\x00` is ever emitted.
`MDRenderer.render_tree` asserts that none survives, and this design satisfies that assertion by construction rather than by accident.

The consequence is the property in §1.
After the postprocessor returns, each line mdformat receives contains no interior wrap point, so `_wrap` has nothing to break on and returns the line unchanged whatever `fill_column` it was given.
Verified by execution against mdformat 1.0.0 with a throwaway postprocessor of exactly this shape: a 140-character sentence survives intact at `--wrap 80`, and the same input at `--wrap no` produces byte-identical output.
The same experiment *without* pinning produces 78- and 61-character lines at `--wrap 80`, which is the behavior this plugin exists to avoid.

Idempotency across mdformat's two-pass render follows from the same construction.
On the second pass the inserted `\n` re-parses as a softbreak and the literal spaces re-collapse, so every gap is a `\x00` again and the identical content re-derives the identical breaks.
That holds only because no break decision consults a width, and because §3.3's block-construct rule guarantees mdformat adds no escape on the first pass that would change the second pass's tokens.

### 3.5 Correctness rules

Two, both non-negotiable.

**Edge safety.**
A gap is ineligible when the last character of the segment to its left, or the first character of the segment to its right, is whitespace that `str.strip()` would delete.
Test with `.strip()`, not with a character list.
mdformat's `paragraph()` strips each line after wrapping, so a break at such a gap silently deletes the character, and `is_md_equal` cannot see it because HTML comparison collapses whitespace.

The rule is small because of §3.4: only sentence gaps can break at all, and every other gap is already pinned, which is the same mechanism the guard uses.
An ineligible sentence gap is simply pinned like its neighbors.

**Tilde sections are declined outright.**
A run of three or more tildes at a line start opens a fenced code block and changes the render.
This is an upstream mdformat defect, not ours — plain mdformat with no plugin and no extensions reproduces it — but our breaks reach it far more often, so the blast radius is ours.
A section containing `~{3,}` is returned unchanged, with every gap pinned — every gap in the section, not only the gaps adjacent to the tilde run.
Pinning only the gaps on either side of the run is not sufficient, because a break taken anywhere else in the section can put the run at a line start by another route; pinning the whole section emits no `\n` and no `\x00` in it, so it stays a single line and the run can only reach a line start if it already was one.
A section containing a tilde fence is not one anybody is line-breaking for readability anyway.

### 3.6 Failure policy

Rebuild the emitted section from the input: replace the *i*th run of `\x00` in the input section with the *i*th separator the loop chose, and require byte equality with what was actually emitted.
On mismatch, return the text untouched.

Two reconstructions that look equivalent and are not.

Do *not* recover the input by scanning the emitted string for `\n` and `" "`: mdformat has already collapsed each link, image and code span into a single segment with literal interior spaces (§3.1), so a scan turns those spaces into wrap points too and the check fails on every paragraph carrying a multi-word link.

Do *not* use `"\x00".join(segs) == section` either.
`re.split(r"\x00+", ...)` collapses a run of wrap points (§2.3), so that comparison is false for every section containing one, and a single tab at the end of a line produces one: `text()` turns the tab into a space and then into a `\x00`, and the following `softbreak()` contributes a second, which is measurable as `'Alpha\x00beta.\x00\x00gamma\x00delta.'` from `"Alpha beta.\t\ngamma delta."`.
Every such paragraph would be handed back untouched and never broken at all.
It is also the weaker check, because it never looks at the emitted string and therefore cannot see the error it exists to catch.

The alternative is writing corrupted prose into the user's file.
"Untouched" is a coherent degraded mode here rather than a failure: the paragraph is simply left to mdformat, which under `--wrap no` puts it on one line and under `--wrap keep` leaves it alone.

______________________________________________________________________

## 4. Config surface

One option and one rules file.

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `require_sentence_capital` | bool | `true` | `word. lowercase` is not a boundary |
| `rules_file` | path | none | a TOML rules file, which lists the shipped sets its own rules build on |

Abbreviations are **not** settable on the command line.
A list of tokens is the wrong thing to type into a shell, and once rules carry patterns and examples it stops being a list at all.

**`include` is mandatory, and it is always an array.**
It names the sets or files whose rules are laid down ahead of this file's own, in the order given.
`include = ["default"]` builds on the shipped table; `include = []` says in as many characters that this file is the whole table.
Omitting the key is a load error, and so is a bare string where the array belongs.
That is the whole of the question, and an empty array answers it in the one way that cannot be reached by forgetting something: a missing key would silently drop the shipped rules, and the symptom is diffuse, text breaking in more places than it used to, at `Dept.` and `Mr.` and `Fig.`, with nothing naming the cause.

**Composition is splicing, not merging.**
`include = ["default", "academic"]` lays down the default's rules, then academic's, then this file's, and §3.3's last-match-wins settles any gap they disagree about.
So a file overrides an inherited rule by writing a later one that matches the same token, without knowing or repeating how the earlier one was expressed, and removes a rule by writing `break = 'allow'` for what it matched.
Several bases compose through the array and only through it, because TOML forbids a duplicate key and a second `include` line is a parse error rather than a second base.
A name that is not a shipped set is a load error, as is a cycle, and both resolve before any pattern compiles.

**`schema` is the format version, and the loader checks it.**
A file whose `schema` this version does not recognize is a load error naming the one it does, so a future incompatible format is refused rather than half-read into rules that look plausible.

**There is no `language` key**, because nothing would read it.
Case folding is per-pattern (§3.3), quote direction is decided by what a mark follows rather than by which language wrote it, and the terminators are a Unicode property, so no check left in this design takes a language.
What a set is for belongs in a comment at the top of it and in its filename, where a reader sees it and no one expects it to do anything.

**What an `include` entry names, and where a path starts from.**
A bare word carrying no path separator and no `.toml` suffix is a shipped set, and a bare word naming no shipped set is a load error that lists the ones there are.
Anything else is a path, resolved relative to the file the `include` is written in, so a rules file and the files it builds on travel together.
That is deliberately neither the config file's directory nor the working directory: an included file is a neighbor of the file naming it, and resolving against anything else breaks as soon as the pair is copied somewhere.

**A relative `rules_file` resolves against the config file mdformat read**, found the way mdformat finds it.
The plugin walks up from the directory of `context.options["mdformat"]["filename"]` to the nearest `.mdformat.toml`, which is exactly what `_conf.py`'s `read_toml_opts` does for that file, and resolves against the directory it stops in.
With no config file on the way up, or no filename to start from (`''` under `mdformat.text()`, `'-'` for stdin), it resolves against the working directory; an absolute path is used as written.

**Where a value came from is not visible at this seam**, so no rule can depend on it.
`_cli.py` binds the config file's path as a local and merges TOML-set and CLI-set plugin options into one mapping, so a plugin sees `rules_file` as a bare string either way; mdformat's own `is_excluded` can tell them apart only because it runs inside `run()`, where that local is still in scope.
The cost falls on the command line: a relative `--sentence-rules-file` resolves against the config directory whenever one exists, not against the shell's directory, so a path typed at the shell is safest absolute.

**What an included file contributes is rules and macros, never the notation.**
The `$name` sets of §3.3 are the pattern language rather than rule content, so every file gets them and no file can shadow them.
`$letter`, `$roman`, `$whole` and `$mixed` are **not** among them: they are `[macros]` in the default file, so a file including nothing must define its own, and using `$whole` without defining it is an undefined-macro error rather than a silent no-op.
`$letter` carries trailing marks, `(?:$upper|$lower|$oletter)$mark*`, so a decomposed `É` counts as one letter wherever it is used.
That is the intended split, because it is what lets a user narrow `$roman` to reject `iiiv` while leaving `$numeric` meaning one thing everywhere.

**Every string in a rules file is a literal string**, `'…'` for patterns and `'''…'''` for examples.
A basic string rejects `\d` outright as an unescaped backslash, so no pattern can be written in one.
A triple-quoted literal takes backslashes unchanged, holds an apostrophe, and carries real newlines with the one after the opening delimiter trimmed, so an expected output reads as the lines it is.
It also preserves leading whitespace exactly, so its content stays flush left however the surrounding keys are indented.

The file carries `[macros]` and `[[rule]]` tables, each rule optionally carrying `[[rule.example]]`:

```toml
# The shipped English set.
schema  = 1
include = []

[macros]
letter = '(?:$upper|$lower|$oletter)$mark*'
roman = '[IVXLCDM]+|[ivxlcdm]+'
whole = '(?:$numeric)+|(?:$roman)'
mixed = '(?:$roman)|(?:$numeric).*|.*(?:$numeric)'

[[rule]]
at    = '(?i:mr|mrs|ms|dr|prof|sr|jr|st|vs)'
break = 'no'

[[rule]]
at         = '(?i:fig|vol|ch|sec)'
after_full = '$whole|$lower.*'
break      = 'no'

  [[rule.example]]
  input = '''
He ate a fig. Then he left.
'''
  output = '''
He ate a fig.
Then he left.
'''

[[rule]]
at         = '(?i:no)'
after_full = '$mixed|$lower.*'
break      = 'no'

  [[rule.example]]
  input = '''
See No. 5 for details.
'''
  output = '''
See No. 5 for details.
'''

  [[rule.example]]
  input = '''
The answer was no. Then he left.
'''
  output = '''
The answer was no.
Then he left.
'''

[[rule]]
at    = '(?:$letter+\.)+$letter+'
break = 'no'

  [[rule.example]]
  input = '''
He holds a Ph.D. Cambridge gave it to him.
'''
  output = '''
He holds a Ph.D. Cambridge gave it to him.
'''

[[rule]]
at    = '$upper$mark*'
break = 'no'

  [[rule.example]]
  input = '''
Written by J. K. Rowling. The sequel followed.
'''
  output = '''
Written by J. K. Rowling.
The sequel followed.
'''

# Exactly three periods is an ellipsis. `at` has already lost one
# terminator, so this asks for exactly two left, and nothing else.
[[rule]]
at    = '(?:.*[^.])?\.\.'
break = 'no'

  [[rule.example]]
  input = '''
A moment... Nobody moved.
'''
  output = '''
A moment... Nobody moved.
'''

  [[rule.example]]
  input = '''
A moment.... Nobody moved.
'''
  output = '''
A moment....
Nobody moved.
'''
```

**Examples are mandatory for any rule carrying a pattern**, and the loader rejects one that has none.
That is not caution in the abstract: a pattern that compiles and is wrong looks exactly like one that is right, and neither the render-equality gate nor §6.2's minimality row can tell them apart.
Each example runs against the real postprocessor with that rule and its includes loaded, which is the smallest set that can show anything: a rule whose verdict is `allow` countermands nothing when it stands alone.

Two things about where an example sits.
One written before the first `[[rule]]` is a TOML parse error rather than a silent misbinding, because it makes `rule` a table that the following `[[rule]]` cannot overwrite.
One left behind when its rule moves is not caught by anything, because it silently rebinds to whatever rule now precedes it; the two-space indent above is cosmetic and carries no meaning.

**The default file is package data, loaded at runtime, and is itself the default.**
There is no second copy in code for it to drift from, and it carries `include = []` like any other complete table.
A separate console script prints it, so `mdformat-sentence-rules > my-rules.toml` is the whole workflow for starting from the shipped set, and the dump arrives already saying what it is.

**A second set ships, `academic.toml`, and it is two rules on top of the default.**
It exists because the rules that move between audiences are few and identifiable, not because academic Markdown is a different language: `al` earns its place only where unparenthesized author-year citations are house style, and the index class wants a looser follower where `Fig. 3a`, `Eq. 13b` and `Sec. 4.2` are ordinary.

```toml
schema  = 1
include = ['default']

[[rule]]
before_full = '(?i:et)'
at          = '(?i:al)'
after_full  = '$numeric{4}'
break       = 'no'

  [[rule.example]]
  input = '''
Smith et al. 1990 showed the effect. The result held.
'''
  output = '''
Smith et al. 1990 showed the effect.
The result held.
'''

[[rule]]
at         = '(?i:fig|vol|ch|sec|eq|eqn|tbl|p|pp)'
after_full = '$mixed|$lower.*'
break      = 'no'

  [[rule.example]]
  input = '''
See fig. 3a and sec. 4.2. The rest follows.
'''
  output = '''
See fig. 3a and sec. 4.2.
The rest follows.
'''
```

The second rule does not repeat the default's grouping and does not have to.
It covers the default's four index tokens and five more, with the looser follower, and being later it decides wherever it matches; where it does not match, such as `fig.` before `Then`, neither rule matches and ordinary detection breaks as it should.
`Ph.D.`, `a.m.`, `e.g.` and `i.e.` are **not** here and need no rule anywhere: §3.3's dotted-initialism check already covers every one of them.
`cf` is not here either, for the reason it is absent from the default, which academic prose does not change.

**Lifting one token out of a shipped rule is the case the ordering exists for.**
A manual full of street addresses and no saints overrides `st` without knowing that the default grouped it with eight other titles:

```toml
schema  = 1
include = ['default']

[[rule]]
at    = '(?i:st)'
break = 'allow'

  [[rule.example]]
  input = '''
He walked down Main St. Then he left.
'''
  output = '''
He walked down Main St.
Then he left.
'''
```

The cost of ordering is that a token's fate is no longer readable in one place: it is whichever rule matched last, across every included file.

The dump script takes an optional set name, so `mdformat-sentence-rules academic` prints this one and a bare invocation prints the default.

That command is deliberately **not** an mdformat flag.
`_cli.py`'s `run()` calls `parse_args` as its first statement, before path resolution and before the per-file loop, so a print-and-exit action would fire there: `mdformat --check --sentence-dump-rules file.md` would print and exit `0` having checked nothing.

CLI spelling is short, because mdformat namespaces only the argparse `dest` and leaves the flag text to the plugin (§2.4):

```
--sentence-no-require-sentence-capital
--sentence-rules-file PATH
```

Every default must be `None`, for the reason in §2.4.

As with any mdformat plugin, these are CLI- and TOML-only: `mdformat.text()` does not populate `options["mdformat"]["plugin"]`, so a library caller gets the defaults.
An undocumented escape hatch exists and the test harnesses use it — `options={"plugin": {"sentence": {...}}}` reaches the seam via the splat at `_api.py:29` — but it is not a supported mdformat interface.

**`require_sentence_capital` is inherited, and that is the whole of its provenance.**
rumdl has it under the same name with the same default, and its trigger was one issue reporting that lowercase English prose did not reflow ([rvben/rumdl#514](https://github.com/rvben/rumdl/issues/514)); no argument from any language was attached to it there or here.
It is kept because it now costs nothing, not because a need for it has been shown, and the widened test in §3.3 removes the one principled use it had.
Turning it off is not free: it makes every abbreviation absent from the shipped set a break site, so `Dept. of Defense` breaks after `Dept.`
It re-arms nothing that protects the output, though: the conditional abbreviations and the block-construct rule both carry their own guards (§3.3).

**One rough edge inherited from mdformat, stated rather than worked around.**
Nothing in `_api.py` or `_cli.py` wraps plugin code in `try`/`except`, so a malformed rules file surfaces as an uncaught traceback, and `sys.exit()` from a plugin would kill a `mdformat.text()` caller's process rather than just the CLI.

### 4.1 Options deliberately not provided

- **Any width, column or line-length option.** §1.
- **`avoid_escapes`.**
  Unnecessary: §3.3's block-construct rule is unconditional, so no break can land before `#`, `>`, `-`, an enumerator or an HTML block opener, and no escape and no four-space indent is ever added.
- **A "honor `--wrap`" mode** that would let mdformat wrap inside a sentence.
  That is a coherent product — GNU Emacs's `fill-paragraph-semlf` is exactly it — but it reintroduces geometric line breaks and therefore forfeits §1's property, which is the only reason this plugin exists.
  Anyone who wants it wants a different tool.
- **`break_words`, `strict_clauses`, `merge_short_lines`, `min_line_chars`.**
  No clause or width machinery exists to configure.
- **Reading the document's language from front matter.**
  Reachable, and declined.
  With a front-matter plugin named in `--extensions` a `lang:` key survives as a node this seam reaches by walking to the root, and hand-scanning for it needs no YAML parser and no dependency.
  It is declined because it would be silently conditional on an unrelated plugin being named: `--extensions` is a whitelist (§2.1), so a user who does not name the front-matter plugin gets the shipped rules with nothing saying why, which is the failure mode `include` was just made mandatory to avoid.
  The language mechanism here is a rules file named by `rules_file` or `include`, which is explicit and needs no plugin.

______________________________________________________________________

## 5. Conformance to the specification

The sembr specification has thirteen normative rules.

| # | Rule | Mechanism | Status |
| --- | --- | --- | --- |
| 1 | Text MAY use semantic line breaks | the premise | n/a |
| 2 | MUST NOT alter rendered output | breaks only at wrap points; `--validate` on by default | **yes** |
| 3 | SHOULD NOT alter intended meaning | sentence boundaries only | **yes** |
| 4 | MUST occur after a sentence | §3.3, unconditional | **yes** |
| 5 | SHOULD occur after an independent clause | — | **declined, §5.1** |
| 6 | MAY occur after a dependent clause | — | not implemented |
| 7 | RECOMMENDED before an enumerated list | n/a — a list inside a paragraph is not a list | n/a |
| 8 | MAY be used after items in a list | mdformat handles list structure | n/a |
| 9 | MUST NOT occur within a hyphenated word | no wrap point inside a token | **yes** |
| 10 | MAY occur before and after a hyperlink | wrap points surround links, but no break is taken there | not implemented |
| 11 | MAY occur before inline markup | as rule 10 | not implemented |
| 12 | 80 characters RECOMMENDED | — | **not implemented, §1** |
| 13 | MAY exceed the maximum where necessary | — | n/a without rule 12 |

Rules 4 and 9 are the two this plugin implements, and they are the only MUSTs among the break rules.

### 5.1 Declining rule 5 honestly

Rule 5 is a SHOULD, and this plugin does not do it.
That is a real gap and it should not be dressed up as a design choice about taste.

The reason is that rule 5 cannot be implemented from punctuation alone without over-firing.
Read unconditionally, it breaks at every comma at paren depth zero with no test for whether an independent clause follows, which shatters serial lists (`LaTeX,` / `Markdown,` / `and plain text,`), coordinate prepositional phrases and introductory adverbials.
The usual remedy is a length-based merge pass that folds short lines back — a geometric patch for a grammatical problem, and one this plugin has no width to compute.

Implementing rule 5 correctly needs a test for whether both sides of a comma could stand alone as sentences, which is the parsing problem this project has ruled out by charter.
Declining the rule is the honest position for a tool that will not parse.

Rule 12 is declined for the reason in §1 and needs no further defense: it is a RECOMMENDED, and honoring it is incompatible with the property this plugin sells.

### 5.2 What punctuation cannot see, measured

§5.1 argues that a punctuation rule over-fires.
It also under-fires, and that is the sharper objection, because no amount of tuning reaches a position where there is no signal.

Every line break in the Semantic Line Breaks specification's own prose, which is hand-written clause-level sembr by the specification's author, classified by what sits at the break:

| break falls at | rule | count | share |
| --- | --- | ---: | ---: |
| a sentence end | 4 | 11 | 12% |
| clause punctuation `,` `;` `:` — | 5 | 37 | 42% |
| a hyperlink or inline-markup boundary | 10, 11 | 8 | 9% |
| none of the above | 6 | 32 | **36%** |

Breaks are classified by the first row that matches, so the rows are disjoint by construction rather than by luck; two of the breaks classified 4 or 5 also sit at a markup boundary and would have been claimed by the third row had it been tested first.

Three things follow.

**This plugin implements the rule that accounts for 12% of what a sembr author does by hand.**
That is the size of the promise.

**Declining rule 5 forgoes 42%, and it is the larger of the two costs.**
§5.1 gives the reason and the reason stands; this is its price.

**The remaining 36% is reachable by nothing lexical at all.**
Rule 6 breaks after a *dependent* clause, where there is no punctuation and no reliable vocabulary.
A 36-word break-word list recovers 12 of those 32 and leaves 23% of all breaks undetectable; a conservative 14-word list recovers 2.
Real breaks from that prose, none of which any punctuation or word rule can see:

```
_Semantic Line Breaks_ describe a set of conventions
for using insensitive vertical whitespace
Conventional markup languages like HTML and XML
```

So even a perfect rule 5 would leave more than a third of the breaks unreachable.
That is the measurement behind §5.1's claim that implementing rule 5 correctly needs a parser: the part punctuation can see is not the whole problem, and the part it cannot see has no smaller solution.

**The rules 10 and 11 row is the cheapest 9% on the table.**
They are in it so they are not forgotten, because they are the one part of the unimplemented remainder that is *not* a hard problem.
Unlike rule 6 their positions are trivially matchable, the more so at this seam, because mdformat has already collapsed a link or image into a single atom before the plugin runs (§3.1), so a gap adjacent to one is exactly identifiable.
Ten of this corpus's 122 prose lines open with a reference link, which is what those 8 breaks are.
It is a corpus that uses links lightly, so read the share rather than the count, and if rules 10 and 11 are ever revisited this row is the measurement to redo first against prose that leans on links.

Reproduce the table with `notes/experiments/rules.py`, and the break-word figures above it with `notes/experiments/breaks.py`.
One document and 88 breaks is a small sample, and `notes/corpus/README.md` explains why it is nonetheless the right one: this document is pure sentence-per-line, so measuring layout rules against it returns a perfect score for anything.

______________________________________________________________________

## 6. Verification

### 6.1 The width-independence invariant

This is the cheapest and strongest test here.

> For every input, the output at `--wrap no` is byte-identical to the output at `--wrap 20`, `40`, `80`, `120` and `1000`.

It is total rather than statistical, it needs no corpus and no oracle, and almost any implementation error breaks it — a forgotten pin, a width consulted anywhere, an off-by-one in segmentation.
Run it over the fixtures, over `notes/corpus/`, and over a fuzz corpus that the §6.4 harness will have to define.

### 6.2 The rest of the gate

| Check | Required |
| --- | --- |
| width independence (§6.1) | exact, at every width |
| render equality vs baseline | 0 regressions |
| idempotency vs baseline | 0 regressions |
| whitespace deletions vs baseline | 0 |
| structural property | pass |
| positive control | must fail when the plugin is absent |
| locality (§1's promise) | one inserted word changes exactly one line |
| minimality | every shipped rule is the last match for something |

**The requirement in each row is zero; the sample it is measured over is not yet fixed.**
No generator for adversarial paragraphs and no fuzz corpus exists yet, so the harness of §6.4 sets those sizes when it is built, and until then a green row means only that the fixtures and `notes/corpus/` passed.

**The locality row tests §1's leading promise, which nothing else does.**
For each paragraph, insert a *neutral* token — a plain lowercase word carrying no terminator — into sentence *n*, format before and after, and require the diff to change exactly one line, sentence *n*'s.
The neutrality matters: a token carrying a terminator legitimately creates a line.
This passes on the first day and proves little, because every sentence already occupies its own line, so locality currently falls out of the structure rather than being earned.
It is a tripwire, and worth its cost as one: it is the row that catches any future rule whose decisions depend on text elsewhere in the document.

**The minimality row keeps the shipped sets honest**, and it runs over every file the package ships, not only the default.
Each set is loaded with its own includes and tested on the rules it defines, so `academic.toml` must justify its own two rules but may shadow the default's index rule, which it does on purpose; a gate that forbade that would forbid the override the ordering exists to allow.
For each rule, build a fixture where the table's verdict at some gap is that rule's, then require that removing the rule changes the output there.
A conditional rule needs two fixtures, one where its `before_full` or `after_full` pattern holds and one where it does not, so the row also catches a condition that has quietly become unreachable.
Ordering makes this stronger than a removal test alone: a rule that is never the last match for any gap is fully shadowed by a later one, and the fixture cannot be built at all.
A rule no fixture can distinguish was copied from somewhere else and is silently widening the exclusion.
The checks living in code rather than in the table — the opaque-atom check, the block-construct rule, bracket depth, masking, the footnote strip — cannot be tested by removal and need hand-written fixture pairs instead.

Every oracle is **relative**: plain mdformat at the same width, with `extensions=set()` named explicitly.
Absolute render equality is the wrong bar because mdformat itself already breaks the render on some inputs (§3.5's tilde fence), and holding ourselves to a standard mdformat does not meet means either failing forever or weakening the test until it says nothing.

Three traps in the harness itself.
`--extensions` is a whitelist, so every baseline must name `extensions=set()`;
`--check` never validates;
and the quality harness must fail loudly rather than reporting an F1 for a plugin that never ran.

### 6.3 rumdl is a working implementation to learn from, not an oracle

rumdl's MD013 has four reflow modes, one of them `sentence-per-line`.
Verified by execution against `rumdl==0.2.60`: in that mode, with `line-length = 80`, a 136-character sentence is left intact on one line, and the reflow trigger contains no length test at all.
So a shipped tool already makes the width-independent sentence-per-line promise, which is evidence that §1 describes a coherent product rather than one person's idiosyncrasy.

It is worth more than that, though.
rumdl has solved in production several of the problems §3 will have to solve, and its solutions are worth reading before writing ours: `sentence_utils.rs` for the terminator and abbreviation handling, and `text_reflow.rs` for segmentation and for the atomicity of links and code spans.
The closer-set exclusion in §3.3 is a case where reading a working implementation is what surfaced the right rule.
Read it as a source of solved problems and of test cases we would not have thought of.

What it is not is an oracle.
It is deliberately absent from §6.2's gate: agreement is not a target and divergence is not a defect.
rumdl has its own blind spots, this design intends to do better in places, and where the two disagree the specification decides, not the other implementation's output.

### 6.4 What to build first

1. The positive control, before anything else.
   Every other check in §6.2 passes with the plugin disabled — an identity function deletes nothing, changes no render, and is trivially width-independent — so until one test fails when the plugin is absent, a green suite does not distinguish a working plugin from an inert one.
1. §6.1, which is three lines and catches most of what can go wrong.
1. The sentence-detection fixtures, which are where the remaining complexity actually lives: abbreviations, initials, the capital rule, footnote references, CJK, French spaced closers, German quotes, the `?"` case, bracket depth, and block constructs.

**Six of them come from Panache's semantic-wrap suite**, paraphrased rather than copied.
Three hold as Panache states them; the other three turn on an authored soft break, which this design deliberately does not preserve (§2.5), and are kept with the output it does produce so the divergence is pinned rather than rediscovered.
Panache is MIT and is a working implementation of this same cascade, so its expectations are worth borrowing even under §6.3's caution about oracles.

| case | input | required |
| --- | --- | --- |
| inline list markers | `Hear from us in 60 days. 1. Tell us your name. 2. Describe the error.` | `1.` and `2.` end lines, never start them |
| an authored break, not kept | `First sentence ends here. A question asks:` + newline + `then it continues.` | `First sentence ends here.` + newline + `A question asks: then it continues.` |
| an authored clause break, not kept | `First clause,` + newline + `second clause. Next sentence. Done.` | `First clause, second clause.` + newline + `Next sentence.` + newline + `Done.` |
| an abbreviation across an authored break | `We use tools, e.g. the parser,` + newline + `and more. End.` | `We use tools, e.g. the parser, and more.` + newline + `End.` |
| one long sentence | eighty-eight columns with no interior terminator | unchanged, at every width |
| a trailing newline | `Only one sentence.` | no empty line is emitted |

The first is the strongest block-construct test available and it is the one this list previously omitted altogether.
Both of its gaps matter and in opposite directions: the gap before `1.` must not break, because that puts an enumerator at line start where `paragraph()` escapes it to `1\.`, and the gap after `1.` must break, which leaves the marker at the end of a line where it is harmless.
The escape is the enumerator's remedy as the four-space indent is the HTML opener's (§3.3), and like the indent it is invisible to `is_md_equal`, which reads `1\.` as the `1.` it renders to.
The second, third and fourth record a deliberate difference rather than a pass: an authored soft break reaches this seam as an ordinary wrap point (§3.1), and although `node.children` still marks it, this design does not keep it, so only a hard break survives as a section boundary.
All three would pass under the add-only mode `notes/PRESERVE-MODE.md` describes, which this specification does not adopt.
