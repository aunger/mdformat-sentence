# Preserve mode: should the plugin keep the author's existing line breaks?

A note, not a specification.
`DESIGN.md` specifies sentence-only formatting and this note explains why it stays that way.

Everything marked measured was produced by execution against mdformat 1.0.0.
Everything else is argument.
Programs are in `experiments/`; the corpus question is in `corpus/README.md` and it matters more than it sounds.

______________________________________________________________________

## 0. Verdict

The plugin should not delete an author's line break automatically, in any mode, under any detector tried here.

Two detectors were built and measured.
A punctuation detector fails outright: it cannot see 41% of real Semantic Line Breaks.
A sentence-coverage detector separates hand-written sembr from geometric wrapping perfectly on the corpus, and is still not safe to act on destructively, for reasons that are about the *remedy* rather than the detector.

If a preserve mode ever ships it should be add-only: never delete, only add the missing sentence breaks.
The case it does not serve, a width-wrapped paragraph dropped into a sembr document, is not solvable inside a formatter, and §7 says where that signal actually lives.

______________________________________________________________________

## 1. What the seam makes possible

Measured, `probe.py` and `addonly.py`.

At the postprocessor the rendered string cannot distinguish the author's newline from a space, because both are already `\x00`.
But the postprocessor also receives `node`, and `node.children` carries `softbreak` nodes at exactly the author's line breaks.
Rendering the children individually and tracking cumulative offsets recovers those positions precisely.

Only on the first render pass.
A paragraph that pass 1 has collapsed arrives at pass 2 with children `['text']` and the information is gone.
This is not fatal: if pass 1 preserves a break, pass 2 re-parses it as a softbreak and preserves it again.
The arrangement is self-stabilising, and both add-only and every triage variant below measure idempotent.

So preservation is mechanically possible.
The rest of this note is about whether it is wise.

______________________________________________________________________

## 2. Detector A: punctuation. It fails.

The obvious detector asks whether a line break falls at a sentence or clause boundary, using rule 5's own punctuation, `,` `;` `:` and em dash.

Measured against the specification's own prose, `breaks.py`:

| | |
| --- | --- |
| author line breaks | 75 |
| carrying no punctuation at all | **31, or 41%** |
| recovered by a 36-word break-word list | 11 of 31 |
| still undetectable | 20 of 75, or **27%** |

The cause is structural rather than statistical.
Rule 6 breaks after a *dependent* clause, and rules 10 and 11 break before and after hyperlinks and inline markup, and none of those positions carries punctuation.
Real breaks from the specification that no punctuation rule can see:

```
_Semantic Line Breaks_ describe a set of conventions
for using insensitive vertical whitespace
Conventional markup languages like HTML and XML
```

A break-word list narrows the gap and cannot close it, and the version that recovers anything is the noisy one: two of its eleven recoveries are `for` and `and`, the two words most often wrong when they *make* a break.

This disqualifies punctuation as a per-gap keep rule and as the basis of any paragraph classifier built on it.

______________________________________________________________________

## 3. Detector B: sentence coverage. It works.

Define **coverage** of a paragraph, computed on the input layout before the plugin acts:

> Of the sentence boundaries strictly inside the paragraph, the fraction that already have a line break at them.

A paragraph with no internal sentence end returns 1.00 vacuously.
That is a definitional choice and it is load-bearing: single-sentence paragraphs broken at clause level are common in real sembr, and any other choice sends them to the destructive branch.

This detector never infers a clause boundary.
It asks only a question the plugin can already answer with §3.3, which is why it succeeds where detector A fails.

Measured, `triage2.py`:

| | coverage |
| --- | --- |
| real hand-written sembr, n=9 | **1.00** at min, median and max |
| the same text hard-wrapped at 62, 72, 80, n=27 | **0.00** median, 26 of 27 below 1.00 |

Perfect separation with an empty middle.
For contrast, a punctuation-ratio classifier reflows 31% of real sembr paragraphs at threshold 0.5 and 69% at 0.9.

One false negative is visible in `cov.py`: a width-wrapped paragraph scores 1.00 when the wrap happens to land just after a sentence end.
That error is in the safe direction, since it preserves junk rather than destroying meaning.

______________________________________________________________________

## 4. Why a good detector still does not license deletion

### 4.1 The remedy is disproportionate to the defect

When the detector fires it knows exactly which gap is missing a break.
That gap is the whole defect.

Measured, `edit.py`, on the most ordinary edit there is, appending a sentence to a line without breaking it:

| remedy | diff lines | clause breaks surviving, of 4 |
| --- | --- | --- |
| rewrap the paragraph | 9 | **0** |
| add the missing break | **1** | **4** |

Both leave a clean paragraph untouched and both are idempotent.
Rewrapping destroys *n* good breaks to repair one bad gap.
The minimal remedy is `keep = existing_breaks | sentence_ends`, which is plain add-only.

### 4.2 Any threshold reintroduces paragraph-sized diffs

Measured, `thresh.py`.
A 12-line paragraph at coverage 0.33; one hand-added break moves it to 0.67; the remedy flips; the diff is **18 lines**, at every threshold tried.

The general rule, which holds for every design in this note: the diff blast radius of a formatter equals the domain of its decision function.
A per-gap rule can perturb one gap.
A per-paragraph rule can perturb the whole paragraph.
For any threshold in (0,1] there is an input one edit away from crossing it.

### 4.3 A threshold of exactly zero is better, and still not safe

