# Preserve mode: should the plugin keep the author's existing line breaks?

A note, not a specification.
`DESIGN.md` specifies sentence-only formatting; this records the ideas that were tried against that decision and what each one turned out to establish.

It is written as a ladder.
Each section is one idea, stated in its strongest form, then what it buys and what it costs.
The ideas were not reached in a straight line and several of them are wrong; they are kept because the wrong ones are what constrain the right one.

Measured claims were produced by execution against mdformat 1.0.0.
Everything else is argument and is marked as such.
Programs are in `experiments/`, and `corpus/README.md` explains why the corpus choice decides most of these answers.

______________________________________________________________________

## 0. Where the ladder ends

No idea here licenses the plugin to delete an author's line break automatically.
The one that survives is **add-only**: never delete, only add the missing sentence breaks, behind an explicit opt-in.
The case that motivates the whole question, a width-wrapped paragraph dropped into a hand-broken document, is not solvable inside a formatter; §10 says where its signal actually lives.

______________________________________________________________________

## 1. Ground: what the seam permits

Measured, `probe.py` and `addonly.py`.

At the postprocessor the rendered string cannot tell the author's newline from a space, because both are already `\x00`.
The postprocessor also receives `node`, though, and `node.children` carries `softbreak` nodes at exactly the author's line breaks.
Rendering the children individually and tracking cumulative offsets recovers those positions precisely.

Only on the first render pass.
A paragraph that pass 1 collapsed arrives at pass 2 with children `['text']`, and the information is gone.
That is not fatal: if pass 1 preserves a break, pass 2 re-parses it as a softbreak and preserves it again, so the arrangement is self-stabilising.
Every variant below measures idempotent for this reason, which is also why idempotency turns out to discriminate nothing (§11).

So preservation is mechanically available.
The ladder is about whether it is wise, and which breaks.

______________________________________________________________________

## 2. Idea: preserve every existing break

Add-only. `keep = existing_breaks | sentence_ends`.

**Buys.** No heuristic anywhere, so nothing can be wrong. Measured idempotent and width-independent, `proto.py`. Diff blast radius of 2 lines under a one-character edit, flat regardless of paragraph size.

**Costs.** Output stops being a pure function of the text: the same sentence in two layouts gives two outputs.
Worse, the preserved set only ever grows. Every accidental break ever introduced, by an editor auto-fill, a paste from a hard-wrapped source, or a bad merge, is frozen and thereafter actively defended.
Measured: a paragraph hard-wrapped at 62 columns keeps all of those breaks forever.

**Status.** Survives, and remains the only survivor. Everything below is an attempt to fix its one real defect, the monotone accretion of junk.

______________________________________________________________________

## 3. Idea: preserve only breaks at clause punctuation

Keep an author break when the text to its left ends in rule 5's own punctuation, `,` `;` `:` or em dash.
Never add a clause break, only decline to destroy one, so there are zero false additions by construction.

**Buys.** On toy examples it looks excellent: it keeps hand-written clause breaks and correctly collapses hard wrapping.

**Costs.** Measured against real hand-written sembr, `breaks.py`, it deletes **45% of the author's line breaks**, because that share carry no punctuation at all.

**Why.** Structural, not a tuning problem.
Rule 6 breaks after a *dependent* clause, and there is nothing there to match.
Real breaks from the specification's own prose that no punctuation rule can see:

```
_Semantic Line Breaks_ describe a set of conventions
for using insensitive vertical whitespace
Conventional markup languages like HTML and XML
```

**Status.** Rejected. A keep rule that silently deletes nearly half an author's breaks is not a preserve mode.

**Note on rules 10 and 11.** They break before and after hyperlinks and before inline markup, and unlike rule 6 those positions *are* trivially matchable; at this seam better than trivially, since mdformat already collapses a link into a single atom.
They account for 8 of the 88 breaks on this corpus, whose prose holds 12 reference links across 122 lines with 10 of those lines opening with one.
An earlier reading of this note put them at zero; that was the paragraph extractor deleting every line that starts with `[`, which is exactly the evidence, and `breaks.py` records the correction.
So they recover 8 of the 40 unpunctuated breaks and leave 32 that nothing lexical reaches, and this corpus still says little about prose that uses links heavily.

______________________________________________________________________

