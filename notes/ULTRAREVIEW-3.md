# Ultrareview 3 of DESIGN.md, consolidated

A record of findings, not a specification.
`DESIGN.md` decides wherever the two differ.
Nothing here has been applied to `DESIGN.md` or to any other file.

**Subject:** `DESIGN.md` at `819e75b`, the head of `main` when the review ran.
Every link below is pinned to that commit, so line numbers keep pointing at the text that was reviewed.
**Method:** four reviewers each took one line range of `DESIGN.md` and checked its claims by execution against [mdformat 1.0.0](https://github.com/hukkin/mdformat/tree/82912cdaea4fb830f751504486a7879c70526547), [mdformat-gfm 1.0.0](https://github.com/hukkin/mdformat-gfm/tree/1c2d3c68019d93ff30c69482b0b19098b41b0a17), [rumdl 0.2.60](https://github.com/rvben/rumdl/tree/50dbfef7cf08f1d28633b684c0884490a63094e3) and [mdformat-sembr 0.2.0](https://github.com/bugrasan/mdformat-sembr/tree/795e9f4580599ff4a5d27a597061a8ee090598e6).
Each report was then vetted by two other agents, and every reviewer could retract their own findings.
The reviewer of the last range was lost in a container restart, so a fresh agent vetted in their place.
The consolidation was not re-run by hand.
**Ranges:** A is [L400-800](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L400-L800), B is [L776-1260](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L776-L1260), C is [L1259-1486](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1259-L1486), D is [L1-400](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1-L400).
Links to a heading open the rendered section.
Links to a line use `?plain=1`, because GitHub ignores line anchors in the rendered view.
**Ids:** R is a correctness finding, C is clarity or conciseness, X is a finding retracted or refuted in vetting.
Comment against the id.
"Proposed fix" is what the reviewers suggested, not a decision.
Source lines in mdformat's own code are named in backticks and not linked, because this repository does not contain them.

## 1. Correctness

### R1. DESIGN.md does not follow its own claim ([L5-7](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L5-L7))

[L5](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L5) says the document is written one sentence per line, "which is the output this plugin produces".
By its own [§3.2](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#32-inline-atoms) and [§3.3](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#33-sentence-detection) the plugin would join about 28 of its breaks:

- Seven lines open with `§`, which fails the capital test of [§3.3](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#33-sentence-detection) ([L576](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L576)): [L155](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L155), [L162](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L162), [L210](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L210), [L251](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L251), [L617](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L617), [L727](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L727), [L1339](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1339).
- Six lines end inside a code span with no terminator outside it ([L340](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L340) is the rule): [L389](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L389), [L390](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L390), [L394](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L394), [L434](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L434), [L555](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L555), [L754](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L754).
- The bold lead-in at [L402](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L402) has no period.
- The list items at [L1431](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1431), [L1432](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1432) and [L1433](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1433) end in `;`, which is not a terminator.
- About eleven lines open with a lowercase product name (`mdformat`, `rumdl`), the lowercase-opener limitation of [§3.3](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#33-sentence-detection).

The count of 28 is a rough simulation by the replacement vetter.
The `§` and code-span lines were confirmed by all three vetters.
The `§` case also shows the symbol-opener cost is not rare in technical prose.

**Proposed fix:** soften [L5-7](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L5-L7) to "hand-kept in this style", or edit the lines, and add `DESIGN.md` as a fixture in [§6](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#6-verification) ([§6.1](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#61-the-width-independence-invariant)).

### R2. [§5.2](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#52-what-punctuation-cannot-see-measured) counts the wrong text ([L1317-1365](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1317-L1365))

[experiments/rules.py](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/experiments/rules.py) is a line-based extractor.
It drops list items and the blockquote, keeps four lines inside `<pre>` demonstrations, and keeps nine rule-list continuations.
So [L1322](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1322) ("every line break in the specification's own prose") and the total of 88 at [L1362](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1362) are inaccurate.

Re-counting [corpus/sembr.md](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/corpus/sembr.md) with markdown-it:

| scope | breaks | rule 4 | rule 5 | rules 10/11 | other |
| --- | --- | --- | --- | --- | --- |
| top-level paragraphs, `table` enabled (recommended) | 75 | 9 (12%) | 31 (41%) | 8 (11%) | 27 (36%) |
| all paragraphs, lists and blockquote | 103 | 10 (10%) | 42 (41%) | 8 (8%) | 43 (42%) |
| as published | 88 | 11 (12%) | 37 (42%) | 8 (9%) | 32 (36%) |

The `commonmark` preset has no table rule and parses the pipe table at [corpus/sembr.md:L247-253](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/corpus/sembr.md?plain=1#L247-L253) as a paragraph, which is why a first recount gave 82 and 110.

Downstream figures under the paragraph scope: the unpunctuated share is 35 of 75 (47%, now 45%); the 36-word list recovers 10 of 27 (now 12 of 32); the residual 23% is unchanged; the 14-word list recovers 2 of 27; "10 of 122 lines" becomes 10 of 102.
"More than a third unreachable" survives both scopes.

Places to update: [L1322](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1322), [L1327-1329](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1327-L1329), [L1335](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1335), [L1338](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1338), [L1341](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1341), [L1343](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1343), [L1358](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1358), [L1362](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1362), [README.md:L43](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/README.md?plain=1#L43), [PRESERVE-MODE.md:L75](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/PRESERVE-MODE.md?plain=1#L75), [PRESERVE-MODE.md:L90](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/PRESERVE-MODE.md?plain=1#L90), [PRESERVE-MODE.md:L92](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/PRESERVE-MODE.md?plain=1#L92), [PRESERVE-MODE.md:L100](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/PRESERVE-MODE.md?plain=1#L100), [PRESERVE-MODE.md:L105](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/PRESERVE-MODE.md?plain=1#L105), [PRESERVE-MODE.md:L303 (14. Wrong turns, kept)](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/PRESERVE-MODE.md#14-wrong-turns-kept), and the docstrings at [experiments/rules.py](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/experiments/rules.py) and [experiments/breaks.py:L4](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/experiments/breaks.py#L4) and [experiments/breaks.py:L11](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/experiments/breaks.py#L11).

Also in [§5.2](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#52-what-punctuation-cannot-see-measured):

- Example 1 (`conventions` / `for using…`, [L1344-1350](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1344-L1350)) is recovered by `for`, which is in the 36-word list ([experiments/breaks.py:L18](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/experiments/breaks.py#L18)), so "none of which any word rule can see" is false.
  The corpus has better examples: `The following light markup languages` / `are verified…`, and `writers, editors, and other collaborators` / `can make…`.
- None of the three examples is a dependent clause, so the "6" row is a residual mix and might be relabeled "none of the above".
- "Three things follow" ([L1333](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1333)) is followed by four bold paragraphs, and "the larger of the two costs" never names the two.
- The shares 12, 42, 9, 36 sum to 99, because 11 of 88 is 12.5% and rounds down.
- The 36% row measures rule 6 under-firing, not rule 5 over-firing, so [L1353](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1353) does not support [§5.1](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#51-declining-rule-5-honestly)'s claim ([L1309](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1309)) that rule 5 needs a parser.
  A rough count by one reviewer found about 41 clause marks at breaks and 22 mid-line, another 31 and 19; neither method is recorded.

Vetting: upheld with correction by all three vetters; the scope question was settled by the replacement vetter.

### R3. The locality promise is overstated ([L22-23](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L22-L23))

[L22](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L22) says a word added inside a sentence changes exactly one line "at any width, forever".
Two things contradict it.
An unmatched bracket pairs with a closer in a later sentence ([§3.2](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#32-inline-atoms), [L337](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L337)) and holds back every gap between, so one stray `(` can merge several lines.
Example: `One ( fine day. A b. C d. E 1) f. G h.` merges three gaps.
A word that ends in a terminator can also split a line, which [L23](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L23) does concede.
The `et` / `al.` case ([L1415](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1415)) only splits its own sentence's line, so it is a missing caveat and not a contradiction.

**Proposed fix:** list the exceptions in [L22-23](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L22-L23) and drop "forever".
Do not say the effects are "local to the adjacent gaps", which is false for brackets.

Vetting: upheld with correction by all three vetters.

### R4. The `st` discriminator ([L694-703](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L694-L703))

The rule is `before_full='$upper$letter*'`, `at='(?i:st)'`, `break='allow'`.
It matches any capitalized unpunctuated word before `St.`, so `In St. Louis` and `The St. Louis Cardinals won.` lose the veto and break after `St.`.
[L703](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L703) lists only lowercase or numeric left neighbours as the wrong cases, which hides this class.

**Proposed fix:** add a sentence-initial example to the wrong cases.
Two vetters rejected the first reviewer's alternative, `after='The|Then|He|…'`: it is a break-word list ([L33](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L33) forbids those) and it would not cover `Elm St. Later he moved.` ([L703](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L703)).

### R5. Hard break, "glued" ([L105](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L105))

"Glued to the preceding segment with no wrap point between them" holds for the two-space form only.
`foo. \` followed by a newline and `Bar baz.` renders as `foo.\x00\\\nBar\x00baz.`, so the section ends in a lone `\` segment.
It is safe only because a section-final run of lone marks never breaks ([L472](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L472), [L763-765](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L763-L765)), so those lines must stay.

**Proposed fix:** "glued when no space precedes the backslash".

### R6. Pattern anchors ([L536-538](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L536-L538))

A leading `^` or trailing `$` is a no-op under `fullmatch`: `^5` and `5$` both match `5`.
So "silent narrowing" is wrong, and `^$numeric` demanding "exactly one digit" is only because `$numeric` is one character wide.
An interior anchor does narrow: `(?:.*-)?^st` rejects `Wrangell-st`.

**Proposed fix:** reject anchors at load (the vetters prefer this to accepting them), keep `[^…]` from being read as an anchor, and say how a literal `$` is spelled against the macro sigil.

Vetting: upheld with correction by all three vetters.

### R7. `at` strips one terminator, `before` and `after` strip a run ([L453-465](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L453-L465), [L483](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L483))

The key table says all three are "stripped".
[L462](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L462) says the bare keys lose "any trailing run", and [L483](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L483) says `at` loses "its trailing terminator", singular.
The shipped ellipsis rule `(?:.*[^.])?\.\.` ([L1134-1138](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1134-L1138)) works only on the singular reading: `moment..` matches, and `moment...`, `moment.` and `moment....` do not.
Only a comment at [L1134](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1134) says the two strippers differ.

**Proposed fix:** one clause in the key table.
One vetter downgraded this, because [L483](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L483) does say it.

### R8. Line-start safety list ([L813-814](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L813-L814), [L1263](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1263))

`#`, `>`, `-`, `+`, `---` and `===` already fail the capital test, since they are neither letters, digits nor openers ([L575-576](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L575-L576)), so [L814](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L814) ("the only thing preventing…") and [L1263](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1263) overstate.
The reachable cases are `\d+[.)]`, runs of `*` `_` `~`, raw HTML, the task box and the definition syntaxes.
mdformat itself escapes only a marker followed by a space, tab or end of line ([`paragraph()`](https://github.com/hukkin/mdformat/blob/82912cdaea4fb830f751504486a7879c70526547/src/mdformat/renderer/_context.py#L421-L440)), so a prefix reading of "starts with `*`" would wrongly refuse `Done. **Note:**`; that reading is plausible and not confirmed.

**Proposed fix:** define the rule by mdformat's own escape predicates, say the others are defence in depth, and reword [L814](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L814) and [L1263](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1263).
Do not call the entries wrong.

### R9. Examples in an included file ([L1162-1167](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1162-L1167), [L1175](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1175))

An included file's examples run with the shipped base laid down, so a copy of the default dumped to `mine.toml` can add or override rules but not narrow them.
Removing `Dr` from the titles pattern and flipping its example to expect a break fails at load, because the base's `Dr` rule still matches.
[L1167](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1167) ("depend on nothing but the file") is loose wording, not a hard contradiction.

**Proposed fix:** document that a copy narrows with `allow`, and reword [L1167](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1167).
Do not run the examples under the composition's `base_rules`, which defeats the aim at [L1164](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1164).

### R10. Verification gate ([L1375](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1375), [L1399-1402](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1399-L1402), [L1454 (§6.4)](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#64-what-to-build-first), [L1474](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1474))

- [L1399](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1399) names gfm, mkdocs and footnote, but [L1468](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1468) and [L1469](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1469) load myst and wikilink and [L1401](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1401) installs dollarmath, while [L840](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L840) says the definition list is closed over "the co-plugins the gate loads".
- [L1375](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1375) sends the fuzz corpus to [§6.4](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#64-what-to-build-first), which has no fuzz item, and the quality harness at [L1434](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1434) has no row or build step.
- [L1402](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1402) says "now", which is stale; [§3.6](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#36-failure-policy) ([L848](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L848)) makes an unlocated container an atom, and the container-fallback row exists at [L1389](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1389).
- [L1454 (§6.4)](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#64-what-to-build-first) ("every other check in [§6.2](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#62-the-rest-of-the-gate) passes with the plugin disabled") is false for positive controls and minimality.
- [L1474](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1474) "Three of them come from Panache" has the wrong antecedent: it means the next table's rows.
- [L1415](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1415) says "both of which [§1](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#1-what-this-is-and-what-it-is-not) states", but [§1](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#1-what-this-is-and-what-it-is-not) ([L23](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L23)) states only the lowercase-opener case.

### R11. The numeral-share table ([L633-646](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L633-L646), [L707](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L707))

The text says "share of each token's ten commonest continuations that are numerals".
[experiments/ngram.py](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/experiments/ngram.py) computes a frequency-weighted share (`100*dig/tot`) and counts any `[IVXLCDM]{1,4}` string as a numeral.
That is why 97%, 92%, 13% and 12% appear; none is a multiple of ten.
[L707](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L707) ("100% means every one of the ten") holds for only some rows; `Vol` is 100% and its continuations are not years.

**Proposed fix:** "share of the frequency mass of the ten commonest continuations that is digits or an uppercase roman string of up to four letters".

### R12. Default index patterns ([L652-654](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L652-L654), [L680-688](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L680-L688))

- `whole` rejects `4.2`, `3a` and `2-1`, so `Fig. 2.1 shows…` and `Sec. 4.2` break in the default set while `no` takes `mixed`.
  `academic.toml` ([L1199](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1199)) exists for exactly this.
  **Proposed fix:** state the cost in [§3.3](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#33-sentence-detection).
  Two vetters rejected widening `whole`, because it removes the reason for the academic set.
- The `al` rule's `$numeric{4}` misses `1990a` and `2020b`, and the snippet is printed twice ([L680-688](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L680-L688), [L1183-1187](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1183-L1187)).
  **Proposed fix:** `$numeric{4}$lower?`, an example for it, and one copy of the snippet in [§4](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#4-config-surface).

### R13. `Sr` and `Jr` ([L543](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L543), [L629](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L629), [L1001](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1001))

[L629](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L629) describes the title class as "precede a capitalized name", which is wrong for the suffixes `Jr` and `Sr` (`Robert Downey Jr. He…`).
Neither token is in the n-gram table ([L646](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L646)).
The first reviewer proposed dropping them and withdrew that, and the vetters agreed, since [L666](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L666) prefers a long line to a wrong break, and rumdl also keeps `Jr.` joined (it is in rumdl's [built-in abbreviation list](https://github.com/rvben/rumdl/blob/50dbfef7cf08f1d28633b684c0884490a63094e3/src/utils/sentence_utils.rs#L23-L29)).

**Proposed fix:** correct the description and state the cost.

### R14. Smaller correctness items

- [L469](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L469) against [L474](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L474): a condition that requires a character does not match at a section start, but `before_full = ''` and `.*` do.
- [L749](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L749) and [L740](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L740): only the first mark after a terminator reads closing (`He said. " ' Yes.` gives close, then open), and "ends in a terminator" means "ends a sentence, closers skipped".
- [L359](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L359): `¿` and `¡` are in the openers ([L356](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L356)), so "everything before *plus* is a quotation mark" is false.
  A fix must keep them in the lone-mark class ([L722](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L722), [L739](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L739), the fixture at [L1456](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1456)).
- [L585](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L585): a bare gfm URL is a [`gfm_autolink` node](https://github.com/hukkin/mdformat-gfm/blob/1c2d3c68019d93ff30c69482b0b19098b41b0a17/src/mdformat_gfm/_mdformat_plugin.py#L136) that opens nothing, while `<url>` is a `link` with markup `autolink` that does.
  The cost is already recorded at [FUTURE-WORK.md:L64](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/FUTURE-WORK.md?plain=1#L64) and [MATH-AND-OPENERS.md:L77](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/MATH-AND-OPENERS.md?plain=1#L77).
- [L510](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L510): "candidate gap" is broader than the ATerm-only table ([L433](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L433)); it is first used at [L367](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L367) and [L374](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L374).
- [L1300](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1300): the MUST-level rules are 2, 4 and 9, and the plugin meets all three, rule 9 vacuously.
- The [§5](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#5-conformance-to-the-specification) table: rule 7 omits "or itemized" ([corpus/sembr.md:L103](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/corpus/sembr.md?plain=1#L103)), rule 8 "n/a" is doubtful, and rule 12 is "not implemented" at [L1297](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1297) but "declined" at [L1315](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1315).
- [L1262-1267](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1262-L1267): `avoid_escapes`, `break_words`, `strict_clauses`, `merge_short_lines` and `min_line_chars` are never attributed and are not mdformat-sembr 0.2.0 options; [L1312](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1312) cites a "charter" that nothing defines (replaced on this branch in `a6acf9d`, after the review ran); [L1263](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1263) "no escape… is ever added" needs a hedge against [L840](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L840).
- [L650](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L650): add a citation for rumdl.
  The claim is true: rumdl 0.2.60 ([list](https://github.com/rvben/rumdl/blob/50dbfef7cf08f1d28633b684c0884490a63094e3/src/utils/sentence_utils.rs#L23-L29)) and mdformat-sembr 0.2.0 ([list](https://github.com/bugrasan/mdformat-sembr/blob/795e9f4580599ff4a5d27a597061a8ee090598e6/src/mdformat_sembr/_sembr.py#L41)) leave `fig.`, `no.` and `sec.` joined.
- [L572](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L572): `'ა'.islower()` is true on every Python, so "on Python 3.11" misleads; the cause is Ll against OLetter.
- [L95](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L95) and [L1431](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1431): also say that [`mdformat.text()` defaults to no extensions](https://github.com/hukkin/mdformat/blob/82912cdaea4fb830f751504486a7879c70526547/src/mdformat/_api.py#L17) and that [`--no-extensions` exists](https://github.com/hukkin/mdformat/blob/82912cdaea4fb830f751504486a7879c70526547/src/mdformat/_cli.py#L262-L266).
  The earlier "conflation" claim was retracted (X6).
- [L197-199](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L197-L199): other defaults are [hidden by Python's default warning filters](https://github.com/hukkin/mdformat/blob/82912cdaea4fb830f751504486a7879c70526547/src/mdformat/_cli.py#L292-L298), and an unhashable default crashes the CLI with `TypeError`; the plugin's own defaults are `None`, so low relevance.
- [L157](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L157): validation sits in the [`else` of the `--check` branch](https://github.com/hukkin/mdformat/blob/82912cdaea4fb830f751504486a7879c70526547/src/mdformat/_cli.py#L145-L155) of `_cli.py`; there is no early return.
- [L110-111](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L110-L111): [`_wrap`](https://github.com/hukkin/mdformat/blob/82912cdaea4fb830f751504486a7879c70526547/src/mdformat/renderer/_context.py#L348-L363) skips `textwrap` for `--wrap no`, and [`indent_width`](https://github.com/hukkin/mdformat/blob/82912cdaea4fb830f751504486a7879c70526547/src/mdformat/renderer/_context.py#L397) matters only to integer wrapping.
- [L269-281](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L269-L281): `re.split` loses the length of runs of wrap points, which the offsets need ([L180](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L180)); and the newline-inside-an-atom example list should add a hard break in link text and a link title (the rule itself is already general).
- [L300](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L300): the example `Lorem (ipsum sit). Dolor amet.` contains no link, image or code span.
  A replacement that does: `` See `a b`. Next [x y](u). ``.
- [L367](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L367): "the table acts only at candidate gaps" is not the reason; rules only veto, and a gap is a candidate only after a terminator.
- [L1213](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1213): "being later it decides wherever it matches" is moot, since both rules say `no` and order is irrelevant.

## 2. Clarity and conciseness

### C1. Pinning is stated four or five times

[L113](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L113), [L161-162](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L161-L162), [L210](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L210) (a pointer), [L310-313](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L310-L313) and [§3.4](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#34-emission-and-the-width-independence-property) ([L776-785](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L776-L785)).
Keep [L161-162](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L161-L162): [§3.6](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#36-failure-policy) cites it ([L851](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L851)), and "no part of this design may assume that [mdformat's wrap] will act" is stated nowhere else.
Trim [L113](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L113) and [L310-313](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L310-L313) against [§3.4](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#34-emission-and-the-width-independence-property).

### C2. [§3.3](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#33-sentence-detection) argues against a design nobody has seen ([L758-769](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L758-L769))

"Break / NoBreak / unmatched", "three-valued form" and "forcing verdict" occur only there, and "cascade" is never defined.
**Proposed fix:** two sentences: every check only vetoes, so order is free; a segment of only opening marks is a lone mark in a run.
Keep [L763-765](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L763-L765), which makes a trailing `\` safe (R5).

### C3. Repetition in [§3](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#3-algorithm) and [§4](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#4-config-surface)

- Composition order is stated at [L865](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L865), [L904](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L904), [L930](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L930) and [L964](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L964).
- The `is_md_equal` blindness argument repeats at [L617](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L617), [L807](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L807), [L821](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L821) and [L823-829](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L823-L829).
- [L915-916](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L915-L916) says "looked up first among the shipped sets" and "no order… is needed".
- [L494-496](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L494-L496) spends a paragraph on `Straße`, `ﬁ`, Turkish and sigma; two sentences would do.
- [L525-527](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L525-L527) repeats [L78](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L78).
- [L388-399](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L388-L399) and [L719-757](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L719-L757) restate [QUOTE-ROLES.md](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/QUOTE-ROLES.md).

### C4. Inconsistent or dangling references

- Macros reference "earlier ones" at [L530](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L530) and any macro at [L979](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L979).
- The [§3.4](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#34-emission-and-the-width-independence-property) emission table says "edge-safe ([§3.5](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#35-correctness-rules))" ([L781](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L781)), but [§3.5](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#35-correctness-rules) also has line-start rules.
- `mdformat-sentence-rules` ([L1175](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1175), [L1240](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1240)) is missing from [§2](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#2-name-packaging-and-the-hook-point)'s packaging list ([L57-78](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L57-L78)).
- [L809](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L809): "the same mechanism the guard uses" has no referent; the mechanism is pinning, [§3.1](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#31-segmentation).
- [L560](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L560): "Its known cost is unchanged" has no antecedent.
- [L625](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L625): "three jobs and one mistake" never names the mistake.
- [L620-622](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L620-L622): two bold headings stack.
- [L603](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L603): the table/code principle contradicts the capital test, and the shipped ellipsis rule is in neither the checks list ([L540-593](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L540-L593)) nor the table.
  The bracket-depth rule is called a "safety rule" although [§3.5](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#35-correctness-rules) is the safety section.

### C5. "Atom" is used for two different things

An atom is an inline node recorded whole ([L321 (§3.2)](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#32-inline-atoms)), and a link or image is one, so [L106](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L106) and [L1357](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1357) are correct.
The misuse is [L285](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L285) ("Segments are the atoms") and [L300](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L300) (`sit).` called an atom); say "segment" or "unit".

### C6. Other wording

- [L151](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L151): three limits follow, not two.
- [§2.5](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#25-the-three-wrap-modes) ([L239-248](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L239-L248)) reads out of order: it argues library callers are not silent, then says the warning cannot reach them.
- [L208](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L208) and [L215](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L215) each call something the most surprising; they have different scopes, so this is style.
- [L152-154](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L152-L154) packs three points into one item; [L343](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L343) "re-arming" is jargon.
- [L1456](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1456) is one run-on sentence of about 35 fixture families that overlaps table row 10.
- [L490](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L490) and [L655](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L655) call homo-case "measured"; it is argument.

## 3. Retracted or refuted in vetting

- **X1.** The tilde example at [L833](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L833) does not exercise the refusal: refuted, it is a deliberate negative control matching the fixture "a section that merely mentions one" at [L1456](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1456).
- **X2.** `cli_include` against the unknown-key rule ([L968](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L968) vs [L450](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L450)): retracted, [L968](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L968) states the behavior.
- **X3.** Dropping `Sr` and `Jr`, or making them conditional on a lowercase or comma context: withdrawn (R13).
- **X4.** [L552](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L552) "wrong three ways" lists only two: refuted, it lists three; "the ellipsis rule below" is fine.
- **X5.** [L622](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L622) against [L692](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L692) "this corpus": retracted.
- **X6.** The `extensions=set()` conflation at [L95](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L95) and [L1431](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1431): retracted as a defect, reduced to a wording note in R14.
- **X7.** Row 12 "not gating" against [L1395](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1395) "the requirement in each row is zero": refuted, they are different tables.
- **X8.** The Dr/Drive cost is shown only in passing ([L1218-1236](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1218-L1236)): refuted, [L1218](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1218) already says "full of street addresses and no doctors".
- **X9.** "atom" misused at [L106](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L106) and [L1357](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L1357): refuted (C5).
- **X10.** Widening `whole`, and the `after=`-based `St` rule: rejected by two vetters (R12, R4).
- **X11.** The `et al.` case as a contradiction of [L22](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md?plain=1#L22): reduced to a missing caveat (R3).

## 4. External sources cited

Pinned to the commit each tag points at.
No issue or pull-request page of any project is linked.

- mdformat 1.0.0: [`82912cd`](https://github.com/hukkin/mdformat/tree/82912cdaea4fb830f751504486a7879c70526547), the commit the tag `1.0.0` points at.
  The installed 1.0.0 package matched these files byte for byte in `_cli.py`, `_api.py`, `_util.py`, `plugins.py`, `renderer/_context.py` and `renderer/__init__.py`.
- mdformat-gfm 1.0.0: [`1c2d3c6`](https://github.com/hukkin/mdformat-gfm/tree/1c2d3c68019d93ff30c69482b0b19098b41b0a17).
- mdformat-sembr 0.2.0: [`795e9f4`](https://github.com/bugrasan/mdformat-sembr/tree/795e9f4580599ff4a5d27a597061a8ee090598e6), the GitHub mirror of the canonical Codeberg repository, at the same commit.
- rumdl 0.2.60: [`50dbfef`](https://github.com/rvben/rumdl/tree/50dbfef7cf08f1d28633b684c0884490a63094e3).
  Its sentence-boundary test is [`is_sentence_boundary`](https://github.com/rvben/rumdl/blob/50dbfef7cf08f1d28633b684c0884490a63094e3/src/utils/text_reflow.rs#L580) and its abbreviation check is [at line 759](https://github.com/rvben/rumdl/blob/50dbfef7cf08f1d28633b684c0884490a63094e3/src/utils/text_reflow.rs#L759).
- The Semantic Line Breaks specification that [§5](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/DESIGN.md#5-conformance-to-the-specification) measures against: [sembr.org](https://sembr.org), kept in this repository as [`notes/corpus/sembr.md`](https://github.com/aunger/mdformat-sentence/blob/819e75b69ad2e584280b57f46c01a972cad13d5e/notes/corpus/sembr.md).