Rewrapping only when *no* internal sentence end is broken demands unanimous evidence.
Measured, `k0.py`:

| edit to a hand-sembr paragraph | coverage | branch | diff | clause breaks |
| --- | --- | --- | --- | --- |
| append a sentence, don't break it | 1.00 → 0.50 | repair | 1 line | 4 → 4 |
| remove the break at the sentence end | 1.00 → 0.00 | **rewrap** | 8 lines | 4 → **0** |

So it survives the common edit, which is better than expected.
It dies on the other one, and this measurement says how easily:

> **How many internal sentence ends does a real sembr paragraph have?**
> sembr.org spec: 7 of 9 have exactly one.
> `DESIGN.md`: 27 of 52 have exactly one.

For those, coverage is binary and a single removed break zeroes it.
Unanimity over a set of size one is not unanimity.

### 4.4 The loss is silent and irreversible

Both branches are individually idempotent, so `--check` is green before the destruction and green after it.
Restoring the edit does not restore the layout, because the break positions no longer exist in the file and cannot be derived from the text.
Rewrapped output scores 1.00, so the paragraph is classified preserve forever after and its machine-chosen breaks are defended indefinitely.
Information flows one way only.

______________________________________________________________________

## 5. `DESIGN.md` §6.2 would certify a destructive plugin

Every candidate mode was run end to end.
All of them pass idempotency and all of them pass §6.1's width-independence invariant, including the mode that silently deletes 41% of an author's line breaks.

Idempotency is necessary and nowhere near sufficient.
Any preserve mode needs two invariants the gate does not have:

**Break preservation.** No author line break inside a paragraph is removed unless the mode's contract says it removes all of them.
Total, no corpus, no oracle, and it fails every deleting variant immediately.

**Diff locality.** For every single-character edit the output diff is at most *k* lines for small fixed *k*, independent of paragraph length.
Measured *k* is 2 for add-only, 3 for sentence-only, unbounded for anything per-paragraph.

______________________________________________________________________

## 6. Is "a pure function of the text" the right property?

**For.** A canonical form is most of what a formatter is for on a team.
If output depends on input layout, `--check` stops defining a normal form and asks only whether the file is a fixed point.
Add-only's preserved set only ever grows: every accidental break ever introduced, by an auto-fill, a paste, or a bad merge, is frozen and thereafter defended.

**Against.** mdformat already made the opposite choice and made it the default, and its documentation gives hand-written semantic line breaks as the reason `wrap = "keep"` is the default.
The premise of sembr is that the line break carries information the text does not.
If it does, a formatter that is a pure function of the text is by construction one that deletes that channel.
Black can be a pure function because layout in Python carries no meaning; the argument does not transfer to prose.

**Resolution.** Purity is not the deciding axis, since both principles are defensible.
The deciding axis is whether the preserved set is bounded and author-controlled.
Sentence-only: empty, trivially bounded.
Add-only: unbounded, grows monotonically with every accident.
Anything inferring: neither bounded nor author-controlled, and it deletes as well, which is strictly worse.

______________________________________________________________________

## 7. The case that motivates all of this, and where its signal actually lives

An agent inserts a width-wrapped paragraph into a hand-sembr document, and the check runs in CI with no human present.

Sentence-only flattens the whole document, which is not a repair.
Add-only freezes the new paragraph's geometric breaks forever.
Any automatic deleting rule is §4.

The information needed is "was this paragraph written by something that does not know about sembr", and that is not in the text.
It is in version control.
A pre-commit wrapper that runs sentence-only over *changed line ranges* only has blast radius bounded by what was actually edited and needs no heuristic anywhere.
mdformat cannot do this, since it sees one file and no history, so it is a wrapper rather than a plugin mode.

The plugin-only answer that survives CI is weaker but safe: add-only, never delete, plus a warning naming any paragraph whose coverage is zero.
The warning channel exists and is measured: `mdformat.renderer.LOGGER`, with a `RendererWarningPrinter` handler attached in `_cli.py` that prints WARNING and above to stderr.
It is attached on the CLI path only, so `mdformat.text()` callers see nothing unless they configure logging themselves.

______________________________________________________________________

## 8. Recommendation

1. Keep sentence-only exactly as `DESIGN.md` specifies it. Nothing in this note amends the specification.
1. Reject every deleting variant: punctuation per-gap, punctuation triage, coverage thresholds, and coverage at exactly zero.
1. If a preserve mode ships, ship add-only: explicit opt-in, per-gap, no heuristic, documented as freezing existing breaks including accidental ones, with §6.2 extended by the two invariants in §5.
1. Solve the agent-insertion case outside the plugin, in a VCS-aware wrapper.

______________________________________________________________________

## 9. Corrections

Both errors were stated confidently before being caught, and both shaped the argument, so they stay.

**A clause-punctuation keep rule was proposed as "the variant that fixes most of it".**
It was tested on two hand-made examples and looked excellent.
Against real sembr it deletes 41% of the author's breaks (§2).
The corpus was the error: `DESIGN.md` is pure sentence-per-line, so any layout detector scores perfectly against it.

**A coverage threshold was then proposed to choose between remedies.**
It reintroduces exactly the paragraph-sized blast radius the coverage detector had just been praised for avoiding (§4.2), measured at 18 diff lines from one edit.

A third claim was overcorrected: that no deleting rule can ever be stable.
The true statement is narrower.
What matters is how far an input must travel to flip the branch, and §4.3 measures that distance as one edit for roughly half of real paragraphs.
