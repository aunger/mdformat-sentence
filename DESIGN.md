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

The whole configuration surface is two options, both about sentence *detection* (§4).

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
Licence MIT, matching mdformat and every plugin in its curated list.

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

Guard: return unchanged unless `node.parent.type == "paragraph"`.
An inline node's parent is the block that owns it, so the test is exact rather than heuristic.

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

| `--wrap` | `do_wrap` | behaviour |
| --- | --- | --- |
| `keep` (mdformat's default) | `False` | **Inert.** No wrap points exist, so there is nothing to act on. |
| `no` | `True` | Sentence per line. The intended mode. |
| any integer | `True` | **Identical output to `no`.** The width is deliberately not honoured. |

The third row is the surprising one and it is deliberate.
A user who passes `--wrap 80` alongside this plugin is asking for two incompatible things, and this plugin resolves the conflict in favour of its own promise rather than silently producing something that is neither.
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
for each section in inline_text.split("\n"):     # hard breaks, inline HTML
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
There is no other source of truth.
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

The two link patterns are written on one line each; the first is split above only to fit the page.
The eleven forms they were checked against are `[t](u)`, `![t](u)`, `[![t](u)](v)`, `[![t](u)][r]`, `[t](u/a_(b))`, `[t](u "title")`, `[t][r]`, `[t]`, `[a [b] c](u)`, two links in one segment, and `` `code` ``; each masks away completely and so contributes a delta of zero, which is the only property the depth counter needs.

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
terminators  . ! ? … 。 ！ ？
closers      " ' ’ ” » › « ‹ “ ‘      plus  * _ ~
openers      " ' “ ‘ « ‹ » › ¿ ¡ „ ‚  plus  * _ ~ [ ( \
```

`“` and `‘` are in both sets deliberately: they open in English and close in German.
So are the guillemets, and for the same reason: French and Swiss German write «…» while German and Austrian usage reverses them to »…«, so each of the four marks both opens and closes depending on the language.
Leaving `«` out of the closers is what would silently drop every sentence end in `»Ist das ein Test?« Dann ging er.`
Inside a segment the overlap costs nothing, because a closer is tested after a terminator and an opener before a capital, and neither test is reached from the position the other is asked about.
**A mark standing alone as its own segment is the one place where it does cost something, and set membership must not decide it there** — see the two structural rules below, which decide by what precedes the mark instead.

**Clause punctuation is not a closer, and that is what handles `e.g.,`**
A terminator followed by `,` `;` or `:` is not a sentence end, because the test scans back over *closers* only and none of those three is one, so the scan meets a character that is neither closer nor terminator and fails.
`e.g.,` and `i.e.,` are the common cases and they are very common in technical prose; `etc.;` in a semicolon-separated list and `Ph.D.,` in a byline are the same shape.
No rule is needed for them, and none is added.

The point of stating it is that the behaviour rests entirely on an *absence*.
Anyone who later adds clause punctuation to the closer set, which is a tempting thing to try when working on rule 5, silently turns every `e.g.,` into a sentence-end candidate.
The closer set is for marks that can follow a terminator *and still end the sentence*; a comma after a period means the abbreviation was not a sentence end at all.

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

| terminator | abbreviations | single initial | `require_sentence_capital` |
| --- | --- | --- | --- |
| `.` | yes | yes | yes |
| `…` | no | no | yes |
| `!` `?` | no | no | only when the first closer is a quote |
| `。` `！` `？` | no | no | no |

`…` skips the abbreviation check because no abbreviation ends in an ellipsis, so `moment… and then` correctly does not break while `moment… Nobody` does.
The CJK terminators skip both checks: a CJK opening passes the capital test anyway, and no CJK abbreviation ends in `。`.
Their wrap point exists only where the author separated the sentences with a space, which is the only case that can be acted on.
A bare `!` or `?` is unambiguous, but one immediately followed by a closing quote is not, because the question may belong to the quoted phrase rather than to the sentence carrying it.
Without that qualifier, `A "Is this a test?" guide to the whole subject…` breaks after `test?"`, stranding a 19-character fragment mid-sentence.

**The three checks:**

- **Abbreviations.**
  **The default set is English only**: `mr mrs ms dr prof sr jr st i.e e.g vs fig no vol ch sec al`.
  `etc`, `inc`, `ltd` and `cf` are deliberately **absent**: they commonly end sentences, and with `etc` present `Use commas, semicolons, etc. The next sentence…` loses a real boundary.
  The index entries carry a condition, for the reason set out after this list.
  User-supplied abbreviations (§4) are **added** to the default set, never replace it.
  Two refinements to the match, both reachable in practice: strip leading punctuation from the candidate word so `(e.g.` and `[i.e.` match, and also test the last hyphen-separated component so `Wrangell-St.` matches via `st`.
  Only this list is language-specific: the quotation rules decide opening from closing by what precedes a mark, and the terminator set covers CJK.

- **Single capital initials** — `J. K. Rowling`.

- **`require_sentence_capital`** (default true): the next sentence must open with a digit, or with an alphabetic character that is not lowercase.
  The alphabetic conjunct is load-bearing: a bare *not lowercase* is a wider set that admits `#`, `>` and `-`, and the paragraph below turns on the difference.
  Digits matter: `1976 was hot.` is a sentence opening.
  **Writing the case half as *not lowercase* rather than as *uppercase* is what carries the caseless scripts.**
  CJK, Arabic, Hebrew, Devanagari, Thai and Ethiopic are alphabetic and neither upper nor lower, so each passes without a clause of its own, while `a` and `ω` still fail.
  An *uppercase* test admits only the scripts that have case, which would leave Arabic and Hebrew prose unbreakable and the option the only way out.
  Georgian needs one carve-out, because Python reports `ა` as lowercase where the Mtavruli capitals exist: treat `U+10D0..U+10FA` and `U+10FD..U+10FF` as not lowercase.
  UAX #29 writes the same two ranges into its own `Lower` property for the same reason, so this is the standard's answer and not an invention here.
  **Verified by execution**, both the script coverage and the carve-out: it moves Georgian and nothing else.
  Opening markup is skipped first, using the opener set above.

**What an abbreviation entry is actually for.**
**Partly measured.** The repository corpus exercises none of these tokens, but Google Books English 2019 does; `notes/experiments/ngram.py` reproduces the figures, and the method's one real limitation is recorded at the end of this block.

An entry only ever does work when the next token is capitalised or a digit, because the break before a lowercase word is suppressed already — by `require_sentence_capital` at its default, and by the conditional class's own lowercase clause whatever that option is set to.
That reframes the question for every entry, from *is it also a word* to *what does it suppress that the capital rule does not already*, and it sorts them into three jobs and one mistake.

| entry | job | also a word, or sentence-final | rule |
| --- | --- | --- | --- |
| `mr mrs ms dr prof sr jr st` | precede a capitalised name | `st` only, as *Street* | unconditional |
| `i.e e.g vs` | introduce the term that follows | no | unconditional |
| `fig no vol ch sec al` | precede an index, or for `al` a citation year | `fig`, `no`, `sec` | **conditional** |

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
`He ate a fig.`, `The answer was no.` and `Wait a sec.` all end sentences, and all three lose that boundary if the entry is unconditional, which is what rumdl and `mdformat-sembr` both do.

So these suppress a break **only when the next segment opens with an index token** — a digit, or a run of one or more of `IVXLCDM` — **or with a lowercase letter**.
`No. 5`, `Fig. 3`, `Vol. II`, `Ch. IV` and `Vol. I` hold; `He ate a fig. Then he left.` breaks.

**The lowercase half is deliberately redundant with `require_sentence_capital`.**
At the option's default the capital rule has already suppressed those breaks and the clause does nothing.
With the option turned off it is the only thing between `Smith et al. showed that…` and a break, and likewise for `vol. iii` and `ch. iv`, whose lowercase roman numerals the index token does not admit.
The class carries its own guard for the same reason the block-construct rule below does: a safety property a user-facing flag can switch off is not one the rest of the design can rely on.

A digit-only test would be wrong, because roman numerals are ordinary for volumes, chapters and sections and digits alone would split `Vol. II`.
Measured: `Ch` has the single letter `D` among its five commonest continuations, so single-character labels are real and not a corner case.

**The run is deliberately not required to be two or more characters**, although that would fix one bad case: a bare `I` is the English pronoun, so `No. I think so.` is suppressed and stays on one line.
That is a *missed* break, and the alternative error is worse.
Requiring two characters splits `Vol. I of the series` after `Vol.`, which severs a noun phrase and puts `I` at the head of a line — visibly wrong output rather than merely unbroken output.
Holding a break back costs a long line; taking one that should not be taken corrupts the text.
Single-letter labels outside `IVXLCDM`, such as `Sec. A`, are not covered and will break, which is the same trade taken the same way.

**`vs` stays unconditional** although it too precedes a name rather than an index, because it is not an English word in any inflection and cannot end a sentence.

**`al` rides the index test rather than belonging to it.**
Nothing indexes anything in `Smith et al. 1990`; what follows is a citation year.
A year is digits, so the digit half of the index test fits it exactly, and the entry is placed in this class for that reuse and for nothing more principled than that.
Three things can follow `et al.`, and only two of them are obvious.
Before a lowercase word — `Smith et al. showed that…` — the break is suppressed already, so the entry changes nothing.
Before a capital — `…described by Smith et al. Then he left.` — the entry suppresses a break that should happen.
Those two alone argue for deleting `al` outright, and the third case is why that would be wrong.
**Every one of `et al`'s ten commonest continuations is a citation year** — 1990, 1991, 1992, 1989, 1993 lead them and no non-numeral appears among the ten at all — so a numeral is what typically follows.
Measure the bare token instead and the figure is 44%, because `al Qaeda` and `al dente` are not this abbreviation; the bigram is the only form that isolates it.
Digits are sentence openings (see `require_sentence_capital` above), so the capital rule does *not* suppress before one, which makes the entry **required** for `Smith et al. 1990 showed…` and makes deleting it the wrong call.
Conditioned on an index token it does all three correctly.
The reuse is not free: the roman half of the test has no meaning for a citation, and a bare `I` matches it, so `…described by Smith et al. I disagree.` is suppressed.
That is the same missed break `No. I think so.` already accepts, reached by the same route.

**`st` is a known ambiguity and no rule is offered.**
`St. Louis` and `Main St. Then he left.` both put a capital after the period, so neither the capital rule nor an index test separates them.
The measurement is reassuring but not decisive: `St` is followed by `John`, `Paul`, `Louis`, `Petersburg` and `Mary`, with the *Street* sense nowhere in the top continuations, so unconditional is the right default for prose like this corpus.
Books under-represent addresses, though, and a discriminator plausibly exists in what *precedes* the token, since *Saint* leads a name and *Street* trails one.
Neither is implemented.

**What the measurement cannot show, and why.**
The wildcard returns only the ten commonest continuations and omits punctuation from them, so every figure above is a share of that top ten rather than of all occurrences.
A 0% row means no numeral is among the ten, not that none ever follows, and the 100% row means every one of the ten is a year, not that a year always follows.
`et al. showed that…` never enters the denominator.
Google's tokenizer splits the abbreviation period off and treats it as a sentence terminator, so `Fig . 1` has a frequency of exactly zero while `Fig 1` is ordinary, and every n-gram following a period is `_END_`.
The corpus has therefore already decided the question this section is about, and decided it wrongly for abbreviations.
The figures above are from the period-less forms, which measure *index use versus word use* — the axis that sorts the table — and say nothing directly about how often each token ends a sentence.
`Sec` is the one row carrying a direct signal: `_END_` is Google's sentence-end marker, so `Sec` demonstrably ends sentences, which is why the entry is conditional.
`fig` is the clearest case the method does reach: capitalised `Fig` is 97% numerals while lowercase `fig` is 46% `tree`, so the label and the fruit separate cleanly on case, which the case-insensitive match in this design deliberately does not exploit.

**None of this departs from rumdl's reasoning, only from its implementation.**
rumdl admits an entry only if it is "almost always followed by something, not sentence-final", and files this class under "Reference abbreviations — followed by what they refer to".
The conditions above make that criterion operational instead of assuming it holds for the bare token.

**A sentence never opens with a block-construct marker, and this applies to every terminator.**
If the next segment would start `#`, `>`, `-`/`*`/`+`, a bare `\d+[.)]`, a setext or thematic run at line start, or an HTML block opener, the gap is not a sentence boundary.
The HTML entry is the one it is easy to omit, because mdformat's remedy for it is not an escape character.
`paragraph()` prefixes four spaces to any line matching an `HTML_SEQUENCES` opener that can interrupt a paragraph, so `Do not use it. <div> is a block element.` broken at the sentence end comes back as `'Do not use it.\n    <div> is a block element.\n'`.
Verified by execution against mdformat 1.0.0, with `<div>`, `<table>` and `<!-- -->`.
`is_md_equal` passes on all three, so §6.2's render-equality gate cannot catch this one and the rule is the only guard.

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
The same experiment *without* pinning produces 78- and 61-character lines at `--wrap 80`, which is the behaviour this plugin exists to avoid.

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
An ineligible sentence gap is simply pinned like its neighbours.

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

Two options, both about sentence detection, both in `[plugin.sentence]` and as CLI flags.

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `require_sentence_capital` | bool | `true` | `word. lowercase` is not a boundary |
| `abbreviations` | list | `[]` | **added** to the defaults, never replacing them |

Turning `require_sentence_capital` off re-arms nothing that protects the output: the conditional abbreviations and the block-construct rule both carry their own lowercase and marker guards (§3.3), so the option decides only whether `word. lowercase` is a boundary.

**The option is inherited, and that is the whole of its provenance.**
rumdl has it under the same name with the same default, and its trigger was one issue reporting that lowercase English prose did not reflow ([rvben/rumdl#514](https://github.com/rvben/rumdl/issues/514)); no argument from any language was attached to it there or here.
It is kept because it now costs nothing, not because a need for it has been shown, and the widened test above removes the one principled use it had.
Turning it off is not free: it makes every abbreviation absent from the default set a break site, so `Dept. of Defense` breaks after `Dept.`

CLI spelling is short, because mdformat namespaces only the argparse `dest` and leaves the flag text to the plugin (§2.4):

```
--sentence-no-require-sentence-capital
--sentence-abbreviations A,B,C
```

Every default must be `None`, for the reason in §2.4.

As with any mdformat plugin, these are CLI- and TOML-only: `mdformat.text()` does not populate `options["mdformat"]["plugin"]`, so a library caller gets the defaults.
An undocumented escape hatch exists and the test harnesses use it — `options={"plugin": {"sentence": {...}}}` reaches the seam via the splat at `_api.py:29` — but it is not a supported mdformat interface.

### 4.1 Options deliberately not provided

- **Any width, column or line-length option.** §1.
- **`avoid_escapes`.** Unnecessary: §3.3's block-construct rule is unconditional, so no break can land before `#`, `>`, `-`, an enumerator or an HTML block opener, and no escape and no four-space indent is ever added.
- **A "honour `--wrap`" mode** that would let mdformat wrap inside a sentence. That is a coherent product — GNU Emacs's `fill-paragraph-semlf` is exactly it — but it reintroduces geometric line breaks and therefore forfeits §1's property, which is the only reason this plugin exists. Anyone who wants it wants a different tool.
- **`break_words`, `strict_clauses`, `merge_short_lines`, `min_line_chars`.** No clause or width machinery exists to configure.

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

Rule 12 is declined for the reason in §1 and needs no further defence: it is a RECOMMENDED, and honouring it is incompatible with the property this plugin sells.

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
Run it over the fixtures, over the corpora, and over the fuzz corpus.

### 6.2 The rest of the gate

| Check | Required |
| --- | --- |
| width independence (§6.1) | exact, at every width |
| render equality vs baseline | 0 regressions per 4,000 adversarial paragraphs |
| idempotency vs baseline | 0 regressions per 4,000 |
| whitespace deletions vs baseline | 0 per 1,500 fixtures |
| structural property | pass |
| positive control | must fail when the plugin is absent |

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
1. The sentence-detection fixtures, which are where the remaining complexity actually lives: abbreviations, initials, the capital rule, footnote references, CJK, French spaced closers, German quotes, the `?"` case, bracket depth.
