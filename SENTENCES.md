# mdformat-sentences

A design for a second, much smaller plugin.

This document is written one sentence per line, which is the output this plugin produces.
It is the dogfood, and it is also the argument: read it at any window width and the line breaks do not move.

`mdformat-semantic-line-breaks` implements the full [Semantic Line Breaks](https://sembr.org) cascade, and its `DESIGN.md` specifies it.
This specifies a different plugin with a smaller promise.
This document stands alone.
Where the two designs agree it restates the shared material rather than depending on `DESIGN.md`, citing that document only to say where a fact was verified; where they differ, it says so explicitly.

______________________________________________________________________

## 1. What this is, and what it is not

**The whole promise, in one sentence:** a line break after every sentence, nowhere else, ever, at any width.

**The output does not depend on `--wrap`.**
Line positions are a pure function of the text.
Adding a word to the second sentence of a paragraph changes exactly the line that word is on, and no other line, at any width, forever.
That is the diff-stability property Semantic Line Breaks exists for, and the full cascade cannot offer it — as soon as a break position is chosen by "the rightmost candidate that still fits in 80 columns", an edit upstream can change which candidate wins and cascade down the paragraph.

**Absent by construction, not defaulted off.**
This is the canonical list, and every later section that declines something cites it rather than re-arguing the case.

- **Width, column and line-length.**
  Not a default, not an option, not a tie-breaker.
  A 400-character sentence occupies a 400-character line.
- **Word lists and clause machinery.**
  No conjunctions, no clause punctuation, no break words, no parenthetical strategy, no merge pass, no minimum line length, no `MIN_SPLIT_RATIO`.
- **Spec rules 5 and 12.**
  Rule 12 is a line-length recommendation and there is no length here; rule 5 cannot be done without a parser, and §5.1 makes that case.
  This is a strict subset of correct Semantic Line Breaks, not a competing interpretation of them.

The whole configuration surface is two options, both about sentence *detection* (§4).

### 1.1 Why not a mode of the other plugin

It could be one, and `DESIGN.md`'s cascade reduces to this when its width-driven rules are disabled.
Three things make a separate plugin the better shape, and the longer version of the argument belongs in the README rather than here.

The promise is explainable in one sentence and verifiable by reading the output, where "break at sentences, then clauses, then parentheticals, then break words, then let the wrapper finish, then merge the stubs back" is neither.
The failure modes that have dominated `DESIGN.md`'s tuning — coordinating `and` splitting noun phrases, rule 5 shattering serial lists, a length floor standing in for a grammatical test — all live in rules 5 and 6, which do not exist here.
`--wrap` independence (§6.1) is an invariant this plugin can assert and the cascade cannot, and it is cheap, total, and catches almost any implementation error.

______________________________________________________________________

## 2. Name, packaging and the seam

Distribution `mdformat-sentences`, module `mdformat_sentences`, entry-point id `sentences`.
Both `mdformat-sentence` and `mdformat-sentences` were unregistered on PyPI as of 2026-09-12, verified against the JSON API.

```toml
[project.entry-points."mdformat.parser_extension"]
sentences = "mdformat_sentences"
```

Dependencies: mdformat only, `>=1.0,<2`.
`requires-python >= 3.10`, because mdformat 1.0.0 declares it.
Licence MIT, matching mdformat and every plugin in its curated list.

§2.1 to §2.4 are inherited from the `mdformat-semantic-line-breaks` design work, where every fact below was verified by execution against mdformat 1.0.0.
None of it is re-verified here.
It is restated rather than cited so that this specification stands alone, and the one place the parent's reasoning does *not* carry over is called out in §2.2.

### 2.1 The entry point id, and why it is the binding constraint

The id is what `--extensions` accepts, what keys `[plugin.sentences]` in `.mdformat.toml`, and what `mdformat.text(..., extensions={"sentences"})` names.
It follows the ecosystem convention of the distribution name with underscores, as `mdformat-simple-breaks` registers `simple_breaks` and `mdformat-frontmatter` registers `frontmatter`.

**An id collision is silent.**
mdformat loads plugins with `loaded_ifaces[ep.name] = ep.load()`, a plain dict assignment in `mdformat/plugins.py`, so two distributions registering the same id overwrite each other with no warning and no error.
The id, not the PyPI name, is the identifier that has to be unique.
`sentences` collides with neither `mdformat-sembr`'s `sembr` nor `mdformat-semantic-line-breaks`'s `semantic_line_breaks`, and all three can be installed together.

**`--extensions` is a whitelist, not an addition.**
`enabled_parserplugins` is *all* installed plugins when `--extensions` is absent, and *only* the named ones when it is present.
So `--extensions sentences` silently disables GFM.
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
- The empirical support for the choice is that `mdformat-sembr` hooks `paragraph` instead, and both of its observable defects follow from that.

**One line of the parent's reasoning does not carry over.**
`DESIGN.md` also counts on mdformat word-wrapping whatever `WRAP_POINT`s the plugin leaves behind, which is the bottom rung of its cascade and free.
Nothing is left behind here (§3.4), so that rung does not exist and no part of this design may assume it.

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

So `dest="require_sentence_capital"` lands at `options["mdformat"]["plugin"]["sentences"]["require_sentence_capital"]`, and the visible flag text is whatever string the plugin passes to `add_argument`.
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

`--wrap keep` stays silent rather than warning.
`keep` is mdformat's default, and mdformat's own documentation gives hand-written Semantic Line Breaks as the reason it is the default, so a user who installs this plugin and keeps `wrap = "keep"` is asking mdformat to preserve the breaks they wrote themselves.
Warning on the tool's default configuration would fire constantly for people doing nothing wrong.
A warning would be justified if the plugin were *explicitly* named in `--extensions` alongside `--wrap keep`, since that is closer to a contradiction, but that is not worth the plumbing until someone trips over it.

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
mdformat has already collapsed each link, image and code span into a single segment with literal interior spaces, so punctuation cannot detach from its token — `Lorem (ipsum sit). Dolor amet.` segments as `['Lorem', '(ipsum', 'sit).', 'Dolor', 'amet.']` and `sit).` is one atom (`DESIGN.md` §3.1, verified there by execution).

**Every gap that is not a sentence break becomes a literal space, never a wrap point.**
This is `DESIGN.md` §4.8's *pinning* primitive applied unconditionally rather than selectively.
A literal space is carried through `textwrap` as a preserved character and restored verbatim, so a pinned gap is unbreakable by mdformat's own word wrap as well as by us.
That single decision is what makes the output width-independent, and it is why this plugin emits no `\x00` at all.

**`is_sentence_break` sees the whole segment list.**
It cannot be a function of two adjacent segments, for the reasons in §3.3: bracket depth accumulates from the start of the section, the French closer rule looks one segment back, and the opener rule defers forward.
`scan` computes those once per section.

### 3.2 Masking

Within a segment, blank out the spans below, preserving length so offsets stay valid.
The patterns are `DESIGN.md` §4.2's, corrected and verified there against ten cases:

```
code span            (?<!\\)(?<!`)(`+)(?!`)(?:[^`]|`(?!\1(?!`)))*?(?<!`)\1(?!`)
link/image dest      \]\((?:[^()\\\s]|\\.|\((?:[^()\\]|\\.)*\))*(?:\s+"[^"]*")?\)
reference label      \]\[[^\]]*\]
autolink / raw HTML  (?<!\\)<(?:[/!?]?[A-Za-z][^<>]*
                     |[A-Za-z][A-Za-z0-9+.\-]*:[^<>\s]*|[^<>\s@]+@[^<>\s]+)>
```

Masking has exactly one consumer here: bracket-depth counting (§3.3), where an unmasked `)` inside a URL drives depth negative and corrupts every later gap in the section.
It does not feed sentence detection, because §3.3's closer set already excludes backtick, `)` and `]`, so a terminator inside a code span or a link destination fails the terminator test unmasked.
In the parent design masking fed clause detection too, which is why it is specified there as a length-preserving rewrite; whether the length requirement survives that reduction is open (§7).

### 3.3 Sentence detection

This is the entire substance of the plugin.
Everything below is inherited from `DESIGN.md` §4.3, restated in full because it is normative here and because a reader of this document should not have to hold two specifications open.

**A sentence end is a terminator followed by zero or more closers, at segment end.**

```
terminators  . ! ? … 。 ！ ？
closers      " ' ’ ” » › “ ‘      plus  * _ ~
openers      " ' “ ‘ « ‹ ¿ ¡ „ ‚  plus  * _ ~ [ ( \
```

`“` and `‘` are in both sets deliberately: they open in English and close in German.
That is not a conflict, because a closer is tested after a terminator and an opener before a capital, and no position tests for both.

The closer set **excludes** `)`, `]`, `}` and backtick.
This is the root fix for a family of bugs rather than a patch for any one of them, and it is what rumdl does.
Three consequences, all verified in `DESIGN.md` §4.3:
`` Install the `foo.` Then run… `` does not break after the code span;
`See the [docs](https://ex.com/a.b.) The next…` does not break after the link;
`An array like (1, 2, 3.) Then…` does not break after the parenthetical.
The cost is that a sentence genuinely ending inside parentheses — `He left. (He came back.) Then…` — is not detected, which is rumdl's blind spot too, and is accepted.

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
The CJK terminators skip both checks: CJK has no case, so `require_sentence_capital` has nothing to test, and no CJK abbreviation ends in `。`.
Their wrap point exists only where the author separated the sentences with a space, which is the only case that can be acted on.
A bare `!` or `?` is unambiguous, but one immediately followed by a closing quote is not, because the question may belong to the quoted phrase rather than to the sentence carrying it.
Without that qualifier, `A "Is this a test?" guide to the whole subject…` breaks after `test?"`, stranding a 19-character fragment mid-sentence.

**The three checks:**

- **Abbreviations.**
  The English default set is `mr mrs ms dr prof sr jr st i.e e.g vs fig no vol ch sec al`.
  `etc`, `inc`, `ltd` and `cf` are deliberately **absent**: they commonly end sentences, and with `etc` present `Use commas, semicolons, etc. The next sentence…` loses a real boundary.
  German abbreviations are in the default set too, and `usw` is excluded from them for exactly the same reason as `etc`.
  **The German set is not enumerated anywhere upstream**: `DESIGN.md` §4.3 names only `bzw.` and `Abb.` as examples and records that five of six ordinary German sentences broke spuriously without the set, but never lists it.
  That is a gap inherited from the parent document, not a decision, and it has to be closed before this specification can be implemented from.
  German is on by default rather than behind a language flag because the asymmetry runs one way — an abbreviation held back costs at most a missed break, one that is missing corrupts a sentence — and these tokens are vanishingly rare in English prose.
  German cannot borrow the capital rule to cover a missing abbreviation, because German capitalises every noun.
  User-supplied abbreviations are **added** to the defaults, never replace them.
  Two refinements to the match, both reachable in practice: strip leading punctuation from the candidate word so `(e.g.` and `[i.e.` match, and also test the last hyphen-separated component so `Wrangell-St.` matches via `st`.
- **Single capital initials** — `J. K. Rowling`.
- **`require_sentence_capital`** (default true): the next sentence must open with a character having no lowercase form — uppercase, a digit, or CJK.
  Digits matter: `1976 was hot.` is a sentence opening.
  Opening markup is skipped first, using the opener set above.

**A sentence never opens with a block-construct marker, and this applies to every terminator.**
If the next segment would start `#`, `>`, `-`/`*`/`+`, a bare `\d+[.)]`, or a setext or thematic run at line start, the gap is not a sentence boundary.

This rule is **unconditional and independent of `require_sentence_capital`**, and that matters more here than in the parent design.
It is the only thing preventing a break from putting a construct at a line start where mdformat would escape it, and because this plugin has no `avoid_escapes` option (§4.1), it is the only protection there is.
Writing the capital rule as *uppercase, digit or CJK* rather than as *not lowercase* happens to suppress the same cases, but a user who sets `require_sentence_capital = false` would otherwise re-arm all of them.

**Quotation marks are language-specific.**
Two structural rules follow, neither of them about any one language:

- A segment consisting only of closing punctuation is never a break candidate, and when the segment to the left is such a mark, the terminator test looks one segment further back.
  French spaces its closer off — `« Ceci est important. »` — which puts the closer in a segment of its own and breaks the naive rule twice, once by orphaning the mark onto the next line and once by failing to see the terminator.
- A segment consisting only of *opening* markup defers the capital test to the next segment rather than failing it.
  Returning "no opener found" is not the same as "no sentence opens here".

**No boundary inside brackets.**
Depth counts `[` as well as `(`, accumulated across the section over masked segments.
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

Two, both inherited, both non-negotiable.

**Edge safety.**
A gap is ineligible when the last character of the segment to its left, or the first character of the segment to its right, is whitespace that `str.strip()` would delete.
Test with `.strip()`, not with a character list.
mdformat's `paragraph()` strips each line after wrapping, so a break at such a gap silently deletes the character, and `is_md_equal` cannot see it because HTML comparison collapses whitespace.

This rule is much smaller here than in the parent design, and the reduction is a direct benefit of §3.4.
There, every gap was a potential wrap point and all of them needed the guard.
Here, only sentence gaps can break at all; every other gap is already pinned, which is the same mechanism the guard uses.
An ineligible sentence gap is simply pinned like its neighbours.

**Tilde sections are declined outright.**
A run of three or more tildes at a line start opens a fenced code block and changes the render.
This is an upstream mdformat defect, not ours — plain mdformat with no plugin and no extensions reproduces it — but our breaks reach it far more often, so the blast radius is ours.
A section containing `~{3,}` is returned unchanged, with every gap pinned.
Pinning alone is not sufficient, because a code span or list marker elsewhere in the same section can re-segment the text so the fence reaches a line start by another route.
A section containing a tilde fence is not one anybody is line-breaking for readability anyway.

### 3.6 Failure policy

Reconstruct the pre-layout section by mapping every emitted `\n` and every inserted `" "` back to a `\x00`, and require byte equality with the input.
On mismatch, return the text untouched.

rumdl takes the same posture, and its comment is worth keeping: the alternative is writing corrupted prose into the user's file.
"Untouched" is a coherent degraded mode here rather than a failure: the paragraph is simply left to mdformat, which under `--wrap no` puts it on one line and under `--wrap keep` leaves it alone.

______________________________________________________________________

## 4. Config surface

Two options, both about sentence detection, both in `[plugin.sentences]` and as CLI flags.

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `require_sentence_capital` | bool | `true` | `word. lowercase` is not a boundary |
| `abbreviations` | list | `[]` | **added** to the defaults, never replacing them |

CLI spelling is short, because mdformat namespaces only the argparse `dest` and leaves the flag text to the plugin (§2.4):

```
--sentences-no-require-sentence-capital
--sentences-abbreviations A,B,C
```

Every default must be `None`, for the reason in §2.4.

As with any mdformat plugin, these are CLI- and TOML-only: `mdformat.text()` does not populate `options["mdformat"]["plugin"]`, so a library caller gets the defaults.
An undocumented escape hatch exists and the test harnesses use it — `options={"plugin": {"sentences": {...}}}` reaches the seam via the splat at `_api.py:29` — but it is not a supported mdformat interface.

### 4.1 Options deliberately not provided

- **Any width, column or line-length option.** §1.
- **`avoid_escapes`.** Unnecessary: §3.3's block-construct rule is unconditional, so no break can land before `#`, `>`, `-` or an enumerator, and no escape is ever added.
- **A "honour `--wrap`" mode** that would let mdformat wrap inside a sentence. That is a coherent product — GNU Emacs's `fill-paragraph-semlf` is exactly it — but it reintroduces geometric line breaks and therefore forfeits §1's property, which is the only reason this plugin exists. Anyone who wants it wants the other plugin, or Emacs.
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

The reason is that rule 5 cannot be implemented from punctuation alone without over-firing, and the evidence is in this repository.
Under the parent design's unconditional reading, rule 5 breaks at every comma at paren depth zero with no test for whether an independent clause follows, which shatters serial lists (`LaTeX,` / `Markdown,` / `and plain text,`), coordinate prepositional phrases and introductory adverbials.
It is made tolerable only by a length-based merge pass that folds short lines back — a geometric patch for a grammatical problem, and one this plugin has no width to compute.

Implementing rule 5 correctly needs a test for whether both sides of a comma could stand alone as sentences, which is the parsing problem this project has ruled out by charter.
Declining the rule is the honest position for a tool that will not parse.
Anyone who wants rule 5 as currently implementable wants `mdformat-semantic-line-breaks`.

Rule 12 is declined for the reason in §1 and needs no further defence: it is a RECOMMENDED, and honouring it is incompatible with the property this plugin sells.

______________________________________________________________________

## 6. Verification

### 6.1 The width-independence invariant

This is the gate that does not exist for the other plugin, and it is the cheapest and strongest test here.

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
| rumdl `sentence-per-line` agreement (§6.3) | to be established, then held |
| positive control | must fail when the plugin is absent |

Every oracle is **relative**: plain mdformat at the same width, with `extensions=set()` named explicitly.
Absolute render equality is the wrong bar because mdformat itself already breaks the render on some inputs (§3.5's tilde fence), and holding ourselves to a standard mdformat does not meet means either failing forever or weakening the test until it says nothing.

The harnesses in this repository's `tests/` port across almost unchanged, and their traps apply here too.
`--extensions` is a whitelist, so every baseline must name `extensions=set()`;
`--check` never validates;
and the quality harness must fail loudly rather than reporting an F1 for a plugin that never ran.

### 6.3 rumdl is a direct differential oracle

This is a significant advantage over the parent design and it should be used from the first commit.

rumdl's MD013 has four reflow modes, and one of them is `sentence-per-line`.
Verified by execution against `rumdl==0.2.60`: in that mode, with `line-length = 80`, a 136-character sentence is left intact on one line.
Its reflow trigger contains no length test at all, unlike its `Default` and `SemanticLineBreaks` modes.
So rumdl's sentence mode makes the same promise this plugin does, including the width-independence part.

`DESIGN.md` §8 had to enumerate deliberate divergences from rumdl because the parent plugin reads rule 5 differently.
Here there is no such divergence to manage, and agreement is a target rather than a thing to explain.
Where the two differ, one of them has a bug, and the burden is on us to say which.

### 6.4 What to build first

1. The positive control, before anything else.
   Every other check in §6.2 passes with the plugin disabled — an identity function deletes nothing, changes no render, and is trivially width-independent — so until one test fails when the plugin is absent, a green suite does not distinguish a working plugin from an inert one.
1. §6.1, which is three lines and catches most of what can go wrong.
1. The sentence-detection fixtures, which are where the remaining complexity actually lives: abbreviations, initials, the capital rule, footnote references, CJK, French spaced closers, German quotes, the `?"` case, bracket depth.
1. The rumdl differential.

______________________________________________________________________

## 7. Provenance

What is new in this document versus inherited, stated honestly, because the parent repository holds claims to that standard.

Everything inherited from `DESIGN.md` is cited there at the point where it is used, and was verified there by execution against mdformat 1.0.0 rather than re-derived here.

**Verified by execution in the session that produced this document.**
Both `mdformat-sentence` and `mdformat-sentences` were unregistered on PyPI on 2026-09-12, checked against the JSON API.
A postprocessor emitting `\n` at sentence gaps and a literal space everywhere else leaves a 140-character sentence intact at `--wrap 80`, and produces byte-identical output at `--wrap no`.
The same postprocessor *without* pinning yields 78- and 61-character lines at `--wrap 80`.
`rumdl==0.2.60` in `sentence-per-line` mode leaves a 136-character sentence intact at `line-length = 80`, while its `semantic-line-breaks` mode breaks the same input at the clause comma.

**Asserted but not executed.** No implementation of this specification exists, so §6's gate has never been run.
Masking is specified as a length-preserving rewrite, inherited from the parent design where it also fed clause detection; if bracket depth is genuinely its only consumer here (§3.2), a per-segment integer would do and the length requirement is dead weight, but that has not been checked against `DESIGN.md` §4.2's other callers.
The German abbreviation set is referenced but cannot be carried over, because the parent document never enumerates it (§3.3); an earlier draft of this document invented one, which is exactly the failure `CLAUDE.md`'s provenance rule exists to catch.
The reduction of masking's role in §3.2 is an argument about which tests can fire, not a measurement of which do.

**Not checked.** Whether §3.3 reduces to a clean subset without the parent's clause machinery, or whether any of the sentence-detection rules interact badly in the absence of the clause rung.
That reduction is reasoned from the two specifications, not measured, and the parent design has always been measured with both rungs present.
Whether declining rule 5 changes the calculus on any §3.3 rule that exists partly to keep clause breaks honest.