## 4. Idea: add break words to the keep rule

Rule 6 has no punctuation, but it has vocabulary. Keep a break whose following word is a subordinator or coordinator.

**Buys.** Measured, `breaks.py`: a 36-word list recovers 12 of the 32 rule 6 breaks, taking silent deletion from 45% down to **23%** once rules 10 and 11 take their 8.

**Costs.** Still deletes more than a quarter of an author's breaks.
The residual has no lexical signal at all; the words following those breaks are `to`, `exhibit`, `without`, `makes`, `the`, `can`, `in`.
And the list that recovers anything is the noisy one: two of its eleven recoveries are `for` and `and`, the two words most often wrong when they *make* a break.
A conservative 14-word list recovers 2 of 32.

**Status.** Rejected. It narrows the gap and cannot close it, because you cannot narrow your way to a rule that fires where there is no signal.

______________________________________________________________________

## 5. Idea: stop judging gaps, judge paragraphs

If per-gap punctuation cannot decide, perhaps the paragraph as a whole can: score what fraction of its line ends fall at sentence or clause boundaries, and preserve the paragraph if the score is high, reflow it if low.

**Costs.** Measured: at threshold 0.5 this reflows 31% of real sembr paragraphs, and at 0.9 it reflows 69%.
The score distribution is spread across the whole range, with five paragraphs at exactly 0.000, so no threshold sits safely under it.
No program in `experiments/` reproduces these three numbers; they were produced by a scorer that was not kept, so take them as the weakest measurements in this note.

**Status.** Rejected, and it inherits §3's blindness rather than escaping it. Aggregating a signal that is absent does not produce a signal.

**Trap worth recording.** Evaluated against `DESIGN.md` this idea looks flawless: all 62 of its paragraphs that have an internal sentence end score 1.000 with zero variance, because that document is already pure sentence-per-line.
The corpus, not the threshold, was doing the work. See `corpus/README.md`.

______________________________________________________________________

## 6. Idea: judge the paragraph on sentences only, which are knowable

The failure in §3 to §5 is always the same: inferring clause boundaries.
So infer nothing about clauses. Ask only a question §3.3 of `DESIGN.md` can already answer.

> Scan the paragraph as the author left it.
> If every sentence end is already followed by a line break, the layout respects the promise; assume the extra breaks are deliberate and preserve them all.
> If some sentence end is not, the paragraph is not sembr-shaped; rewrap it sentence-per-line.

**Buys.** Measured, `triage2.py`, and it is a categorically better detector than anything above.

| | score |
| --- | --- |
| real hand-written sembr, n=9 | 1.00 at min, median and max |
| the same text hard-wrapped at 62, 72, 80, n=27 | 0.00 median, 26 of 27 below 1.00 |

Near-perfect separation against 31–69% misclassification for §5, but not perfect: three of the 27 hard-wrapped paragraphs score above zero, two at 0.50 (one at width 62, one at width 72) and one at 1.00 (at width 72).
The other 24 score 0.00, so the middle is nearly empty rather than empty.
The 1.00 is the case that matters, because it is indistinguishable from the hand-written class; §7 names the mechanism, a wrap that happens to land just after a sentence end, so it is a false *preserve*, in the safe direction.
It is also the only idea here that addresses §2's real defect, because it is the only one that can recognise geometric wrapping as geometric.

**Costs.** The detector is sound; the *remedy* is not. See §8.

**Status.** The detector survives and is the most useful thing on this ladder. The all-or-nothing remedy attached to it does not.

______________________________________________________________________

## 7. Idea: soften the all-or-nothing rule into a threshold

Rather than requiring *every* sentence end to be broken, define

> **coverage** = of the sentence boundaries strictly inside a paragraph, the fraction that already have a line break at them,

with a paragraph having no internal sentence end scoring 1.00 vacuously, and let a threshold *k* decide which remedy applies.

The vacuous case is a definitional choice and it is load-bearing: single-sentence paragraphs broken at clause level are common in real sembr, and any other choice sends them to the destructive branch.

**Costs.** Measured, `thresh.py`.
A 12-line paragraph at coverage 0.33; one hand-added break moves it to 0.67; the remedy flips; the diff is **18 lines**. At every threshold tried.

