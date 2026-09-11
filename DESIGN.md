# `mdformat-semantic-line-breaks` — design

An mdformat parser-extension plugin
that inserts [Semantic Line Breaks](https://sembr.org) into paragraph source
without changing the rendered output.

Status: design,
validated against **mdformat 1.0.0** and differentially against **rumdl 0.2.60**.

The measurements throughout were taken with a throwaway prototype.
It is deliberately not kept here —
it existed to test the design, not to become the implementation,
and a proof of concept sitting in the repository
would only be mistaken for one.
**It is not in `git log` either, and earlier drafts of this document said
it was.** The committed version (`7b42d70^`, 466 lines) predates
`strict_clauses` entirely — its clause handling is a cascade rung, i.e. the
*conditional* reading — while the code that produced §9's figures was ~580
lines and was never committed. The four commits that followed touched only
`DESIGN.md` and `notes/`. So the default column of §9.6, and §9.1's
`strict_clauses` rows, came from a working copy that no longer exists.
§14.4 says what follows from that.
The four **test harnesses** are a different matter: they are recoverable in
full from `git show 7b42d70^:tests/`.

This is the second pass.
The first pass established the hook point and a rough cascade;
this one turns the cascade into a normative algorithm,
resolves the open questions with evidence,
and replaces two guesses that turned out to be wrong.
§12 records what is still unknown.

Everything marked **verified** was executed, not reasoned about.
§13 says how far each claim was actually checked.

______________________________________________________________________

## 1. Name and identifiers

| Thing | Value |
| --- | --- |
| Distribution | `mdformat-semantic-line-breaks` |
| Module | `mdformat_semantic_line_breaks` |
| Entry point group | `mdformat.parser_extension` |
| Entry point id | `semantic_line_breaks` |
| TOML section | `[plugin.semantic_line_breaks]` |
| CLI prefix | `--semantic-line-breaks-*` |
| Python API | `mdformat.text(..., extensions={"semantic_line_breaks"})` |

The id follows the ecosystem convention of dist-name-with-underscores:
`mdformat-simple-breaks` registers `simple_breaks`,
`mdformat-frontmatter` registers `frontmatter`.

**`mdformat-sembr` was not available** — see §10.
The binding constraint is not the PyPI name but the entry point id:
mdformat loads plugins with `loaded_ifaces[ep.name] = ep.load()`
(`mdformat/plugins.py`, a plain dict assignment),
so two distributions registering `sembr` silently overwrite each other
with no warning and no error.
The id must be unique even where the dist name could coexist.

Verified: with both this plugin and `mdformat-sembr` 0.2.0 installed,
`PARSER_EXTENSIONS` holds `sembr` and `semantic_line_breaks` side by side,
and each is separately selectable.

### 1.1 Three plumbing details that bite

**The CLI option strings are hand-written; only `dest` is namespaced.**
mdformat does this (`mdformat/_cli.py`):

```python
group = parser.add_argument_group(title=f"{plugin_id} plugin")
plugin.add_cli_argument_group(group)
for action in group._group_actions:
    action.dest = f"plugin.{plugin_id}.{action.dest}"
```

So `dest="require_sentence_capital"` lands at
`options["mdformat"]["plugin"]["semantic_line_breaks"]["require_sentence_capital"]`,
and the visible flag name is whatever string we pass to `add_argument`.
Shortening the CLI prefix later costs nothing else.

**`default` must be `None` or `argparse.SUPPRESS`.**
The same loop warns otherwise:

> The `default` (…) for (…) from the (…) plugin,
> will always override any value configured in TOML.

A plugin that writes `action="store_false", default=True`
silently defeats its own TOML config.
Use `action="store_const", const=False, default=None`
and resolve the default in the plugin, not in argparse.
Verified: with the fix, `python3 -W error::DeprecationWarning -m mdformat …`
is clean,
and `[plugin.semantic_line_breaks]` keys take effect.

**`--extensions` is a whitelist, not an addition.**
`enabled_parserplugins` is *all* installed plugins when `--extensions` is absent,
and *only* the named ones when it is present.
So `--extensions semantic_line_breaks` silently disables GFM.
This matters for benchmarking against a baseline,
and it is worth a line in the README.

______________________________________________________________________

## 2. Hook point

**`POSTPROCESSORS["inline"]`.**
Not a `paragraph` renderer override, not a `paragraph` postprocessor.

The relevant mdformat 1.0.0 pipeline, in order
(`mdformat/renderer/_context.py`):

1. `text()` — escapes inline markup,
   then, if `context.do_wrap` and `_in_block("paragraph", node)`,
   replaces every run of `[ \t\n]+` with `WRAP_POINT` (`\x00`).
1. `softbreak()` → `WRAP_POINT`.
   `hardbreak()` → `"\\" + "\n"` — a backslash *and* a newline,
   glued to the preceding segment with no wrap point between them.
1. `link()` and `image()` replace every interior `WRAP_POINT` with a space,
   so a whole link or image is one unbreakable atom.
1. **← plugin runs here.**
   `RenderTreeNode.render` applies postprocessors
   immediately after the renderer for that node type.
1. `paragraph()` — splits the inline text on `\n`,
   word-wraps each section independently through `textwrap`,
   then walks *every* resulting line
   and escapes anything that would become block syntax at line start.
1. `blockquote()` / `bullet_list()` / `ordered_list()` — prefix and indent every line;
   `context.indented()` keeps `env["indent_width"]` accurate.

So the plugin's whole job is: **turn selected `WRAP_POINT`s into `\n`.**

Guard: return unchanged unless `node.parent.type == "paragraph"`.
An inline node's parent is the block that owns it,
so this is exact, not heuristic (§7.2).

§10 has empirical support for the choice:
the existing `mdformat-sembr` hooks `paragraph` instead,
and both of its observable defects follow from that.

### 2.1 Four facts about the seam that the first pass missed

**`mdformat.text()` renders twice.**
`_api.py` re-renders its own output whenever `wrap != "keep"`,
because escaping depends on wrapping.
Two consequences:
a non-idempotent plugin produces visibly unstable output rather than a subtle drift,
and the plugin must tolerate seeing its own output as input.
It does: pass 2 re-parses the inserted newlines as softbreaks,
which become `WRAP_POINT`s again,
so the plugin re-derives the same layout from a fully collapsed paragraph.

**`WRAP_POINT` and `PRESERVE_CHAR` are the same byte.**
Both are `\x00`.
They never collide because they are alive in disjoint phases:
`PRESERVE_CHAR` exists only inside `_prepare_wrap`,
which runs in step 5, after us.
At plugin time every `\x00` is unambiguously a wrap point.

**No literal `\x00` can reach us from the source.**
CommonMark requires U+0000 to be replaced with U+FFFD,
and markdown-it does so.
Verified: parsing `"a\x00b"` yields content `'a\ufffdb'`.
This is what makes `\x00` safe to use as a delimiter,
and it is the guarantee `mdformat-sembr`'s placeholder scheme would break
if it ran at this seam (§10).

**A run of consecutive `WRAP_POINT`s collapses to one space.**
`_prepare_wrap`'s regex matches `\x00+` as a unit.
So `RE_WRAP_POINT = re.compile(r"\x00+")` is the correct splitter,
and re-joining segments with a single `\x00` is lossless.

### 2.2 Why this seam

- A `WRAP_POINT` is mdformat's own assertion
  that this position may become a newline without changing the render.
  Breaking only there makes the sembr invariant structural
  rather than something we police.
- Breaks inserted here become *sections* in step 5,
  so line-start escaping and blockquote/list indentation apply to them for free.
- Any `WRAP_POINT`s left alone are still word-wrapped by mdformat.
  That is cascade priority 4, free.
- `CHANGES_AST = False` is correct.
  `_cli.py` gates `--validate` on `not changes_ast`,
  and `validate` defaults to **`True`**,
  so declaring `False` means mdformat verifies our invariant for us.
  Three caveats, all of which the second pass glossed:
  `--check` never reaches the validation branch at all
  (`_cli.py:145` compares strings and returns);
  `changes_ast` is OR-ed across *every* enabled plugin,
  so one plugin declaring `True` silently disables validation for all of them;
  and the Python API does not validate at any time.
  So it is a strong default, not a guarantee —
  and it is blind to the whitespace class regardless (§3.2).
- Postprocessors chain,
  so this composes with other plugins
  instead of fighting them over the `paragraph` renderer.

______________________________________________________________________

## 3. What the seam gives us for free

This is the core argument for the design,
and it is now backed by rumdl's own source.
rumdl carries a guard called `replaces_whitespace`,
whose docstring states the invariant precisely:

> `first` is a prefix of `text` with its trailing whitespace removed
> and `rest` a suffix with its leading whitespace removed,
> so the bytes between them are exactly what the split consumed.
> That gap must be non-empty and hold nothing but breakable whitespace the paragraph owns:
> the newline replacing it renders as a single space,
> so an empty gap inserts a word boundary the author did not write,
> and a gap holding anything else drops content.
> Whitespace inside an inline element belongs to that element,
> where it is literal (a code span) or structural (a link destination),
> never a place a line may break.

Every clause of that is a property of `WRAP_POINT`s by construction.
The guards rumdl needs and we do not:

| rumdl guard | What it protects | Why we don't need it |
| --- | --- | --- |
| `replaces_whitespace` | breaks that insert or delete a space | a wrap point *is* consumed whitespace |
| `clause_break_allowed_after` | `16:9`, `key:value`, `{cite:p}`, `cost—benefit` | no wrap point inside a token |
| `is_inside_element` / `ElementSpan` | code spans, link destinations, autolinks | `link()`/`image()` already collapsed them |
| `preceded_by_space && followed_by_space` | break-words inside words (`band` → `and`) | segments are whole tokens |
| hyphenated-word protection (sembr rule 9) | `well-known` | `[ \t\n]+` never matches `-`; `textwrap` uses `break_on_hyphens=False` |

That is roughly a third of rumdl's positional machinery
that has no analogue here.
It should not be ported.
What *does* have to be ported is everything about **which** gap to choose,
which is §4.

### 3.1 A bug we cannot have

rumdl issue #770, "MD013 semantic reflow orphans periods after parentheticals",
is the clearest single illustration.
At `line-length = 11`, `Lorem (ipsum sit). Dolor amet.` came out as:

```
Lorem
(ipsum sit)
.
Dolor amet.
```

The period was stranded on its own line.
The stated root cause is that `split_at_parenthetical`
attaches closing quotes and some punctuation after `)`,
but `is_clause_punctuation` covers only `,;:—` and not `.!?`.
It took two rounds to fix — PR #601 for closing quotes, then #770 for `.!?`.

That failure is unreachable here, and not because we guard against it.
Our segments for that input are:

```
['Lorem', '(ipsum', 'sit).', 'Dolor', 'amet.']
```

`sit).` is a single atom:
there is no whitespace between `)` and `.`,
so mdformat never emitted a wrap point there,
so no break can land there.
Verified — at `--wrap 11` the design produces rumdl's *expected* output exactly:

```
Lorem
(ipsum
sit).
Dolor amet.
```

The general rule this stands for:
**every rumdl bug about punctuation or markup detaching from its token
is structurally impossible at this seam**,
because token adjacency in the source *is* the absence of a wrap point.
Attachment rules are a whole category of work we do not have to do.

### 3.2 Where the seam stops

The seam is not total, and it has now been over-claimed twice.

**First, classification still reads raw text.**
Segment *text* contains structural punctuation —
a link destination, a code span's backticks —
and classification reads segment text.
So masking is needed for classification (§4.2),
just never for choosing split positions.
That distinction is the whole of §4.2.

**Second, and more seriously: the gap is safe, but its *edges* are not.**
`text()` converts only `[ \t\n]+` into wrap points.
Every other Unicode whitespace character survives *inside* a segment,
including at a segment edge.
`paragraph()` then runs `lines[i].strip()` on every line it emits,
and Python's `str.strip()` deletes 29 characters in total,
of which 26 are at risk here
(the other three are space, tab and line feed, which become wrap points).
So a segment whose edge is a non-breaking space
loses that character the moment the edge becomes a line edge.

The character is silently deleted, and **`is_md_equal` cannot see it**:
its own `\s+` normalisation treats the character as whitespace,
so the compared HTML is identical either way.
`--validate` passes. This is the one failure mode
the "mdformat verifies our invariant for us" argument does not cover,
and §9 must test it separately (§9.4).

Use `str.strip()` semantics to detect the at-risk set, not
`mdformat.codepoints.UNICODE_WHITESPACE`:
8 of the 26 — `U+000B`, `U+001C`–`U+001F`, `U+0085`, `U+2028`, `U+2029` —
are absent from that constant.

Whose bug this is, measured over 1,500 generated fixtures
carrying one at-risk character each, at widths 30–80:

| | fixtures where the plugin lost it and the baseline did not |
| --- | --- |
| plain mdformat, no plugin | — (it loses it on its own in 146 / 1500) |
| plugin, no guards | 68 / 1500 |
| plugin, per-gap veto | 22 / 1500 |
| plugin, veto + section decline | 13 / 1500 |
| plugin, **pinning** (§4.8) | **0 / 1500** |

So it is an **upstream mdformat data-loss bug** first —
it fires on roughly one in ten of these documents with no plugin present —
and should be reported.
Refusing to break at the gap only got this to 22, then 13.
The residual was never ours to reach by refusing:
our breaks elsewhere move mdformat's *own* wrap onto the fragile gap.
Priority 4 is not ours to veto.

**Pinning it is** (§4.8). Emitting a literal space rather than a wrap point
removes the break opportunity from mdformat's word wrap too, and takes the
figure to zero. That is the difference between declining to cause a bug and
actually preventing it, and it is why §4.8 exists.

______________________________________________________________________

## 4. Algorithm

Normative. Every step below was implemented and measured (§9).

### 4.1 Segmentation

```
for each section in inline_text.split("\n"):     # hard breaks, inline HTML
    segs  = re.split(r"\x00+", section)
    state = scan(segs)                            # §4.3's cross-segment facts
    gaps[i] = classify(segs, i, state)            # one classification per gap
    lines = layout(segs, gaps)                    # §4.5
    emit "\n".join(join(segs[s:e], gaps) for (s, e) in lines)
```

Two things in that sketch are easy to get wrong,
and the second pass got both wrong.

**A gap has three outcomes, not two.**
`join` renders each gap interior to a line as a **pin** (a literal space)
when §4.7 or §4.8 requires one, and as `"\x00"` otherwise;
only the gaps *between* lines become `"\n"`.
Rejoining segments with `"\x00"` unconditionally — as the second pass did —
silently discards pinning,
and with it the 68 whitespace deletions and 26 render regressions
that §4.8 exists to prevent.

**`classify` cannot see only two adjacent segments.**
It takes the whole segment list and an index because §4.3 needs
paren and bracket depth accumulated from the start of the section,
a look *back* past a closer-only segment for the terminator (the French rule),
and a look *forward* past `segs[i+1]` to test whether a parenthetical balances.
`scan` computes those once per section;
`classify` reads them. A pairwise signature cannot express §4.3.

Sections are laid out independently and rejoined with `\n`,
because mdformat needs those newlines preserved
(a hard break is defined by its newline;
for inline HTML, newline versus space decides block versus inline).

Segments are the atoms.
Gaps are the only legal break positions.
There is no other source of truth in the algorithm.

### 4.2 Masking (classification only)

Within a segment, blank out spans whose punctuation is structural,
preserving length so offsets stay valid:

```
code span            (?<!\\)(?<!`)(`+)(?!`)(?:[^`]|`(?!\1(?!`)))*?(?<!`)\1(?!`)
link/image dest      \]\((?:[^()\\\s]|\\.|\((?:[^()\\]|\\.)*\))*(?:\s+"[^"]*")?\)
reference label      \]\[[^\]]*\]
autolink / raw HTML  (?<!\\)<(?:[/!?]?[A-Za-z][^<>]*
                     |[A-Za-z][A-Za-z0-9+.\-]*:[^<>\s]*|[^<>\s@]+@[^<>\s]+)>
```

Literal backticks and angle brackets in prose
have already been escaped by `text()` in step 1,
so an *unescaped* delimiter marks a real construct.
Masking is used for sentence/clause detection and for paren-depth counting.
It is never used to choose a break position.

**All three of the non-trivial patterns were wrong in the second pass**,
each in the same way: a negated character class that cannot cross the very
character the construct exists to carry. All three failures are reproduced.

- **Code span.** `` `+[^`]*`+ `` cannot cross the interior backtick that a
  double-backtick span exists to carry. Against ``` ``a`b`` tail ``` it matched
  ``` ``a` ``` and left ``` b`` tail ``` unmasked, so a terminator inside a code
  span became a break candidate — the bug §4.3's closer set is said to have
  fixed at the root. The replacement takes a run of *N* backticks and closes on
  the next run of exactly *N*, which is CommonMark's own rule.
- **Link destination.** `\]\([^)]*\)` stops at the first `)`, so a destination
  containing balanced parentheses leaks one. Against
  `[Foo](https://en.wikipedia.org/wiki/Bar_(baz)) and (text) here` it consumed
  `](https://en.wikipedia.org/wiki/Bar_(baz)` and left a bare `)`, which drives
  §4.3's depth counting to -1 and misclassifies **every remaining gap in the
  section**. Wikipedia-style disambiguators are common in exactly the technical
  prose this targets. The replacement admits one level of nested balanced
  parens and an optional quoted title, which is what CommonMark permits.
- **Raw HTML.** `<[^<>\s]*>` cannot cross the space before an attribute, so it
  never matched a tag that carries one — the row is labelled "autolink / raw
  HTML" and only ever masked the autolink half. Against `<span class="x">word`
  it matched only the closing `</span>`, leaving the attribute's `"` to reach
  §4.3's closer set as an ordinary quote. The replacement matches a tag, an
  autolink URI and an autolink email address, and still declines prose like
  `a < b and c > d`.

A code span is always contained in one segment, so per-segment masking is
sound: `code_inline` is its own token type, `text()` never rewrites its
interior, and its spaces stay literal rather than becoming wrap points.
Paren depth, by contrast, accumulates across the whole section (§4.3), which
is why `scan` in §4.1 runs before classification rather than inside it.

### 4.3 Classification

One pass over gaps, highest priority wins.
The table is ordered by the **specification's own rule numbers** (§6),
not by a cascade of strategies,
because the spec's text already draws the line this design needs:

> **Rules 6 and 8 carry "or satisfy line length constraints".
> Rules 4 and 5 do not.**

That asymmetry *is* the architecture.
Rules 4 and 5 fire whether or not the line is too long;
everything below them fires only because a line is still over the width.
A four-rung cascade in which sentence breaks are merely the top rung
describes rumdl, not this design, and reading it that way is the single
most likely way to build the wrong thing (§14.2).

| Spec rule | Break at | Applied |
| --- | --- | --- |
| 4 | Sentence end | **always** |
| 5 | Clause end — `[,;:—–]` + closers, at paren depth 0 | **always** under `strict_clauses` (the default); width-driven when off |
| — | Before/around a balanced multi-word parenthetical | width-driven |
| 6 | Before a break-word | width-driven |
| 12 / 13 | Word wrap | mdformat's `textwrap`, automatic |

The parenthetical strategy maps to no spec rule.
It is a layout refinement that earns its place empirically (§4.5),
and it is listed here only so the ordering within the width-driven group
is unambiguous.

**Sentence end** — `[.!?…。！？]` followed by zero or more *closers*,
at segment end.

The CJK terminators are new in this pass and were simply missing before:
`第一句。 第二句。` came back untouched, because `。` was in no set at all.
They take no abbreviation and no capital check —
CJK has no case, so `require_sentence_capital` has nothing to test.
The wrap point is there whenever the author separated the sentences with a
space, which is the only case we can act on anyway.

**The two character sets, stated once and authoritatively.**
Both are given here in full because the second pass stated the closer set once
and then amended it eighty lines later in prose without restating it, so
anyone coding from the stated set reproduced the German bug it claimed to fix;
and it never enumerated the opener set anywhere at all.

```
closers  " ' ’ ” » › “ ‘      plus  * _ ~
openers  " ' “ ‘ « ‹ ¿ ¡ „ ‚  plus  * _ ~ [ ( \
```

`“` and `‘` are deliberately in **both** sets:
they open in English and close in German (see the quotation-mark rules below).
That is not a conflict — a closer is tested after a terminator,
an opener before a capital, and no position tests for both.

The closer set **excludes** `)`, `]`, `}` and backtick.
This is the first pass's two known bugs fixed at the root,
and it is what rumdl does
(`is_closing_quote` covers only quotes;
emphasis runs get their own branch).
Consequences, all verified:

- `` Install the `foo.` Then run… `` no longer breaks after the code span.
- `See the [docs](https://ex.com/a.b.) The next…` no longer breaks after the link.
- `An array like (1, 2, 3.) Then…` no longer breaks after the parenthetical —
  a case the first pass did not know about,
  and the reason "mask link destinations" was the wrong fix:
  the bug was never specific to links.

The cost is that a sentence genuinely ending inside parentheses —
`He left. (He came back.) Then…` —
is not detected. rumdl has the same blind spot. Accepted.

Before testing for a terminator, strip a trailing run of footnote
references: `(\[\^[^\]\s]+\])+$`.
A reference glues to the word it annotates —
`The matter at hand.[^1] This is…` gives the single segment `hand.[^1]`,
which ends in `]` and so matched nothing.
Use that narrow grammar rather than adding `]` to the closer set,
so a bare `[1]` or a citation like `[Smith 2020]` still opens no sentence.
rumdl does the same, at `text_reflow.rs:682-691`.

Suppressions, applied when the terminator is `.`:

- **Abbreviations.**
  Default set, deliberately *narrower* than the first pass proposed:
  `mr mrs ms dr prof sr jr st i.e e.g vs fig no vol ch sec al`.
  `etc`, `inc`, `ltd` and `cf` are **removed**.
  rumdl's list carries the rationale —
  "Does NOT include: abbreviations that commonly end sentences" —
  and it is right:
  with `etc` present, `Use commas, semicolons, etc. The next sentence…`
  loses a real boundary. Verified: removing it matches rumdl.
  User-supplied abbreviations are *added* to the defaults, never replace them.
- **Single capital initials** — `J. K. Rowling`.
- **`require_sentence_capital`** (default true):
  the next sentence must open with a character having no lowercase form —
  uppercase, digit, or CJK.
  Digits matter (`1976 was hot.`);
  the first pass's "first alphabetic char in `right[:4]`" got there by accident.
  Opening markup (`*_~`, quotes, `[`, `(`, `\`) is skipped first.
  The default set is English **and German**. German cannot borrow the capital
  rule to cover a missing abbreviation, because German capitalises every noun:
  the word after `bzw.` or `Abb.` is upper case whether or not a sentence
  started. Five of six ordinary German sentences broke spuriously without them.
  They are on by default rather than behind a language flag because the
  asymmetry runs one way — an abbreviation held back costs at most a missed
  break, one that is missing corrupts a sentence — and these tokens are
  vanishingly rare in English prose. `usw.` is omitted for the same reason as
  `etc.`: it commonly ends a sentence.
  Two refinements to the abbreviation match, both from rumdl and both
  reachable in practice: strip leading punctuation from the candidate word,
  so `(e.g.` and `[i.e.` match; and also test the last hyphen-separated
  component, so `Wrangell-St.` matches via `st`
  (`sentence_utils.rs:87-94`).

**A sentence never opens with a block-construct marker,
and this applies to every terminator.**
If the next segment would start a construct at line start —
`#`, `>`, `-`/`*`/`+`, a bare `\d+[.)]`, a setext or thematic run —
the gap is not a sentence boundary.

The second pass had only the enumerator half, and only for `.`.
That left P1 inconsistent in a way that reads as a bug:
for `.` the capital rule suppressed markers *by accident*
(no marker is uppercase, a digit or CJK),
so `Fine. - Dash follows` held together
while `Fine! - Dash follows` broke and picked up a `\-`.
rumdl suppresses all of them; so do we now.
This is rumdl's issue #728, reached from the other direction.

**Quotation marks are language-specific, and the second pass only knew
English.** Three separate failures, all found by reading what writers reported
to obsidian-sembr, all reproduced here:

- German closes with `“` and `‘` — the marks English uses to *open*. Including
  them in the closer set above is safe, because in English a terminator is
  never immediately followed by an opening quote. Without them
  `„Das ist wichtig.“ Dann…` produced **no break at all**.
- Spanish opens with `¿` and `¡`, German with `„` and `‚`; the second pass had
  none of the four in its opener set, which is why they are enumerated above.
- French spaces its closer off: `« Ceci est important. »`.
  That puts the closer in a segment of its own, which broke the rule twice —
  the gap *before* it would orphan the mark onto the next line, and the gap
  *after* it could not see the terminator, which is one segment further back.

So two structural rules, neither of which is about French specifically:
a segment consisting only of closing punctuation is never a break candidate,
and when the segment to the left is such a mark the terminator test looks one
segment back. Symmetrically, a segment consisting only of *opening* markup
defers the capital test to the next segment rather than failing it —
returning "no opener found" is not the same as "no sentence opens here".

**No boundary of any kind inside brackets.** Depth counts `[` as well as `(`.
A citation like `[@Smith2020, p. 12-14]` is prose brackets, its comma is a
field separator, and its `p.` is not a sentence end; without the guard it split
three ways and collected two backslash escapes.

Distinguishing prose brackets from links is free, and the discriminator is the
seam itself: mdformat collapses wrap points inside a link, so a *complete*
bracket group within one segment is link syntax, while a group arriving in
pieces across segments is prose. Depth counting removes the former and counts
the latter.

**One suppression applies to `!` and `?` too.**
A bare `!` or `?` is an unambiguous terminator,
but one *immediately followed by a closing quote* is not:
the question may belong to the quoted phrase rather than to the sentence
carrying it. So when the terminator is `!` or `?` and the first closer is a
quote, `require_sentence_capital` applies as it does for `.`.

Without this, `A "Is this a test?" guide to the whole subject…`
breaks after `test?"`, stranding a 19-character stub mid-sentence —
and because P1 is unconditional, the `MIN_SPLIT_RATIO` guard never sees it.
rumdl fixed this deliberately (`text_reflow.rs:748-750`).
Verified: the fix suppresses that break while leaving
`Is this a test? Yes it is.` and `He asked "Is this a test?" Then he waited.`
breaking as they should.

**Two marks the second pass left out, and the omission was incoherent
rather than conservative.**
`…` (U+2026) is a sentence terminator, and `–` (U+2013) is clause punctuation.

Before: `moment... Nobody` broke and `moment… Nobody` did not,
though they are two spellings of one authorial gesture;
`behaviour — every` broke at `--wrap 60` and `behaviour – every` did not,
though the spaced en dash is *the* clause dash in British and German prose.
Both verified, both now fixed, with no cost to any invariant.
`…` takes the capital rule but no abbreviation check —
no abbreviation ends in an ellipsis —
so `moment… and then` correctly does not break.
A closed range like `1914–1918` is unaffected: one token, no wrap point.

pysembr's set is wider still, adding `/` and `)`.
Neither is adopted. `)` is the mark we deliberately removed from the closer
set, and re-admitting it as a *break* point would reintroduce §3.1's bug
family from the other side; `/` is a path and URL separator far more often
than it is prose punctuation.

Decimals need no special case: `3.14` has no wrap point inside it.

**Clause end** — `[,;:—–]` + closers, at segment end,
**at paren depth 0**. A comma inside `(1, 2, 3.)` separates list items, not
independent clauses. No "must be followed by whitespace" guard is needed (§3).

**Parenthetical** — the next segment starts with `(`
and its group balances over a later gap and spans more than one segment.

**Break-word** — the next segment's first word (after opening markup) is in the list.

Break-words are **suppressed inside parentheticals**.
Paren depth is tracked per gap over masked segments.
Without this, `The configuration file (which lives in …)`
breaks before `(which` — a 22-character first line —
because `which` is a break-word.
rumdl blocks this twice over
(its `paren_depth_map`, and its requirement that the word be space-delimited).
This was a real defect in the first pass's implementation,
and it was not on its list of known ones.

### 4.4 Break-word list

Two tiers, following pysembr's structure but not its contents:

- **Core** — subordinators and relatives, which reliably introduce a clause:
  `which who whom whose because although though unless since while whereas however therefore moreover furthermore nevertheless meanwhile when where whether until once`.
- **Extended** — coordinators and light subordinators, noisier:
  `and or but nor yet so for that if as after before then than`.

**Both tiers are on by default — but the tiering itself was reasoned
backwards, and the measurement now says so.**

Under the default (rule 5 unconditional), F1 over the §9.6 corpora:

| break words | F1 @80 | F1 @ no |
| --- | --- | --- |
| both tiers | **0.650** | 0.649 |
| extended only | 0.647 | 0.649 |
| core only | 0.608 | 0.649 |
| none at all | 0.608 | 0.649 |

**The core tier is indistinguishable from having no break words at all.**
It was described above as the reliable one — the subordinators that "reliably
introduce a clause" — and that is exactly why it never fires: English usually
puts a comma before a non-restrictive `which`, `although` or `because`, so
P2 has already broken there. The tier is pre-empted by the rule it was supposed
to complement. The extended tier does all the work, because coordinators such
as `and`, `or` and `that` routinely appear with no comma in front of them.

At `--wrap no` every variant is identical: break-words are priority 3, which
only fires when a line is over width, and there is no width. So this whole
table is a width-80 phenomenon.

Keep both tiers — the core one costs nothing measurable — but the *reason* in
this section was wrong, and a reader deciding whether to prune the list should
prune from the core end, not the extended one.

The paragraph below was the original argument and is retained because its
conclusion survives even though its reasoning did not.
The first pass proposed defaulting to the core tier,
reasoning that rumdl's single flat list is noisy.
That is true, but the canonical UDHR rendering —
the one the spec and rumdl both use, and our headline regression test —
*depends on breaking before `and`*, which is an extended-tier word:

```
They are endowed with reason and conscience
and should act towards one another in a spirit of brotherhood.
```

Defaulting to core-only would fail the canonical example.
The tiering is still worth having as a documented knob
(`break_words` replaces the set outright),
but it cannot be the default.
Noted because the first pass got this backwards
and the reason is not obvious until you run it.

### 4.5 Layout

Three steps. Iterative, not recursive —
rumdl went iterative explicitly for stack safety on pathological lines,
and the reasoning carries.

```
# Step 1 — the unconditional rules: spec rule 4, and rule 5 by default.
#   Neither carries "or satisfy line length constraints", so neither
#   consults `limit`. Under `strict_clauses` (the default) CLAUSE is cut
#   here beside SENTENCE; with it off, CLAUSE drops to step 2 instead.
cuts = SENTENCE gaps
if strict_clauses:
    cuts |= CLAUSE gaps
spans = split segs at every gap in cuts

# Step 2 — the width-driven rules, for spans still over `limit`.
#   `limit` is the indent-adjusted width; under --wrap no it is infinite
#   and this step does not run at all.
for (s, e) in spans:
    start = s
    while span_width(start, e) > limit:
        pick = latest_fitting(PAREN)                            \
            or (latest_fitting(CLAUSE) if not strict_clauses    \
                else None)                                      \
            or latest_fitting(BREAKWORD)
        if pick is None: break     # rules 12/13: leave the rest to textwrap
        emit(start, pick + 1); start = pick + 1
    emit(start, e)

# Step 3 — merge stub lines
```

The second pass wrote `while width(start, e) > width`,
using one name for the measuring function and for the scalar bound.
They are `span_width` and `limit` here.

**The `CLAUSE` rung of step 2 runs only when `strict_clauses` is off,
and the second pass's pseudocode did not say so.**
Instrumenting the shipped default gives 44 parenthetical and 202 break-word
candidates and **zero** clause, across two of the §9.6 corpora —
not because clause gaps are rare, but because step 1 has already consumed
every one of them. The cascade as shipped is PAREN → BREAKWORD.
Written the old way, the rung reads as live, and an implementer who builds it
that way and then finds it never fires will conclude the instrumentation is
wrong rather than the pseudocode.

`latest_fitting` picks the **rightmost** candidate
whose first line width lies in `[min_first, limit]`,
where `min_first = int(limit * MIN_SPLIT_RATIO)` and `MIN_SPLIT_RATIO = 0.3`.
`min_first` is a pure fraction of the width and nothing else;
in particular `min_line_chars` does **not** enter it (see below).
A candidate producing a shorter first line is rejected outright,
which lets the next strategy down the cascade have a turn —
this is why the ratio check belongs inside each strategy, not around the loop.
Only parenthetical **strategy 1** is exempt from the ratio check —
the case where the span already opens with a balanced multi-word group,
which is a valid semantic line at any length.
Strategy 2, which breaks *before* the rightmost group, goes through the same
`[min_first, limit]` filter as clause and break-word.
The second pass said "the parenthetical strategy is exempt" without
qualification, which does not describe either this design or rumdl's.

Strategy priority is re-evaluated **per iteration**, not once per span.
The first pass locked onto a level for the whole span
(if any clause gap existed anywhere, break-words were never consulted),
which is not what rumdl does and produces worse layouts.

**Two thresholds shared one name in the second pass, and they are separated
here.** `min_first` filters candidates *inside* the cascade; `merge_floor`
decides which *finished* lines get folded back in step 3. The second has
roughly five times the visible effect on output, and the second pass documented
only the first, at length. They are:

```
min_first    = int(limit * MIN_SPLIT_RATIO)          # step 2, candidate filter
merge_floor  = min(min_line_chars, limit)            # step 3, stub floor
             = min_line_chars                        #   ... under --wrap no
```

The second pass instead described `min_line_chars` as "a lower bound on the
ratio", i.e. `max(int(limit * 0.3), min_line_chars)`. **That is degenerate at
narrow widths** and would have shipped: with `min_line_chars = 25`, the
candidate window `[max(int(limit * 0.3), 25), limit]` is *empty* for every
width below 25, so the whole cascade goes inert at widths 12, 16 and 20 —
exactly the widths §9.5 stresses and calls out as mattering. §12's
degenerate-width note analysed only `int(limit * 0.3)` reaching 0 and missed
this entirely.

Taking the `min` instead of the `max`, and only in step 3, is what the two
thresholds are actually for. It leaves the measured configuration untouched —
at width 80 the floor is 25 and under `--wrap no` it is 25, which is what
§9.6 scored — while making narrow widths behave sensibly rather than not at
all.

`min_first` is computed from the **indent-adjusted** width,
so content nested in a blockquote or list gets proportionally smaller stubs.
The second pass recorded this as a deliberate divergence from rumdl.
That was wrong, and it is corrected here:
rumdl subtracts the container prefix *before* the reflow call —
`config.line_length.get().saturating_sub(prefix_width).max(1)`,
at every one of its call sites
(`md013_line_length.rs:1026`, `:1326`, `:1820`, `:2047`, `:2692`, `:3527`;
`text_reflow.rs:4039`, `:4576`) —
so its ratio is already indent-adjusted too. We match it.

**Step 3, the merge pass**, and a floor that survives `--wrap no`.

`MIN_SPLIT_RATIO` is a fraction of the width, so under `--wrap no` there is no
width to take a fraction of and the merge pass did not run at all.
This is why `merge_floor` falls back to `min_line_chars` outright there. Since rule 5
became unconditional that was the mode emitting `pears,` / `plums,` / `tables,`
on lines of their own — and `--wrap no` is the mode §9.6 scores *highest*.
`min_line_chars` is an absolute floor, used alone when there is no width and
capped by the width when there is.

Its value was measured, not adopted. obsidian-sembr ratcheted its own minimum
10 → 15 → 25 in nineteen days, and 25 was the obvious number to copy; sweeping
0, 8, 12, 16, 20 and 25 against the §9.6 corpora moves weighted F1 by at most
0.01, so the floor is nearly free in agreement terms and can be set by taste.
It is 25. What matters is that it runs at all.
Any line narrower than `merge_floor` is folded into its predecessor unless:

- it is a standalone parenthetical (placed deliberately by step 2), or
- the previous line ends a sentence (those splits are intentional), or
- the merge would overflow the width.

Without it, greedy first-fit emits stubs —
the first pass produced `for details,` / `or read on.` as separate lines.

### 4.6 Structure conflicts

A break can put `#`, `-`, `>`, `1.` or a setext-looking run at line start,
where mdformat escapes it (`\#`, `\-`, `1\.`).
The render is unchanged and `--validate` passes,
but a backslash enters the source.

Default: **let it happen.**
Opt-in `avoid_escapes` demotes any gap
whose successor would trigger mdformat's line-start escaping.

The predicate must mirror **mdformat's** `paragraph()`, not rumdl's
`starts_block_construct`. They differ, and copying the wrong one is a real
trap:

- mdformat escapes *any* `[0-9]+[.)]` at line start;
  rumdl deliberately guards only a literal `1.`,
  because only `1.` can interrupt a paragraph in CommonMark.
  mdformat is stricter, so we must be too.
- rumdl also guards ```` ``` ````, `[label]:` and `|`.
  We need none of them: `text()` escapes backticks and brackets
  before we ever see the segment.
- mdformat has a case rumdl does not, and it is **not** a backslash:
  a line whose start matches an HTML block opener is prefixed with
  **four spaces** (`_context.py:461-469`), not escaped.
  `avoid_escapes` should claim that case too,
  and §9.4's normalisation must know about it.

Demotion has to **iterate**: removing one break can make the *next* gap's
successor land at a line start, so the pass repeats until no demoted gap
remains. rumdl reaches the same conclusion from the other direction —
its post-pass, `merge_block_construct_continuations`, keeps folding
until the tail is inert (`text_reflow.rs:2391`).

One case resolves itself for free.
Writing `require_sentence_capital` as *uppercase, digit or CJK* rather than
as "not lowercase" also suppresses a break before `-`, `#` or `>`,
since none of those opens a sentence.
That is why `First sentence here. - Two words…` does not break at all (§9.1),
with no `avoid_escapes` involved.

### 4.7 Correctness rules

**Edge safety.** A gap is ineligible — at every priority — when the last
character of the segment to its left, or the first character of the segment to
its right, is whitespace that `str.strip()` would delete (§3.2). Test with
`.strip()`, not with a character list. This is a correctness rule, not an
aesthetic one, and it is the only rule in §4 that exists to prevent data loss
rather than to choose a layout.

**Section decline — the one construct mdformat does not neutralise.**
`paragraph()` escapes `#`, `>`, `-*+`, `\d+[.)]`, thematic and setext runs,
and indents HTML-block openers by four spaces.
It has **no tilde case**, and `text()` escapes backticks but not tildes.
So a run of three or more tildes at a line start opens a fenced code block
and **changes the render**.

This is an **upstream** bug, and the second pass wrongly called it ours.
Plain core mdformat, no plugin, no extensions:

````python
mdformat.text("aaaaaaaa ~~~ bbbbbbbb cccccccc\n", options={"wrap": 8})
# -> 'aaaaaaaa\n\n```\nbbbbbbbb\ncccccccc\n```\n'   is_md_equal: False
````

What *is* ours is the blast radius.
mdformat only reaches the fault when its own wrap happens to land there;
our breaks land far more often and at far more widths,
so at `--wrap 60` a paragraph the baseline formats correctly
becomes a code fence under the plugin.
`is_md_equal` returns False, so `--validate` does catch it —
loudly, with exit 1 — but a formatter that corrupts a document
and then tells you so is still a formatter that corrupts documents.

A scan of 54 candidate line-start tokens at two widths found
`~{3,}` to be the **only** shape with this property.
`mdformat-gfm` escapes it, but `--extensions` is a whitelist (§1.1),
so running with our plugin alone re-arms it.

Suppressing the adjacent gap is not sufficient,
because priority 4 is not ours:
our breaks elsewhere shift where mdformat's own wrap lands,
and it can land on the dangerous gap instead —
26 render regressions in 3,000 fixtures with a per-gap guard alone.

### 4.8 Pinning: the primitive the second pass missed

A postprocessor at this seam has **two** powers, not one.
It can turn a wrap point into a newline — a break.
It can also turn one into a **literal space** — a *pin*.

A pin is not cosmetic. `_prepare_wrap` creates a break opportunity only at a
`\x00`; an ordinary space is carried through `textwrap` as a preserved
character and restored verbatim. So a pinned gap is unbreakable **by
mdformat's own word wrap as well as by us**. It is exactly the mechanism
`link()` already uses to keep a link on one line.

Verified: replacing every wrap point in an 80-character paragraph with a space
leaves it on one line at `--wrap 20` and `--wrap 40`, render-equal and
idempotent.

This is the correct instrument for §4.7's two correctness rules,
because it reaches the one actor a per-gap veto cannot:

- Pin any gap whose edge character `str.strip()` would delete.
  Whitespace deletions caused by the plugin: **68 → 0** per 1,500 fixtures.
- Pin the gaps around a tilde run.

For the tilde the pin is necessary but *not* sufficient, and the reason is
worth recording: a code span or list marker elsewhere in the same section can
re-segment the text so the fence reaches a line start by another route. So
tilde sections are **both** pinned and declined outright.
Belt and braces, and cheap: a section containing a tilde fence is a section
nobody is line-breaking for aesthetic reasons anyway.

Together the two rules give 0 render regressions and 0 whitespace deletions
in 4,000 and 1,500 adversarial fixtures respectively (§9.5),
against 26 and 68 without them.

Pinning has uses beyond correctness that this design does not yet take up —
a user-facing never-break-here, or deliberate rule-13 overflow to keep a unit
intact. §12 records them as unexplored rather than rejected.

### 4.9 Failure policy

rumdl verifies its own output and, when the check fails,
**returns the input unchanged** — its comment is worth keeping:

> the alternative is writing corrupted prose into the user's file
> (`text_reflow.rs:1101-1119`)

Adopt the same posture, and it costs us less than it costs rumdl.
Reconstruct the pre-layout section by mapping every inserted `\n` back to a
`\x00`; require byte equality with the input; on mismatch return the text
untouched. "Untouched" is not a degraded mode here — it is priority 4 of our
own cascade, so the paragraph is still word-wrapped by mdformat, just without
semantic breaks. The second pass specified no error policy at all.

______________________________________________________________________

## 5. Config surface

Line length comes from **mdformat's own `--wrap`**, not a plugin option.
This collapses rumdl's `line-length` / `reflow` / `reflow-mode` trio
into one existing knob:

| Intent | mdformat | rumdl equivalent |
| --- | --- | --- |
| Sentence breaks only, no length cap | `--wrap no` | `line-length = 0`, `reflow-mode = "semantic-line-breaks"` |
| Full cascade at 80 | `--wrap 80` | `line-length = 80`, same mode |
| Plugin inert | `--wrap keep` (the default) | `reflow = false` |

Plugin options, in `[plugin.semantic_line_breaks]`
and as `--semantic-line-breaks-*` CLI flags. All verified working:

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `require_sentence_capital` | bool | `true` | `word. lowercase` is not a boundary |
| `abbreviations` | list | `[]` | **added** to the defaults |
| `break_words` | list | — | **replaces** the default set |
| `avoid_escapes` | bool | `false` | suppress breaks that would add a `\` at line start |
| `merge_short_lines` | bool | `true` | run step 3 of §4.5 |
| `min_line_chars` | int | `25` | absolute floor for the merge pass, capped by the width when there is one (§4.5's `merge_floor`); the only threshold that applies under `--wrap no` |
| `strict_clauses` | bool | **`true`** | break after every independent clause, as spec rule 5 reads (§6). Set false to match rumdl. |

### 5.1 Plugin options do not exist under the Python API

`mdformat.text(...)` builds its options from what the caller passes.
Nothing populates `options["mdformat"]["plugin"]` —
that key is assembled by `_cli.py` from TOML and argparse,
and the Python API never runs it.
Verified: at the seam under `mdformat.text()`,
`options["mdformat"]` holds exactly `{"filename", "wrap"}`.

So every option in the table above is **CLI- and TOML-only** as far as
mdformat's documented interface goes: a library caller who passes only
`extensions=` and `options={"wrap": ...}` gets the defaults.
There is an undocumented escape hatch, and §9's harnesses need it — see below.

That is mdformat's shape, not something a plugin can fix,
but it should be documented rather than discovered,
and it argues for defaults that are right without configuration —
which is the standard §4.4's break-word decision is already held to.
A caller who needs the options can pass
`options={"plugin": {"semantic_line_breaks": {...}}}` and it will work.
Verified: `_api.py:29` splats the caller's options into `mdformat_opts`
wholesale, and the seam reads the `plugin` key back out unchanged.
It is simply not a documented mdformat interface, so it may break without
notice — but §4.4's break-word table and §4.5's `min_line_chars` sweep were
both produced through it, and cannot be reproduced without it.
(The second pass credited this to `_plugin_options`, which does not exist in
mdformat 1.0.0; the real machinery is `separate_core_and_plugin_opts` at
`_cli.py:305` plus that splat.)

### 5.2 `--wrap keep`

**Resolved: stay silent, and say so in the README.**

`do_wrap` is `isinstance(wrap_mode, int) or wrap_mode == "no"`,
so under `keep` mdformat emits no wrap points at all
and the plugin is structurally inert —
there is nothing for it to do and nothing it could do.
The first pass leaned toward warning.
Against that:
`keep` is mdformat's **default**,
and mdformat's own documentation says it is the default
*specifically* to accommodate Semantic Line Breaks written by hand.
A user who installs this plugin and keeps `wrap = "keep"`
is asking mdformat to preserve the breaks they wrote themselves,
which is a coherent thing to want.
Warning on the default configuration of the tool
would fire constantly for people doing nothing wrong.

A warning would be justified if the plugin were *explicitly* named
in `--extensions` alongside `--wrap keep`,
since that is closer to a contradiction.
Not worth the plumbing yet. Revisit if users trip over it.

______________________________________________________________________

## 6. Conformance to the specification

The [sembr specification](https://sembr.org) has **thirteen** normative rules.
The second pass said twelve and numbered them all one too low (§13).
The numbering matters: the ecosystem cites these by number —
obsidian-sembr files bugs titled "Specification 4/5 Not Fully Implemented" —
so an off-by-one makes our conformance claims uncheckable.
The block is byte-identical from the spec's initial 2019 commit to HEAD;
it has never been amended.
Mapping each to a mechanism, at `--wrap 80`:

| # | Rule | Mechanism | Status |
| --- | --- | --- | --- |
| 1 | Text MAY use semantic line breaks | the premise; we are the tool that does it | n/a |
| 2 | MUST NOT alter rendered output | breaks only at `WRAP_POINT`s; `--validate` on by default | structural |
| 3 | SHOULD NOT alter intended meaning | cascade priorities | best-effort |
| 4 | MUST occur after a sentence | P1, unconditional | yes |
| 5 | SHOULD occur after an independent clause | P2, unconditional (`strict_clauses`, on by default) | yes |
| 6 | MAY occur after a dependent clause | P3 break-words | yes |
| 7 | RECOMMENDED before an enumerated or itemized list | n/a — a list inside a paragraph is not a list | n/a |
| 8 | MAY be used after one or more items in a list | mdformat handles list structure | n/a |
| 9 | MUST NOT occur within a hyphenated word | no wrap point inside a token | structural |
| 10 | MAY occur before and after a hyperlink | wrap points surround links, but no strategy breaks *at* one | **not yet** (§14.5) |
| 11 | MAY occur before inline markup | wrap points surround emphasis | yes |
| 12 | 80 characters RECOMMENDED | `--wrap 80` | yes |
| 13 | MAY exceed the maximum where necessary | `break_long_words=False`; cascade falls through | involuntary only |

**Rule 5 was a knowing divergence for two passes. It is not any more.**
The spec says clause breaks SHOULD happen.
We made them conditional on the line being over width,
as rumdl does in its `semantic-line-breaks` mode,
on the reasoning that breaking at every comma is noisy in prose.

Measured against what two other authors actually wrote (§9.6),
that reasoning did not survive: the literal reading agreed with them better
on **eight out of eight** external measurements, at both widths,
and by the widest margin under `--wrap no`,
where the conditional reading emits no clause breaks at all.
No external measurement favoured the old behaviour,
and our own prose — the bias control — is a tie at the width we wrote it in
(§9.6).

So `strict_clauses` is **on by default**, and rule 5 is now simply conformant.
`--semantic-line-breaks-no-strict-clauses` restores the old behaviour,
which is also what matches rumdl (§9.1).

Flipping it surfaced a guard we had not needed before.
A clause boundary *inside* a parenthetical is not an independent clause —
it is a list separator — and `An array like (1, 2, 3.) Then…`
broke into `(1, 2,` / `3.)`.
Under the conditional reading that gap almost never won,
so the omission never showed. Clause gaps are now suppressed at paren depth,
as rumdl already does in `split_at_clause_punctuation`.
That is the general shape of this whole exercise:
a default that hides a missing rule is not the same as not needing it.

Rule 12 is worth checking rather than assuming.
On mdformat's own README at `--wrap 80`,
17 output lines exceed 80 characters.
All 17 are either headings (never touched)
or single link/image atoms with no interior wrap point — exactly what rule 13 permits.

______________________________________________________________________

## 7. Resolved questions

The first pass left five. All five now have answers, and two overturn it.

### 7.1 Does rumdl break at all clause boundaries, or greedily at the last that fits?

**Greedily at the last that fits, iterated until the remainder fits.**
`cascade_split_line` is a loop:
each turn re-tries parenthetical → clause → break-word on the *remaining suffix*,
takes the rightmost candidate inside `[min_first, line_length]`,
emits it, and advances.
When no strategy yields a candidate it drops out
and word-wraps the tail with `break_on_sentences = false`.
Reimplemented and confirmed byte-identical (§9.1).

### 7.2 How does this compose with `mdformat-gfm`?

**Correctly, and the guard is exact rather than conservative.**
Dumping the parent type of every `inline` node:

| Construct | `inline` parent | Broken? |
| --- | --- | --- |
| paragraph | `paragraph` | yes |
| blockquote / list item | `paragraph` | yes, re-indented |
| heading | `heading` | no |
| GFM table cell | `th` / `td` | no |
| footnote definition | `paragraph` | yes, re-indented |

Verified end to end: table rows stay on one line,
paragraphs break, and blockquote/list nesting re-indents with the right budget.

### 7.3 Do footnote and definition-list plugins hide inline nodes under other parents?

**No — and the first pass was wrong about this.**
It claimed the guard "is conservative there and suppresses all breaks."
A footnote definition's body is a `paragraph`,
so it is broken like any other paragraph,
and mdformat's footnote renderer re-indents the continuation:

```
[^1]: One sentence in the note.
    Another sentence in the note here.
```

This is the desired behaviour, arrived at for free.
Definition lists (`mdformat-deflist`) are still untested.

### 7.4 What about `mdformat-tables`?

**Blocked upstream, and worth knowing before publishing.**
`mdformat-tables` 1.0.0 declares `mdformat<0.8.0,>=0.7.5`.
Installing it alongside mdformat 1.0.0 makes pip either
downgrade mdformat to 0.7.22 or emit a dependency conflict.
`mdformat-gfm` 1.0.0 declares only `mdformat>=0.7.5`
and brings its own table rendering,
so **GFM is the supported path for tables** until that pin is fixed upstream.

### 7.5 Is the output idempotent?

**Yes, wherever mdformat itself is.**
Across 2000 randomised adversarial paragraphs, 2 inputs were non-idempotent —
and both are non-idempotent **without the plugin installed**.

Minimal upstream reproduction, no plugins involved:

```python
mdformat.text("A * * b\n", options={"wrap": 5})
# pass 1: 'A *\n\\* b\n'
# pass 2: 'A \\*\n\\* b\n'   <- differs
# pass 3: stable
```

The render is preserved at every step;
the instability is in emphasis escaping interacting with wrapping.
It converges after one extra pass.
This is an mdformat 1.0.0 bug and should be reported upstream.

The consequence for us is a testing one:
assert idempotency *relative to the no-plugin baseline*,
not absolutely.

### 7.6 Two smaller ones, closed

**Windows line endings never reach us.**
Verified by instrumenting the postprocessor:
under `end_of_line = "lf"` and `"crlf"` alike,
no `\r` is ever present in the inline string.
mdformat converts at the very end, in `file()`, long after the seam.
rumdl carries CR-stripping helpers throughout its reflow path;
we need none, and the §12 entry that called this untested is closed.
A CI fixture is still worth having, to notice if that ever changes.

**Ellipsis.** `He paused for a moment... Then he spoke.` breaks.
That matches rumdl, which does not special-case `...` at all —
the abbreviation test looks at the last whitespace-delimited word,
and stripping the trailing periods from `...` leaves nothing to match.
The first pass suppressed it under one branch of `require_sentence_capital`
and was never sure why. Keeping rumdl's behaviour.

______________________________________________________________________

## 8. Deliberate divergences from rumdl

- **Length counted in characters**,
  matching mdformat's `textwrap`,
  not rumdl's optional visual/east-asian width mode.
  Introducing `wcwidth` would desync our cascade
  from mdformat's own priority-4 wrapping,
  which is the thing that catches everything we decline to break.
  Worth stating the consequence, which the second pass left implicit:
  visual width is rumdl's *default*, arrived at by change (its issue #414),
  so a CJK or emoji line can occupy roughly twice the configured width.
  For CJK prose the question is close to moot —
  it has no inter-word whitespace, so mdformat emits no wrap points
  and the plugin is simply inert. This belongs in the README.
- **Structure conflicts are escaped, not avoided** (§4.6).
- **Clause breaks are unconditional**, where rumdl's are width-conditional.
  This is the one place we now deliberately produce different output from
  rumdl by default (§9.1), and it is the spec's reading, not ours (§6).
  `--semantic-line-breaks-no-strict-clauses` restores parity.
- **Two rumdl guard families are not ported** (§3).
- **No `atomic-spans` option.**
  mdformat already decides:
  emphasis children get wrap points and so wrap word-by-word;
  code spans and links don't and so never break.

______________________________________________________________________

## 9. Verification

Everything in this section was executed against
mdformat 1.0.0, markdown-it-py 4.2.0, rumdl 0.2.60, Python 3.11.

### 9.1 Differential against rumdl

15 hand-built cases covering the cascade, sentence detection,
abbreviations, initials, parentheticals, and block-marker collisions,
run through both implementations at width 80.

| | First pass | This pass, default | This pass, `strict_clauses` off |
| --- | --- | --- | --- |
| Identical output to rumdl | 7 / 15 | 14 / 15 | **15 / 15** |

The single default-mode difference is `clause_long`, and it is deliberate:
rumdl breaks that sentence at one clause boundary, we break it at both,
because spec rule 5 says to (§6). Compatibility with rumdl is now a *mode*,
not the default — but it is still exact, which keeps the cross-check alive.

The eight that changed:
`codespan`, `linkdest`, `parens_num` (closer set);
`paren_long` (break-words in parentheticals + `MIN_SPLIT_RATIO`);
`etc` (abbreviation list);
`ordered`, `dash_list`, `heading_hash` (enumerator guard + capital rule).

Byte-identical to rumdl on the canonical UDHR paragraph,
confirmed by running rumdl rather than by citing its README.

### 9.2 Invariants

| Check | Corpus | Result |
| --- | --- | --- |
| `is_md_equal(src, out)` | 15 cases × 4 widths | 60 / 60 |
| idempotency | 15 cases × 4 widths | 60 / 60 |
| `is_md_equal` | 3 real READMEs @ 80 | 3 / 3 |
| idempotency | 3 real READMEs @ 80 | 3 / 3 |
| `is_md_equal` | 2000 random paragraphs | 2000 / 2000 |
| idempotency vs baseline | 2000 random paragraphs | 2000 / 2000 |
| `is_md_equal` + idempotency | this document | pass |

Real-world corpus: mdformat's README, the sembr specification, the CommonMark spec README.
Random paragraphs are assembled from ~50 adversarial atoms —
bare `#`, `-`, `>`, `*`, `1.`, `|`, `===`, `---`,
code spans containing periods, links whose destinations end in `.`,
CJK terminators, fullwidth letters, footnote refs, escaped asterisks, `16:9`, `3.14`.

### 9.3 The structural property test

Stronger than `is_md_equal`, and the one worth keeping in CI.
If the plugin only ever converts a wrap point to a newline,
then normalising the output should reproduce plain mdformat's output exactly.
Normalisation must account for four things the plugin legitimately causes:

1. whitespace runs collapse (the break itself),
1. a new line inside a blockquote gains `> `,
1. **mdformat may add a backslash escape at a new line start**,
1. **mdformat may add a four-space indent at a new line start** —
   its mitigation for a line that would otherwise open an HTML block
   is an indent, not an escape (`_context.py:461-469`).

Point 4 was missing from the second pass's normaliser,
which would have reported a spurious failure
the first time a `<div>` landed at a break.
Point 3 is not obvious and is worth stating:
"the plugin only changes whitespace" is *false* as literally written.
Breaking before `-` makes mdformat write `\-`.
Verified: with escapes normalised,
2000 / 2000 random paragraphs and 12 / 12 (real file × width) pairs
are byte-identical to the no-plugin baseline.

Getting this test wrong is instructive:
the first two attempts reported failures that were all artifacts —
blockquote markers, then an unequal extension set caused by
`--extensions` being a whitelist (§1.1).

### 9.4 Unicode whitespace preservation

`is_md_equal` is structurally unable to see this class of bug (§3.2),
so it needs its own oracle, and the oracle has to be **relative**:
the plugin must never delete an at-risk character
that plain mdformat, at the same width, kept.

1,500 generated fixtures, each carrying one of 16 at-risk characters
either standing alone between two wrap points or glued to a word's tail,
at widths 30–80. Results are in §3.2's table: **0 plugin-caused deletions**
once the gap is pinned rather than merely skipped.
The absolute figure is not the interesting one —
plain mdformat loses the character in 146 of the same 1,500 —
which is exactly why the test compares against the baseline and not the source.

### 9.5 Relative render safety

The strongest invariant, and the one that actually belongs in CI.

Absolute render-equality is the wrong oracle,
because plain mdformat already breaks the render on some inputs
(an unescaped tilde fence reaching a wrapped line start, §4.7).
Holding ourselves to an absolute standard mdformat itself does not meet
would mean either failing forever or weakening the test until it says nothing.
The invariant that is genuinely ours:

> if plain mdformat preserves the render at this width, so must we —
> and if plain mdformat's output is a fixed point, ours must be too.

4,000 random paragraphs drawn from 74 adversarial atoms —
the §9.2 set plus `~~~`, `~~~~`, `##`, `12)`, ```` ``` ````, `[^1]:`, `[ref]:`,
`<div>`, `<script`, `<!--`, `:::`, `$$`, `-8<-`, `=== "Tab"`, `{{ .Title }}`,
unbalanced paren fragments, CJK terminators and bare NBSP —
at widths 12, 16, 20, 30, 40, 60, 80 and `no`.
Widths below 20 matter: they are where mdformat's own escaping gets strange.

| | result |
| --- | --- |
| render regressions vs baseline | **0 / 4000** |
| idempotency regressions vs baseline | **1 / 4000** |

The one is the escaping instability of §7.5 —
an upstream defect our break placement can flip a document into or out of,
not a defect of the cascade. It converges on the next pass, as that does.

Without §4.7's rules the render figure is 26 / 3000;
without §4.8's pinning the idempotency figure is 8 / 4000.

**The baseline must name `extensions=set()` explicitly.**
An earlier run of exactly this test was invalidated because a competitor
plugin had been installed into the environment mid-session: with no
`extensions` argument mdformat enables *every* installed plugin (§1.1),
so the "plain mdformat" baseline silently included someone else's line
breaking. The trap is documented two sections earlier in this document and
was still walked into. Pin the extension set on both sides of every
comparison.

### 9.6 Quality: agreement with hand-written semantic line breaks

Every figure above measures *correctness*. None of them says the breaks are
good ones. This is the first measurement in this document that does.

**The oracle.** A document a human wrote in semantic line breaks *is* a
labelled corpus: the newline positions inside a paragraph are the labels.
Collapse each paragraph to a single line, format it, and compare the break
positions the formatter chose against the ones the author chose. Precision is
"of the breaks we made, how many did the author also make"; recall is "of the
author's breaks, how many did we find". Paragraphs where formatting changed
the word count are skipped, so positions always align.

**The corpora.** Four documents by three other authors —
the sembr specification (Mattt), mdformat's `docs/users/style.md` and
`README.md` (hukkin), and `admk/sembr`'s README (Xitong Gao) —
85 multi-line paragraphs.
`DESIGN.md` is measured separately and **deliberately not pooled with them**:
we wrote it, so it is a control for bias, not evidence.

**The extractor had a bug, and it contaminated the first published figures.**
It dropped a list item's *marker* line but kept the item's continuation lines,
which were then collected as a "paragraph" beginning mid-sentence. In the sembr
specification that produced four fragments of the numbered rules — a "paragraph"
starting `MUST occur after a sentence,` — plus three `<pre>` blocks: **7 of 29
were junk**. A first check for paragraphs starting lowercase found none and
looked clean, which it was not: the rule continuations begin `MUST` and `SHOULD`.
List items and HTML blocks are now dropped as whole units.

**The harness also fails open, and a partial failure raises the score.**
`measure()` wraps both `mdformat.text` calls in a single
`except Exception: continue` (`notes/quality-harness.py:77-81`).
Three consequences, all measured.
A missing plugin raises `KeyError: 'semantic_line_breaks'` —
a configuration error, not a formatting one — and is swallowed,
producing output byte-identical to "this file had no multi-line paragraphs",
exit 0.
Because the one `try` covers both calls,
a plugin failure also destroys that paragraph's *baseline* datum.
And discarding a failed paragraph is not neutral:
a stub raising only on paragraphs over 25 words moved `style.md` @80 from
**F1 0.07 to 0.17**.
The paragraphs a broken implementation fails on are the hard ones,
and dropping them instead of scoring them zero rewards the failure.

Required before any figure in this section is quoted again:

1. **Startup probe.** Format a known two-sentence paragraph with `EXT` and
   assert a break appears. `sys.exit(2)` if it raises *or* if the output is
   unchanged. This is §12's positive control at harness scope: without it a
   clean run cannot distinguish a working plugin from an absent one.
1. **Narrow the `except`** to the formatting exception, and give the plugin and
   baseline calls **separate** `try` blocks, so a plugin failure costs one
   datum and not two.
1. **Count the discards separately** — `skipped_exception` and
   `skipped_wordcount` — and print both beside `used` and the corpus paragraph
   total. A run with `skipped_exception > 0` is void, not low-scoring.

The joint word-count guard at `:84-86` has the same shape and needs the same
treatment.
It drops a paragraph when *either* side changed the word count,
so the plugin is only ever scored where plain mdformat is also well-behaved —
and §9.4's deletion bug is precisely what changes a baseline word count.
It discards 0 of 85 today, so the bias is latent;
it fires the moment a reimplementation's escaping differs from the prototype's.

No figure in this section is admissible from a run that did not print
`skipped_exception = 0` and a `used` equal to the corpus paragraph count.

**All of this is now fixed, in `tests/quality_harness.py`.**
`notes/quality-harness.py` is kept unchanged as the historical record this
section cites by line number; the working harness lives under `tests/` and
differs in four ways. It runs a startup positive control and **refuses to
report F1 for an inert plugin** unless `--allow-inert` is passed explicitly.
It extracts paragraphs by walking markdown-it's token stream rather than by
regex, which removes the fence-parity, `<pre>`, loose-list, setext and
tab-indent defects structurally, and it drops paragraphs carrying no prose
outside links, which is what CI badge runs are. It aggregates, so the weighted
row can be read off its output — and prints the pooled micro figure beside it,
because the two differ and micro is the defensible one. And it reads UTF-8
explicitly, splits on `\n` rather than `splitlines()`, and strips only spaces
and tabs.

**The corpora are now pinned by commit SHA** in `tests/fetch_corpus.py`. The
second pass fetched from branch tips, so every figure below was measured
against a moving target; the `admk/sembr` README alone has gained a release
note since. Re-pinning is a deliberate act that belongs in a commit which also
re-reports the numbers.

F1 against the author's own break positions. "conditional" is the old
behaviour, still available as `--semantic-line-breaks-no-strict-clauses`;
"default" is rule 5 read literally, with the paren guard of §6.

**"Weighted" means the paragraph-count-weighted mean of the per-corpus F1**,
with weights 24 / 13 / 15 / 33 summing to the 85 paragraphs above. The second
pass never defined it anywhere, and the surviving harness cannot print it —
`measure()` returns only P/R/F1 per file and lets the raw counts go out of
scope, so the row has to be computed outside the tool. Under this definition
four of the five aggregate cells below reproduce exactly.

The fifth did not, and the published figure was wrong: **word wrap only,
weighted @80 is 0.10, not the 0.13 the second pass printed.** No other natural
scheme yields 0.13 either (pooled micro F1 0.1044, unweighted macro 0.1199,
gold-weighted 0.0961) — but pooled micro-averaged *precision* is 0.13021,
which is almost certainly what was transcribed into an F1 cell by hand. The
per-corpus range that the "cascade is doing real work" argument rests on is
unaffected, since that argument reads down the column, not across it.

| Corpus | width | conditional | **default** | word wrap only |
| --- | --- | --- | --- | --- |
| sembr spec | 80 | 0.45 | **0.56** | 0.03 |
| sembr spec | no | 0.26 | **0.55** | 0.00 |
| mdformat `style.md` | 80 | 0.75 | **0.81** | 0.07 |
| mdformat `style.md` | no | 0.65 | **0.86** | 0.00 |
| mdformat `README.md` | 80 | 0.68 | **0.74** | 0.31 |
| mdformat `README.md` | no | 0.53 | **0.72** | 0.00 |
| `admk/sembr` README | 80 | 0.52 | **0.61** | 0.07 |
| `admk/sembr` README | no | 0.29 | **0.61** | 0.00 |
| **external, weighted** | **80** | **0.56** | **0.65** | 0.10 |
| **external, weighted** | **no** | **0.38** | **0.65** | 0.00 |
| *`DESIGN.md` (ours)* | *80* | *0.57* | *0.57* | *0.14* |
| *`DESIGN.md` (ours)* | *no* | *0.38* | *0.58* | *0.00* |

**The word-wrap column has been re-measured against the pinned corpora with
the fixed harness, and it moved.** Everything else in the table above is still
the second pass's unreproducible measurement; this column is not, because a
baseline needs no plugin:

| Corpus | paragraphs | word wrap only @80 | second pass |
| --- | --- | --- | --- |
| sembr spec | 23 | 0.03 | 0.03 (24 paragraphs) |
| mdformat `style.md` | 13 | 0.07 | 0.07 (13) |
| mdformat `README.md` | 14 | **0.26** | 0.31 (15) |
| `admk/sembr` README | 32 | **0.04** | 0.07 (33) |
| **external, weighted** | **82** | **0.08** | 0.10 (85) |
| *micro, pooled* | | *0.08* | |

The three paragraphs that vanished are the CI badge runs, one per README plus
one in the spec's `<pre>` blocks; the two columns that moved are the two
corpora that carried badges. Every badge line exceeds 80 characters, so no
formatter can break inside one and every formatter scored a free true positive
on it. That is where a third of `admk`'s old figure and a sixth of mdformat's
came from.

Three things follow.

**The cascade is doing real work.** Plain word wrap scores 0.03–0.26,
weighted 0.08. Whatever else is true, the breaks are not incidental.

**Reading spec rule 5 literally is better, on every external measurement.**
**Eight out of eight**, at both widths, for all three authors — and the margin is largest
exactly where the old design was weakest, at `--wrap no`, where the conditional
reading emits no clause breaks at all (0.38 → 0.65).
This is why it is now the default (§6).
Recall in particular moves from 0.33 to 0.97 on `style.md`:
under the conditional reading we were simply not making most of the breaks
its author made.

**The bias control is now a tie, not a loss.** At width 80 on `DESIGN.md` the
two readings score identically, 0.57. On the contaminated corpus the conditional
reading appeared to *win* here, 0.62 to 0.58 — the junk paragraphs were
inflating it on our own document specifically. Fixing the extractor removed the
one measurement that had ever favoured the old default, so **no measurement
now favours the status quo** — not the eight external ones, and not the bias
control, which is a tie. Recording it because it is the clearest evidence
in this project that self-evaluation does not work: had `DESIGN.md` been the
only corpus, the conclusion would have been the opposite of the truth.

Caveats, stated plainly: 85 paragraphs across three authors is a small sample;
all three are technical writers writing documentation; and F1 against one
person's choices measures *agreement*, not quality. A blind human comparison
is still the thing that would settle it (§12).

### 9.7 Competitor behaviour

`mdformat-sembr` 0.2.0 on mdformat 1.0.0, both defects reproduced:

- `First sentence here. 1. Two words follow along.` → **exit 1**,
  `Formatted Markdown renders to different HTML than input Markdown`.
- `--wrap 60` **neutralized** — the plugin collapses whitespace on already-wrapped
  text, leaving a 103-character line.

______________________________________________________________________

## 10. Prior art

| Project | What it is | Relevance |
| --- | --- | --- |
| [sembr/specification](https://github.com/sembr/specification) | The spec itself | Normative. §6 maps all thirteen rules. |
| [rvben/rumdl](https://github.com/rvben/rumdl) | Rust linter, `MD013` reflow modes | Most complete implementation. The algorithmic source. |
| [isotopp/pysembr](https://github.com/isotopp/pysembr) | Dependency-free Python splitter | **rumdl's own design source** — see below. Two-tier word lists. |
| [bugrasan/mdformat-sembr](https://github.com/bugrasan/mdformat-sembr) | Existing mdformat plugin, PyPI 0.2.0 | Direct competitor and cautionary example. |
| [admk/sembr](https://github.com/admk/sembr) | Transformer-based line breaker | Different approach (ML inference). Holds the `sembr` PyPI name. |
| [semlf](https://pypi.org/project/semlf/) | Rule-based detector for coding agents | Naming precedent; unexamined. |
| [chrisgrieser/obsidian-sembr](https://github.com/chrisgrieser/obsidian-sembr) | Obsidian plugin | Unexamined. |

### rumdl

Read at 0.2.60, not the 0.2.43 the first pass used;
`src/utils/text_reflow.rs` is now 6,430 lines.
The functions that matter, and what each contributed:

| Function | Contribution |
| --- | --- |
| `cascade_split_line` | the iterative driver (§7.1) |
| `reflow_elements_semantic` | three-step shape; the merge pass |
| `split_at_clause_punctuation` | `MIN_SPLIT_RATIO` placement inside strategies |
| `split_at_break_word` | rightmost-fitting selection; paren suppression |
| `split_at_parenthetical` | both strategies; ratio exemption |
| `is_sentence_boundary` | the closer set; the capital rule; enumerator guard |
| `sentence_utils.rs` | abbreviation list and its exclusion rationale |
| `replaces_whitespace` | the invariant statement quoted in §3 |

`merge_block_construct_continuations` was read and **not** ported (§4.6).

### pysembr

Two-tier word lists (English and German), which is the structure §4.4 borrows.
Punctuation set is wider than rumdl's: it adds `–`, `…`, `/`, `)`.
Protected spans cover link and image syntax via one regex,
`!?\[[^\]]*\]\([^)]+\)` — but **not** code spans,
so pysembr has the same code-span bug the first pass's prototype had.
`_is_hyphenated_at` exists to enforce sembr rule 9;
we get that from the seam.

**pysembr is where rumdl's cascade comes from.**
rumdl issue #388, "Implement "semantic line breaks" reflow mode"
(opened by jankatins, 2026-02-08, closed),
requests the feature by linking
`isotopp/pysembr/blob/753e0e6/src/pysembr/sembr.py#L305-L309`
and quoting that function's docstring as the specification:

> The function first splits at sentence punctuation (`. ! ?`).
> If the line is still longer than `width`,
> it splits at additional punctuation, then at language-specific break words.
> When `extended` is True,
> conjunctions and prepositions are used as a last fallback.

That is the cascade, and it is the ancestor of ours.
The first pass asserted this lineage without being able to check it;
it is now verified against the issue and against `753e0e6`,
which is pysembr's current HEAD.

One detail matters for §4.4.
In pysembr the extended tier is *a last fallback*, gated behind a flag.
rumdl flattened both tiers into a single `BREAK_WORDS` list when it
implemented the issue, which is why its output breaks before `and` by default —
and why the canonical UDHR rendering depends on a word pysembr would not use
unless asked. Our default follows rumdl, knowingly (§4.4).

Not on PyPI; read from the repository.

### bugrasan/mdformat-sembr

PyPI 0.2.0, first published 2026-07-02, requires `mdformat>=1.0`.
Canonical home is Codeberg; the GitHub repo is a publishing mirror.
Its README discloses that it was built by agentic coding.
All six commits landed on a single day.
I could not see the Codeberg side, so treat that as a floor.

It hooks `POSTPROCESSORS["paragraph"]`,
does sentence breaks only by default with clause breaks behind a flag,
uses a `min_chars=15` guard,
and has no break-word tier or width cascade.
Both defects in §9.7 follow from hooking after step 5 of the pipeline.

**What it does better than us**, and the list is longer than the second pass
allowed. Its CLI arguments use `default=None` (§1.1). It ships `py.typed`.
Its core has no mdformat imports at all, so the algorithm is testable without
the renderer. Its abbreviation handling is a single backward alphanumeric scan
that gets `(e.g.` and `Wrangell-St.` structurally, where §4.3 needs three
separate rules. It exposes `clause_chars` as a knob, which turns §4.3's
punctuation argument into a user's decision rather than ours. And its
`test_plugin_discovery.py` tests the things §11 currently has no plan for:
entry-point registration, the declared interface surface, `--version`, the CLI
through a subprocess, and — the only way to exercise it — a real
`.mdformat.toml` written into a temp directory with `cwd=` set.

Its table guard turns out not to be something we need, but not for the reason
§7.2 gives: without a table plugin, a pseudo-table's inline parent *is*
`paragraph`. What protects us is §5.2 — at `--wrap keep` we are inert, and at
any numeric wrap plain mdformat has already flattened the pseudo-table before
we run.

**Six defects beyond the two in §9.7**, all reproduced, and worth listing
because each is a fixture we should own: hard breaks are destroyed (`\` +
newline becomes a literal `\ `, at `--wrap keep`, the default); all Unicode
whitespace is collapsed on every paragraph, invisibly to `is_md_equal`;
sentence detection is ASCII `[A-Z0-9]`, so German, French, Spanish and CJK
never break at all; `min_chars` is measured on *masked* text, so a 54-character
segment counts as 12; masking blocks sentence breaks before any link or code
span; and only one opening-markup character is skipped, so `**Bold**` never
opens a sentence. All 45 of its own tests pass — none of its fixtures contains
a hard break, a non-breaking space, or a non-ASCII opener.

That last fact is the useful one. It is not a careless project; it is a project
whose test corpus did not include the inputs that break it. §9.2's atom list
exists for that reason, and §11 should carry a hard-break fixture explicitly.

Its `_sembr.py` masks with `\x00`-delimited placeholders
(`_PLACEHOLDER = "\x00{kind}{index}\x00"`).
At the `paragraph` seam that is safe.
At the `inline` seam it would collide with mdformat's own sentinel outright.
Cautionary for anyone porting its approach inward.

Worth reporting the exit-1 case upstream regardless of whether we ship separately.

______________________________________________________________________

## 11. Packaging

The repository holds this document, `CLAUDE.md`, `notes/`,
and the package below, which is configured for the **`uv`** ecosystem.
Everything here exists; only the algorithm does not.

```
pyproject.toml          # flit_core, requires-python >=3.10, mdformat only
LICENSE                 # MIT, as are mdformat and all 19 plugins it lists
src/mdformat_semantic_line_breaks/
  __init__.py           # version + the interface re-exported
  _plugin.py            # ParserExtensionInterface; §4 is NOT implemented
  py.typed
tests/
  fixtures.md           # mdformat's own fixture format
  test_fixtures.py      # fixtures, invariants, and §12's positive control
  cases.py              # §9.1's fifteen cases -- the only surviving copy
  atoms.py              # §9.5's 74 atoms, §9.4's 16 at-risk characters
  test_invariants.py    # §9.2's 60/60
  test_structural_property.py   # §9.3
  test_fuzz.py          # §9.4 and §9.5, both relative oracles
  test_differential_rumdl.py    # §9.1; skips without a pinned rumdl
  quality_harness.py    # §9.6; supersedes notes/quality-harness.py
  fetch_corpus.py       # third-party documents, pinned by SHA, not vendored
```

`flit_core` settles what this section previously left open ("hatchling or
setuptools"): it is what `mdformat-gfm`, `mdformat-tables` and
`mdformat-footnote` all use.

```toml
[project.entry-points."mdformat.parser_extension"]
semantic_line_breaks = "mdformat_semantic_line_breaks"
```

`requires-python` must be `>=3.10`, not `>=3.9`:
mdformat 1.0.0 itself declares `>=3.10`,
so a `>=3.9` floor alongside `mdformat>=1.0` is uninstallable on 3.9 anyway.

Dependencies: mdformat only. No `wcwidth`, no `regex`, nothing else.
The test extras are `pytest` and `pytest-randomly`; `markdown-it-py`, which
`tests/quality_harness.py` parses with, arrives with mdformat itself.

**Licence: MIT.** mdformat is MIT, and so is every one of the nineteen plugins
in its curated list at `docs/users/plugins.md` — eight code formatters, nine
parser extensions and two misc, by six different authors. There is no second
licence anywhere in this ecosystem, `mdformat-sembr` included.

**The seam is more public than the second pass thought.**
It called `do_wrap` and `WRAP_POINT` internal API. They are not.
`mdformat.renderer.__all__` exports `WRAP_POINT`,
`do_wrap` is a documented property,
and the 0.7.4 changelog added both *explicitly for plugin authors*:

> - `mdformat.renderer.WRAP_POINT` for plugins to show where word wrap is
>   allowed to occur.
> - `mdformat.renderer.RenderContext.do_wrap` for plugins to check whether
>   word wrap is enabled.

Only `env["indent_width"]` is undocumented,
and upstream considers that a gap rather than a deliberate boundary:
issue #235, "Document `RenderContext.indented`", is open and was filed by the
maintainer.

So the honest pin is a **range, not an exact version**.
The floor is set by `add_cli_argument_group` (0.7.19), not by 1.0;
no plugin-API break landed in 1.0.0
(its removals were deprecated several releases earlier),
and nothing has touched `POSTPROCESSORS`, `WRAP_POINT`, `do_wrap`
or the wrap pipeline since 0.7.4.

Caveat, and it is the reason not to just write `>=0.7.19` today:
**we have only ever tested against 1.0.0.**
Widening the floor is a claim to be earned with a CI matrix, not asserted here.
Ship `mdformat>=1.0,<2` and widen downward once the matrix is green.

What genuinely is unguaranteed is the **style** pipeline —
the escaping and wrapping decisions in `paragraph()` —
which mdformat's changelog explicitly declines to stabilise.
That is what §9.3 and §9.5 protect against,
and a property test that fails loudly when the seam moves
is worth more than any version range.

______________________________________________________________________

## 12. What is still open

**Known defects.**

- `First sentence here. 1. Two words follow.` produces
  `First sentence here. 1.` / `Two words follow.` —
  the enumerator is kept off the line start, but it strands on the previous line.
  rumdl does exactly the same thing, so we match, but neither reads well.
  The nicer output keeps `1. Two words follow.` together
  and accepts the escape, which is what `avoid_escapes` does *not* currently do.
  Worth revisiting as a third policy.
- `avoid_escapes` is implemented but only lightly exercised,
  and its predicate has not been re-checked
  against §4.6's corrected mdformat-vs-rumdl list.
- 1 idempotency regression per 4,000 adversarial paragraphs (§9.5) —
  the figure is 8/4000 *without* §4.8's pinning, and the second pass quoted
  that one here as though it were the shipped result,
  all downstream of the upstream escaping instability of §7.5.
  Not ours to fix, but ours to keep measured.

**Three upstream mdformat bugs, all found here, all confirmed new.**

Checked against the issue tracker (open and closed), the changelog,
and master. Master is byte-identical to the installed 1.0.0 across
`src/mdformat` — HEAD is one commit past the 1.0.0 tag and touches only
`README.md` — so nothing here is fixed or in flight.
All three require `wrap != "keep"`, which is why they have survived:
mdformat's own fuzzer runs with default options, i.e. `wrap = "keep"`.

1. **Non-idempotent emphasis escaping** (§7.5).
   `mdformat.text("A * * b\n", options={"wrap": 5})` converges only on pass 3.
   Nothing in the tracker reports it.
   The report writes itself, because **it fails mdformat's own test**:
   `tests/test_commonmark_spec.py` already asserts `md_new == md_2nd_pass`,
   but parametrises wrap over `["keep", "no", 60]`.
   CommonMark spec example 55 — `_ _ _ _ a` — fails that assertion at
   wrap 5 and wrap 8. Verified. The fix to the *test* is one list entry.
1. **Unicode whitespace deleted at a wrapped line edge** (§3.2).
   Data loss, and `is_md_equal` cannot see it, so `--validate` passes.
   Cite **#339, "`--wrap` removes unicode spaces"** (closed, fixed by PR #341
   in 0.7.15): same symptom, fixed one layer earlier in `_prepare_wrap`.
   Our case is the later `lines[i].strip()`, which that fix never reached.
   It is decisively **not** intended behaviour:
   `tests/data/wrap_width_50.md` carries a case titled
   *"Only use space, tab and line feed as wrap points"*
   that pins literal preservation of U+00A0, U+1680 and U+2000 through wrapping.
   The characters survive there only because they sit mid-line,
   where `.strip()` cannot reach them.
1. **A tilde fence is not escaped at a line start** (§4.7).
   `paragraph()` neutralises every other block opener; `~{3,}` changes the
   render. Reproducible in core mdformat with no plugin and no extensions.
   Report it against `extensions=set()`: `mdformat-gfm` escapes `~`,
   and the CLI auto-enables installed plugins while the Python API does not,
   so a maintainer reproducing from a CLI transcript may not see it.

Filing these is probably worth more to the ecosystem than the plugin is.

**Untested.**

- `mdformat-deflist`, `mdformat-toc`, `mdformat-frontmatter`, MyST.
  deflist now has a concrete motivation rather than a vague one:
  without the plugin, a `: term` line is ordinary paragraph text,
  so it is ours to break and we may break it wrongly.
- Very large paragraphs; no performance work has been done at all.
  The layout is O(segments) per pass with a masking regex per segment.
  Cache masks **per segment, never per suffix** —
  the mask regex uses lookbehind, so a suffix key is unsound.
- Degenerate widths. mdformat clamps to `max(1, wrap - indent_width)`,
  and at a width of 3 or less `int(limit * MIN_SPLIT_RATIO)` is 0,
  so the candidate filter silently switches off.
  Nothing crashes; it is simply unguarded.
  The *other* degenerate case — a merge floor larger than the width, which
  made the cascade inert below width 25 — is fixed in §4.5.

**Design questions with no evidence yet.**

- Language selection was framed as a break-word question. It is mostly an
  **abbreviation** question: the break-word *tiering* barely moves the numbers
  (§4.4 — though the extended tier itself is worth 0.042 F1, the largest tuning
  effect measured here), while a missing abbreviation produces a spurious break
  in the middle of a sentence. German is now covered; French, Spanish and Italian are not.
- pysembr's wider clause punctuation (`–`, `…`, `/`, `)`) is a set of
  decisions we have not made. `/` in particular looks wrong for prose.
- Is `MIN_SPLIT_RATIO = 0.3` right for us, or is it tuned to rumdl's corpus?
  It is a magic number we adopted wholesale.
- **Emphasis spans.** rumdl makes a short `*…*` opaque to the cascade,
  so it never breaks at a break-word inside emphasis; we will.
  Aesthetics only, and the opposite case is in our favour:
  `**First. Second.**` → `**First.\n Second.**` comes free from the seam,
  and was a data-loss bug rumdl had to fix.
- **`[label]` as a sentence opener.** `context.env["references"]` is available
  at the seam — verified, keyed by uppercase label, and absent entirely when
  the document defines none, so any use must be `env.get("references", {})`.
  That would let a defined `[ref]` open a sentence while a bare `[Smith 2020]`
  does not. rumdl cannot do this at all, since it reflows each paragraph in
  isolation. Unimplemented; the mechanism is confirmed to exist.

**An escape hatch, which the second pass wrongly wrote off.**

rumdl has inline escape hatches — `<!-- rumdl-disable MD013 -->`,
`-disable-line`, `-configure-file` — and uses them in its own documentation
to stop MD013 mangling its examples. semlf ships one too.
mdformat has no equivalent, and the second pass concluded
"not something we can fix from a plugin."

That is wrong. Verified: from the inline seam,
`node.parent.previous_sibling` is the preceding block,
and for an HTML comment it is an `html_block` whose `.content` is
`<!-- sembr: off -->` verbatim. A per-paragraph directive is implementable
today, in a few lines, with no mdformat change.
Unimplemented, but it is a feature we declined to build,
not a limitation of the seam. Worth doing: a document with one hand-laid-out
paragraph is a real and common case, and it is the only way a user can
disagree with us locally.

**Quality is now measured, but thinly** (§9.6).

The agreement-with-the-author metric exists and produces numbers, and it has
already settled two questions that were previously taste: the extended
break-word tier earns its place (§4.4 — both tiers score 0.650 weighted @80
against 0.608 for core-only, which is itself indistinguishable from having no
break words at all), and spec rule 5 read literally beats our width-conditional
reading eight times out of eight.
The second pass quoted 0.32 / 0.39 / 0.30 here, which are pre-extractor-fix
figures on a different scale from §4.4's and reverse its conclusion:
calibrating against them, a run producing ~0.39 looks correct while missing
the §14.4 gate by a factor of 1.7.

What is still missing:

- **A bigger corpus.** 85 paragraphs, three authors, all writing technical
  documentation. Hand-written sembr is rare enough that finding more is real
  work.
  An earlier draft of this section said `admk/sembr` "publishes a LaTeX dataset
  that may be adaptable". **It does not.** `huggingface.co/api/datasets?author=admko`
  returns `[]`, the account's overview reports `numDatasets: 0`, and across 107
  commits the repository has never contained a `data/` path or any `.tex`,
  `.jsonl`, `.parquet` or `.csv` file — `data/` is gitignored. The models are
  public and MIT; the corpus behind them is not. What the project *did* yield
  is its README, which is hand-written sembr by a third author and is now one
  of the four corpora above.
- **A label-free metric** — a severed-clause rate, counting lines that end
  mid-phrase. It needs no corpus, so unlike §9.6 it could run in CI on any
  document. Not built.
- **A blind human comparison.** semlf's methodology is detailed enough to
  copy: a compliant corpus, a positive control, false positives recorded in
  either direction, three blind passes on a `true/false/ambiguous` scale, and
  a sealed holdout. This is the only thing that would settle whether
  `strict_clauses` should be the default.
- **Behaviour below 60 columns**, where quality is widely reported to degrade
  and where we have measured correctness only.

**More is now known about the ceiling than about our distance from it.**
On the specification's own document roughly a fifth of the author's breaks fall
at subject|predicate boundaries carrying no lexical marker at all. No
break-word list reaches those, so a chunk of the residual is not tuning error
but a limit of the approach. That reframes the F1 figures: the interesting
question is not why they are not 0.9, but which of the reachable breaks we
still miss.

Two concrete strategies the spec's own author uses and we do not:
**breaking before a hyperlink** (rule 10) accounts for around 9% of his breaks
and around 9% of hukkin's, and is unusually cheap for us because `link()`
already makes a whole link one segment; and the spec writes its em dash as a
spaced ASCII `---`, taking a rule-5 break on it, which we cannot currently
reproduce in a document that is one of our own corpora. Neither is implemented.

**§9 needs a positive control, and does not have one.**

Every check in §9.2 through §9.5 asks "did the plugin avoid breaking
anything?" None of them asks "did the plugin insert a break at all?"

The obvious test to reach for — assert the output differs from the input — is
**wrong**, and it is worth saying why, because returning the input untouched is
frequently the correct answer here:

- under `--wrap keep` there are no wrap points, so there is nothing to do (§5.2);
- a section holding a tilde fence or a whitespace-only segment is declined on
  purpose (§4.7);
- the failure policy returns the input deliberately, and "unchanged" there is
  not a degraded mode but priority 4 of our own cascade (§4.9);
- a paragraph whose every gap classifies `NONE` has no legal break to make.

In all four the plugin is working correctly *by* doing nothing.
A test that demanded change would fail on all of them, and the pressure to make
it pass would push directly against §4.7 and §4.9 — the two rules that exist to
stop us corrupting documents.

So the control has to be specific rather than general:
a fixed input, at a fixed width, asserting one particular expected break.
That distinguishes *inert* from *correctly declining*, which is the real
question. Two ways to be inert are silent misconfiguration a user could hit
without noticing — `--wrap keep`, and not being named in `--extensions`, which
is a whitelist (§1.1) — so the distinction is worth a test rather than a
comment.

Write that assertion before relying on the invariants: until it exists,
a green suite does not tell a working plugin from a disabled one.

**Two uses of pinning (§4.8) that are unexplored, not rejected.**

Pinning is currently used only for correctness. It is also, in principle,
a user-facing *never break here*, and a way to take spec rule 13's
permission to overflow deliberately — keeping a short unit intact rather
than letting priority 4 split it. Neither is designed.

**Where to read next.**

- rumdl `tests/formats/md013_reflow_*.rs` and `tests/regressions/md013_*.rs` —
  integration cases including MkDocs, Quarto, nested lists and definition lists.
- rumdl's proptest oracles: join-the-lines-with-a-space reproduces the source,
  and every code span / link destination / link title payload is unchanged.
  Both are directly portable and stronger than what §9.3 asserts today.
- The obsidian-sembr issue tracker,
  for corner cases reported by writers rather than implementers.

______________________________________________________________________

## 13. Provenance

Claims about mdformat internals were read from the installed 1.0.0 source
and exercised in test runs; every quoted snippet is from that source.

rumdl claims come from its 0.2.60 sdist and clone **and** from running its
manylinux wheel on the same inputs.
Where source reading and execution disagreed, execution won.

Coverage is much wider than the second pass and still not complete.
`text_reflow.rs` (6,430) and `sentence_utils.rs` (583) have now been read
in full; `md013_line_length.rs` (3,736), `md013_config.rs` (591),
`block_builder.rs` (1,001), `helpers.rs` (1,384), `docs/md013.md`,
the MD013 test suite (9,750) and the `tests/formats` and `tests/regressions`
reflow files have been mined for hazards rather than read line by line.
That mining was done by three subagents working from the notes files in the
scratchpad, not by me directly, so treat the *citations* as second-hand
unless they appear in this document attached to a measurement.

Everything in this document that changed behaviour was reproduced here before
being written down, and three of the agents' findings did not survive that:
one was already handled, one was a property of a stand-in implementation
rather than of this design, and one — §4.5's `MIN_SPLIT_RATIO` claim —
went the other way and showed **this document** was wrong, not the code.

pysembr has now been read in full, including its git history,
from the unshallowed clone at `753e0e6`.

mdformat's own repository was read at master, which is byte-identical to the
installed 1.0.0 across `src/mdformat`; its issue tracker, changelog and test
data were searched for each of the three upstream bugs in §12.

`mdformat-sembr` 0.2.0 was read in full and its own test suite executed.
The sembr specification repository, obsidian-sembr, `admk/sembr` and semlf
were surveyed for rules, user-reported corner cases and evaluation method.

A caution about that survey. Its agent-reported F1 and severed-clause figures
were never reproduced and are **not** the numbers in §9.6. What transferred was
the *method* — that a hand-written sembr document is a labelled corpus. §9.6's
table was produced here, by the harness kept at `notes/quality-harness.py`,
over corpora named in that section. §9's figures were all executed by me, against a
baseline naming `extensions=set()` explicitly — after one run was invalidated
by a competitor plugin installed into the environment mid-session.

The specification's rules were read from the cloned repository.
An earlier pass took them from a `WebFetch` summary of sembr.org,
which silently dropped rule 1 and shifted every number after it —
so this document said "twelve rules" and mis-cited every one.
Corrected here. The lesson is narrow and worth keeping:
a summary of a normative document is not the normative document,
and the repo was already on disk.

rumdl issues #388, #728, #770 and PR #601 were read on github.com.
The issue tracker is reachable by ordinary web fetch;
an earlier claim in this project that it required elevated GitHub access
was simply wrong.
The remaining ~50 issue numbers referenced by rumdl's test names
have not been read, only inferred from the tests that cite them.

The prototype was ~580 lines with no dependencies beyond mdformat.
It implemented §4 in full, including every fix listed in the first pass's §7,
and every number in §9 came out of running it.
It is not retained, and it is **not in git either** (see the note under the
title): the committed version at `7b42d70^` is 466 lines and predates
`strict_clauses`, so it cannot produce §9.6's default column or §9.1's
`strict_clauses` rows. §4 is written to be reimplemented from, not to describe
existing code.

**This pass.** Executed, not reasoned about: the three replacement masks in
§4.2, against ten cases including the three that defeated the old patterns —
all ten behave as stated, and the old patterns fail exactly as described;
§9.6's weighting scheme, recomputed from the published per-corpus cells, which
reproduces four of five aggregate figures exactly and gives 0.10 where the
table said 0.13; and the package, built with `flit_core`, installed into a
clean venv, entry point resolving as `semantic_line_breaks`, 35 tests passing
with the positive control xfailing, and the CLI option group registering clean
under `-W error::DeprecationWarning`. Licences were read from PyPI metadata for
mdformat and all nineteen plugins in its curated list; all are MIT.

**Harness restoration.** All four deleted harnesses were recovered from
`git show 7b42d70^:tests/` and executed. The five pinned corpora fetch and were
measured. §9.2's matrix runs 60/60 on both invariants; §9.3 passes at four
widths with escape normalisation added; §9.5's 4,000 paragraphs over 74 atoms
at eight widths and §9.4's 1,500 fixtures over 16 at-risk characters both
report zero regressions against the baseline; §9.1's differential runs against
a pinned `rumdl==0.2.60` and scores **7/15**. Two corroborations worth
recording: 7/15 is exactly the first pass's score, and the eight diverging
cases are the eight §9.1 says the design had to change — so the recovered case
set is faithful. And the re-measured word-wrap column moved exactly as
predicted from the badge and `<pre>` contamination, on both corpora that
carried badges and neither of the two that did not.

Not checked, and worth knowing before relying on any of it.
The five zero-target rows above pass **trivially**, because an identity
function deletes nothing and changes no render; they are correct tests, not
evidence. §9.6's plugin columns are still the second pass's unreproducible
figures — only the word-wrap column was re-measured, since a baseline needs no
plugin. §9.5's atom set and §9.4's sixteen characters are reconstructions from
prose, not the originals. §4.5's
`merge_floor = min(min_line_chars, limit)` is a **decision, not a
measurement** — it was chosen to leave width 80 and `--wrap no` exactly as
§9.6 scored them while removing the degenerate case, and nobody has run it.
The restructuring of §4.3 and §4.5 is textual: no implementation has been
measured in the new shape. The 0.07 → 0.17 partial-crash figure in §9.6 is
carried over from the harness review and was not re-run here. §9.4's sixteen
at-risk characters and §9.5's twenty-four extra atoms are still unenumerated,
which is why §14.4 now asks those rows for zero rather than for a
reproduction.

______________________________________________________________________

## 14. Picking this up

Written at the end of the session that produced §§1–13, to record decisions
that were made in conversation and exist nowhere else. Everything above is
about the design; this section is about how to continue.

### 14.1 Rewrite, do not refactor

The implementation this document was measured against is **not in the
repository**, and — contrary to what earlier drafts of this document said
three times over — it is **not recoverable from `git log`** either (see the
note under the title). It was a proof of concept, deleted on purpose.

It should not be revived. It is a rumdl port: `MIN_SPLIT_RATIO`, `_cascade`,
`_latest_fitting`, `_is_standalone_parenthetical`, `_merge_short` — five
identifiers from rumdl's vocabulary and, at the last count, zero named for any
of the thirteen rules this design claims to implement. Renaming them would be
worse than either honest option: rumdl's control flow wearing spec labels,
looking conformant while remaining a port.

The behaviour is fully specified in §4 and fully measured in §9, so a fresh
implementation loses nothing. **The tests are the asset; the code is not.**

### 14.2 §4 needs restructuring before it is built from

**Done — §4.3 and §4.5 now carry this shape, and the rest of this subsection
records why.** §4 used to describe a four-rung cascade because rumdl has one.
That shape is demonstrably wrong for this design, and §4 is now organised
around the spec's own rules:

> rule 4 (always) → rule 5 (always) → rule 6 (width-driven) → rules 12/13
> (mdformat's own wrap)

The spec states this itself, and more cleanly than §9.6's F1 numbers do:
**rules 6 and 8 carry "or satisfy line length constraints"; rules 4 and 5 do
not.** That textual asymmetry *is* the architecture. Rules 4 and 5 are
unconditional; only rule 6 and the length rules are width-driven.

### 14.3 What is not rumdl inheritance, and must survive

Three things came from this seam, not from any prior implementation, and have
no analogue in rumdl. They are load-bearing:

- **Pinning** (§4.8) — a wrap point may become a *space*, not only a newline,
  and a space is unbreakable by mdformat's own wrap. This is what makes the
  §4.7 correctness rules enforceable rather than advisory.
- **The correctness rules** (§4.7) — edge safety, and the tilde section
  decline. Both prevent data loss or a changed render; neither is aesthetic.
- **Masking and depth counting** (§4.2) — including the discriminator that a
  complete bracket group inside one segment is link syntax while one arriving
  in pieces is prose.

§3's argument stands untouched.

### 14.4 Acceptance gate

Earlier drafts said a rewrite is proven equivalent when it holds *every*
figure in §9. That cannot be asked for, because the code those figures were
measured against exists in no commit (see the note under the title). What
survives that fact, and what does not, differs row by row — so the gate is
split.

**Binding.** These are invariants or exact matches, so they do not depend on
recovering the prototype: a target of zero is still zero against a corpus you
build yourself, and §9.1's fifteen cases plus a pinned `rumdl==0.2.60` are
fully in the repository.

All seven now run. The atom and fixture sets behind the first three are
**ours**, rebuilt from §9.5's and §3.2's prose, because the originals were
never recorded — which is exactly why those rows ask for zero rather than for
a specific number to be reproduced.

| Check | Required | Status today | Harness |
| --- | --- | --- | --- |
| render regressions vs baseline (§9.5) | 0 / 4000 | 0 | `tests/test_fuzz.py` |
| idempotency regressions vs baseline (§9.5) | ≤ 1 / 4000 | 0 | same — **8/4000 is the figure without §4.8's pinning**, and the second pass left this row out of the gate entirely |
| whitespace deletions vs baseline (§9.4) | 0 / 1500 | 0 | same |
| invariant matrix (§9.2) | 60 / 60 | 60 / 60 | `tests/test_invariants.py` |
| structural property (§9.3) | pass | pass | `tests/test_structural_property.py` |
| rumdl agreement, `strict_clauses` off (§9.1) | 15 / 15 | **7 / 15** | `tests/test_differential_rumdl.py` |
| positive control (§12) | must fail when the plugin is absent | **fails, as it should** | `tests/test_fixtures.py` |

**Read that "status today" column carefully.** The plugin is inert, so the
five zero-target rows pass *trivially*: an identity function deletes nothing
and changes no render. They are not evidence of anything yet. The two rows
that carry information are the two that fail — and 7/15 is precisely the score
§9.1 records for the first pass, from a plugin that does nothing at all. The
eight cases that diverge are the eight §9.1 says the design had to change.

Both failing rows are `xfail(strict=True)`, so the suite is green now and goes
**red the moment either starts passing**, forcing the marker off deliberately
rather than letting a gate quietly go green.

**Not binding — prior observation only.** §9.6's `0.650` is not a gate and
must not be treated as one. Three independent reasons, any one sufficient: the
code that produced it is unrecoverable; the corpora were never pinned to a
commit and have already moved; and the harness that computed it has the
extractor and fail-open defects §9.6 now documents, one of which (a partial
crash *raising* F1 from 0.07 to 0.17) biases the number upward.

So the F1 figures in §9.6 are a **direction, not a target**: a rewrite should
land in the same region and beat plain word wrap by a wide margin, and anything
near 0.10 means the plugin is not running. Re-baseline properly — fix the
harness per §9.6, pin the four corpora by commit SHA, re-measure — and replace
§9.6's table with figures that can be reproduced. Then, and only then, is an
F1 row worth putting in this gate.

**This costs less than it sounds.** The one thing §9.6 was doing that nothing
else does — justifying `strict_clauses = true` as the default — does not
actually need it. Spec rule 5 says a break SHOULD occur after an independent
clause and, unlike rules 6 and 8, attaches no length condition (§14.2). The
literal reading *is* the conformant reading; §6 already argues it from the
spec's own text, and the eight-of-eight measurement was corroboration, not the
basis. Keep the default; re-confirm the number later.

Three traps that have each cost a measurement in this project:
every baseline must name `extensions=set()` explicitly, because `--extensions`
is a whitelist (§1.1); `--check` never validates (§2.2); and the quality
harness fails open, so an F1 figure is only admissible from a run that
reported zero exception discards (§9.6).

### 14.5 Order

1. ~~Restructure §4 per §14.2.~~ **Done.** It mattered: writing code first
   produces a §4 that describes the code, which is how the old shape arose.
1. ~~Land packaging.~~ **Done.** The entry point exists and the inline
   postprocessor is an identity function, so every harness can run and reports
   the plain-word-wrap baseline.
1. ~~Restore the four harnesses.~~ **Done**, with the corrections §14.4's
   table names, the corpora pinned by SHA, and the quality harness rewritten
   around markdown-it. The positive control exists and fails, which is the
   only reason the other rows can be trusted later.
1. Implement from the restructured §4. Hold §14.3 fixed.
1. **Then** rule 10 — a break before a hyperlink, which is around 9% of two
   authors' breaks in §9.6's own corpora and nearly free here, since `link()`
   already makes a whole link one segment. Land it *after* parity, as its own
   measured change: it is a new break strategy and will move F1, so folding it
   into the rewrite makes both unattributable.
1. Widen the positive control. `tests/test_fixtures.py` carries a minimal one
   as `xfail(strict=True)`, so the suite goes red the moment breaks start
   appearing and the marker has to come off deliberately; that covers "is the
   plugin running at all" and nothing more.

### 14.6 Two places §4 used to mislead you

Both are now fixed in §4 itself, and are recorded here because anyone working
from an older copy of this document will hit them:

- **The clause rung of the cascade never executes under the default.** Step 1
  consumes every clause gap; instrumenting two corpora gives 44 parenthetical
  and 202 break-word candidates and **zero** clause. §4.5's pseudocode used to
  read as though all three rungs were live. It now cuts CLAUSE in step 1 under
  `strict_clauses` and guards the step 2 rung with `if not strict_clauses`.
- **`MIN_SPLIT_RATIO` was two thresholds sharing one name.** They are now
  `min_first` (the step 2 candidate filter) and `merge_floor` (the step 3 stub
  floor), and §4.5 gives both formulas. The old reading of the second — a
  `max()` against `min_line_chars` — was not merely ambiguous but degenerate,
  emptying the candidate window at every width below 25.