**Why.** The general rule, which governs this whole ladder: *the diff blast radius of a formatter equals the domain of its decision function.*
A per-gap rule can perturb one gap. A per-paragraph rule can perturb the whole paragraph.
For any threshold greater than zero and at most one there is an input one edit away from crossing it.

**Status.** Rejected, and it is worse than §6 rather than better. Softening a binary rule into a graded one reintroduces exactly the instability the graded rule was meant to smooth.

Also measured, `cov.py`: a width-wrapped paragraph scores 1.00 when the wrap happens to land just after a sentence end. That error is in the safe direction, preserving junk rather than destroying meaning.

______________________________________________________________________

## 8. Idea: keep §6's trigger, shrink the remedy

When the detector fires it knows exactly which gap is missing a break.
That gap is the whole defect. Repair it and leave everything else alone.

**Buys.** Measured, `edit.py`, on the most ordinary edit there is, appending a sentence to a line without breaking it:

| remedy | diff lines | clause breaks surviving, of 4 |
| --- | --- | --- |
| rewrap the paragraph | 9 | 0 |
| add the missing break | 1 | 4 |

Both leave a clean paragraph untouched and both are idempotent.

**The catch.** `keep = existing_breaks | sentence_ends` is §2. The minimal remedy *is* add-only, and §6's detector adds nothing to it: where coverage is 1.00 there is nothing to add, and where it is not, add-only already adds exactly the missing breaks.
So this idea is not a new mode. It is a demonstration that the detector's value is diagnostic rather than operative.

**Does a threshold of exactly zero rescue the destructive branch?** It demands unanimous evidence, and it is the best version of §6. Measured, `k0.py`:

| edit to a hand-sembr paragraph | coverage | branch | diff | clause breaks |
| --- | --- | --- | --- | --- |
| append a sentence, don't break it | 1.00 → 0.50 | repair | 1 line | 4 → 4 |
| remove the break at a sentence end | 1.00 → 0.00 | rewrap | 8 lines | 4 → 0 |

It survives the common edit. It dies on the other, and this measurement says how easily:

> **How many internal sentence ends does a real sembr paragraph have?**
> sembr.org spec: 7 of 9 have exactly one.
> `DESIGN.md`: 28 of 62 have exactly one.

For those, the score is binary and a single removed break zeroes it.
Unanimity over a set of size one is not unanimity.

**And the loss is silent.** Both branches are idempotent, so `--check` is green either side of it.
Restoring the edit does not restore the layout, because the break positions no longer exist in the file and cannot be derived from the text.
Rewrapped output scores 1.00, so the paragraph is classified preserve forever after and its machine-chosen breaks are defended indefinitely.

**Status.** The remedy collapses into §2. The destructive branch is rejected at every threshold including zero.

______________________________________________________________________

## 9. Idea: let the author declare it

Stop inferring. A preceding `<!-- sembr:keep -->` marks a paragraph as hand-laid.

**Buys.** Measured reachable from the inline postprocessor via `node.parent.parent.children` and an index lookup; mdformat preserves the comment verbatim and it survives both passes; the mode is idempotent and width-independent.
No heuristic, so no false positives, no false negatives, no blast radius when wrong.
It is the only design here whose preserved set is both bounded and author-controlled.

**Costs.** It inverts badly. In a document that is *mostly* sembr you would mark nearly every paragraph, and at that point `wrap = "keep"` for the whole file is what you actually want, and mdformat gives that for free.

**Unmeasured.** Only top-level paragraphs were tested. A paragraph inside a list item or blockquote has a different `parent.parent`, and the first paragraph of a document has no previous sibling.

**Status.** Sound but redundant against mdformat's own default in the case where it would be used most.

______________________________________________________________________

## 10. Idea: diagnose, don't decide; and scope by version control

The case that motivates all of this: an agent inserts a width-wrapped paragraph into a hand-broken document, and the check runs in CI with no human present.

Sentence-only flattens the whole document, which is not a repair but a different destruction.
Add-only freezes the new paragraph's geometric breaks.
Every automatic deleting rule is §3 to §8.

The information actually needed is "was this paragraph written by something that does not know about sembr", and that is not in the text.
It is in version control.
A pre-commit wrapper that runs sentence-only over **changed line ranges only** has blast radius bounded by what was edited, and needs no heuristic anywhere.
This is the same principle as §9, with the commit boundary doing the declaring instead of a comment.
mdformat cannot do it, since it sees one file and no history, so it is a wrapper rather than a plugin mode.

The plugin-only answer that survives CI is weaker but safe: add-only, never delete, plus a warning naming any paragraph whose layout ignores sentence boundaries.
The warning channel exists and is measured: `mdformat.renderer.LOGGER`, with a `RendererWarningPrinter` handler attached in `_cli.py` that prints WARNING and above to stderr.
It is attached on the CLI path only, but that does not make the API path silent: with no handler configured, `logging.lastResort` still writes the message to stderr, unprefixed.
What the CLI adds is the `Warning: ` prefix, and only on the first render pass.
Measured, `wraparg.py` §3; `MDFORMAT-WRAP-AND-OVERRIDES.md` §7 is the full account.

**Status.** The VCS-scoped wrapper is the only design that serves the motivating case without a heuristic. It is out of scope for the plugin and worth building separately.

______________________________________________________________________

## 11. What this says about `DESIGN.md` §6.2

Every variant on this ladder was run end to end, and **all of them pass idempotency and all of them pass §6.1's width-independence invariant** — including the one that silently deletes 45% of an author's line breaks.

Idempotency is necessary and nowhere near sufficient.
Two invariants would catch what the current gate cannot:

**Break preservation.** No author line break inside a paragraph is removed unless the mode's contract says it removes all of them.
Total, no corpus, no oracle, and it fails every deleting variant immediately.

**Diff locality.** For every single-character edit the output diff is at most *k* lines for small fixed *k*, independent of paragraph length.
Measured *k* is 2 for add-only, 3 for sentence-only, unbounded for anything per-paragraph.

This is the one finding here that applies whether or not a preserve mode is ever built.

______________________________________________________________________

## 12. Is "a pure function of the text" the right thing to insist on?

**For.** A canonical form is most of what a formatter is for on a team.
If output depends on input layout, `--check` stops defining a normal form and asks only whether the file is a fixed point, and two contributors' files never converge.

**Against.** mdformat already made the opposite choice and made it the default, and its documentation gives hand-written semantic line breaks as the reason `wrap = "keep"` is the default.
The premise of sembr is that the line break carries information the text does not.
If it does, a formatter that is a pure function of the text is by construction one that deletes that channel.
Black can be a pure function because layout in Python carries no meaning; the argument does not transfer to prose.

**Resolution.** Purity is not the deciding axis, since both positions are defensible.
The deciding axis is whether the preserved set is bounded and author-controlled.
Sentence-only: empty, trivially bounded.
Add-only: unbounded, grows monotonically with every accident.
Anything inferring: neither bounded nor author-controlled, and it deletes as well.

______________________________________________________________________

## 13. Recommendation

1. Keep sentence-only exactly as `DESIGN.md` specifies it. Nothing on this ladder amends the specification.
1. Reject every deleting variant: per-gap punctuation, punctuation plus break words, paragraph scoring, coverage thresholds, and coverage at exactly zero.
1. Treat §2, add-only, as a possible future mode. If it is ever built: explicit opt-in, per-gap, no heuristic, documented as freezing existing breaks including accidental ones, with §6.2 extended by the two invariants in §11. Whether it is worth building is not a question this note settles.
1. The agent-insertion case is not solvable inside the plugin; §10 sets out where its signal lives.

______________________________________________________________________

## 14. Wrong turns, kept

**§3 was proposed as "the variant that fixes most of it"** on the strength of two hand-made examples. Against real sembr it deletes 45% of the author's breaks. The corpus was the error, and §5 records the same trap in its general form.

**§7 was proposed as the fix for §6's remedy problem.** It reintroduces the paragraph-sized blast radius that §6 had just been credited with avoiding, measured at 18 diff lines from one edit.

**A third claim was overcorrected:** that no deleting rule can ever be stable, because a paragraph-scale branch always has paragraph-scale blast radius.
The true statement is narrower. What matters is how far an input must travel to flip the branch, and §8 measures that distance as one edit for roughly half of real paragraphs. The conclusion holds; the reasoning given for it was too broad.

**Rules 10 and 11 were described as having "nothing to match on",** lumped in with rule 6. They are trivially matchable and §3 now says so.
