# Design review, 2026-10-06: where mdformat-sentence hooks into mdformat

A record, not a specification.
`DESIGN.md` at `7b7f12b` was reviewed by a panel of four Claude agents, two on Opus and two on Sonnet at different effort levels, who worked independently and then reached this consensus together; all four signed it, with no dissent.
It is kept for its evidence register (§3), which says which claims were run and by how many members, and for the alternatives it rejected (§4).

How to read it now:

- **`DESIGN.md` decides wherever the two differ.** One difference is deliberate: C4 lists "raw inline HTML" as an opener, and `DESIGN.md` narrows that to a segment that is nothing but tags, keeping the earlier decision that `<em>then</em>` is tested at its word.
- **Its scripts and board are gone.** Paths under `/tmp/claude-0/panel/` no longer exist. The results that matter are reproduced by `experiments/seam.py`, `experiments/seam_mkdocs.py` and `experiments/recorder.py`, and the upstream findings are in the `quirks-*.md` files.
- **Section numbers and line numbers refer to `DESIGN.md` at `7b7f12b`**, before the review's recommendations were applied.
- **It says "seam" where `DESIGN.md` now says "hook point":** the place in mdformat's render where the plugin runs.
- Deferred items are carried in `FUTURE-WORK.md` and accepted costs in `TRADE-OFFS.md`.

This is revision 2 of the consensus, sha256 prefix `244ee509c970`, unchanged below this preamble except for its title and the abbreviated SHA of the commit it reviewed, which a history rewrite changed.

______________________________________________________________________

**Panel:** opus-high, opus-xhigh (facilitator), sonnet-max, sonnet-high.
**Subject:** `DESIGN.md` at `7b7f12b`, against mdformat 1.0.0.
**Dissents:** none recorded. The sign-offs are `signoff-<name>.md`.
**Revision 2:** this revision folds in the round-03 files and the corrections in `signoff-sonnet-max.md`; `board/04-opus-xhigh.md` lists what was taken.
C1 to C7 are unchanged in substance from revision 1 (09:35 UTC, sha256 `fa7fd853c73e`).
**Evidence:** every result below was executed unless it is marked *reasoned* or *read*.
"n" is the number of members who ran a claim in their own kernel and venv.
Scripts are under `/tmp/claude-0/panel/work/<member>/`, and the board's discussion is in `/tmp/claude-0/panel/board/`.

## 1. Recommendation

**Which seam:** `RENDERERS["inline"]`, as the current spec has it.

**Should the walk stay:** its *product* stays and its *mechanism* goes.
Atoms, their types and their offsets still come from the tree.
They are recorded during the one real render instead of being re-rendered.
The panel calls this **A-rec**.

- **C1. The seam is `RENDERERS["inline"]`.**
  The plugin's renderer calls `DEFAULT_RENDERERS["inline"]` and decides the gaps before any plugin's `inline` postprocessor runs.
  An `inline` postprocessor whose place in the chain is left to load order fails §1's width independence under real co-plugins, with or without a walk (R1, R2).
  That rules out options B and C as briefed.
  One that `update_mdit` moves to the front of the chain is order-safe, and is rejected for the reasons under Alternatives considered (§4, E).
- **C2. A-rec.**
  The renderer passes mdformat a context, `context._replace(postprocessors=…)`, whose postprocessor map appends one recorder, last, to the chain of every node type rendered beneath the inline node.
  The recorder notes each node's final rendering and returns it unchanged.
  - Offsets come from the records.
  - The top-level children's records concatenate to the text by construction.
  - A container's children are located by finding their joined records inside the container's record.
  - There is no second render, no env copy and no throwaway copy. Finding #3's class, and the co-plugin env-state hole (R7), are gone by construction.
  - Under `--wrap keep` the renderer returns mdformat's rendering without installing the recorder.
- **C3. A node whose children were not rendered, or whose children's joined records are not found exactly once in its own record, is an atom.**
  That covers gfm's bare URL (`gfm_autolink`), mkdocs's `{…}` attr list, and any co-plugin container that transforms its children.
  Such a node is never a reason to back off.
- **C4. Closed-world openers.**
  Only a code span, an image, an autolink or raw inline HTML opens a sentence.
  An unknown leaf, or a C3 atom, is an atom for the terminator and bracket rules, and it opens nothing. It is not read through the capital test either.
- **C5. The atom-terminator test reads the terminator's position**, after the footnote strip and the closer skip, not the segment's last character.
- **C6. Line-start safety covers co-plugin definition syntax**, matched against mdformat's escaped text on the line the newline would open: `[label]:`, `*[label]:` (labels may contain spaces) and `(label)=`.
  The list is declared closed over the co-plugins tested.
- **C7. The §3.6 back-off becomes a tripwire.**
  The plugin backs off only if the top-level records do not concatenate to the text. That cannot happen on mdformat 1.0.0; it exists to catch upstream drift.
  It is logged at `DEBUG`, and C3 atoms are counted at `DEBUG`.

## 2. Why

**The seam question is decided by load order, not by the walk.**
Two co-plugins rewrite the inline text at an integer `--wrap`.

- mdformat-mkdocs, inside a list item it re-wraps, inserts U+E000 filler words between wrap points at width-dependent positions.
- mdformat-gfm glues `xxxx` to a task item's first word.

A postprocessor that runs after either one decides on different text at different widths, even if it reads text only and never walks the tree (R1, R2).
Under the API that order follows `PYTHONHASHSEED` (R3).
A renderer runs before every postprocessor of its node type, and every renderer variant was width-independent in both orders (R4).

**Two corrections to the brief.**

- Item 6 ("a text-only plugin as a postprocessor works with gfm in both orders… the seam was sound until the walk arrived") is false in general.
  - With gfm first, it holds only for inputs where no rule reads a task item's first word (R2).
  - With mkdocs first, it fails whenever mkdocs re-wraps a list item: 9 of 41 documents and 123 of 150 random nested-list documents (R1).
- Finding #3 is a real impurity, but every known trigger is an input plain mdformat 1.0.0 already corrupts, which the CLI refuses (R8).
  The seam change rests on #1, R1 and R2, not on #3.

**The walk question is decided by what the re-render costs.**

- Read literally, the spec's walk backs off on gfm bare URLs containing `_(`, `__` or `*` (2 of 150,170 paragraphs in sonnet-high's corpus) and on mkdocs attr lists (36 of 150,286) (R6).
- Its shallow env copy lets a stateful co-plugin silently change later paragraphs. The co-plugin was constructed; none of the 48 sources read has such state (R7).
- It costs 2.5 to 3 times what the recorder costs (R17).

The recorder gives exactly the walk's atoms wherever the walk succeeds (R5), handles the cases where it fails (C3), and fails loudly if upstream changes the convention it rides on (K2).

**The tree's atoms are kept** because they give a co-plugin's syntax (wikilinks, footnote refs, math, roles) atom status with no recognizer of its own.
A text scanner of mdformat's canonical output matches the tree on core syntax, but it is wrong on shortcut references and on plugin atoms, and wrong in the direction of adding breaks (§4, C′).

**The opener rule is closed** because the open-world rule deletes content (R9) and buys almost nothing (R10).

## 3. Evidence register

| # | claim | ran by | n |
| --- | --- | --- | --- |
| R1 | mkdocs's U+E000 fillers make even a text-only `inline` postprocessor width-dependent when mkdocs loads first, wherever mkdocs re-wraps a list item: 9 of 41 documents (0 of 41 when it loads after the postprocessor) and 123 of 150 random nested-list documents | opus-high E1, opus-xhigh E3 and its re-run of sonnet-max's `seam_mkdocs.py`, sonnet-high matrix, sonnet-max F1, T12, `r3_c_mkdocs_first.py` | 4 |
| R2 | gfm's `xxxx` makes a text-only postprocessor miss a rule on a task item's first word (`- [ ] Dr. Smith…`, `- [ ] Mr. Smith…`) at `--wrap 20/40/80` | opus-xhigh E3, sonnet-high `t4.py`, sonnet-max T3 | 3 |
| R3 | API load order follows `PYTHONHASHSEED`; so does the winner of a renderer conflict, 6 of 12 seeds each way | `seam.py` (opus-xhigh, sonnet-high, sonnet-max); sonnet-max `t15`, `t7` | 3 / 1 |
| R4 | every renderer variant is width-independent and idempotent, and render-equal except on R12's input, with gfm and mkdocs in both orders, `--wrap 1` to `100000` included | all four; sonnet-max T12 for extreme widths, and a 697-job re-run against revision 1 | 4 |
| R5 | A-rec gives exactly the spec walk's atoms wherever the walk succeeds | opus-high E2, opus-xhigh E6 (1644 renders × 5 sets), sonnet-high (about 150k paragraphs), sonnet-max F3 (22 sets) | 4 |
| R6 | the literal walk backs off on gfm bare URLs with `_(`, `__` or `*` (e.g. `https://en.wikipedia.org/wiki/Foo_(bar)`; 2 of 150,170 paragraphs) and on mkdocs `{…}` (36 of 150,286) | opus-xhigh E5 and its `t3.py` re-run, sonnet-high, opus-high (corrected phase 1), sonnet-max T4 | 4 |
| R7 | the walk's shallow env copy lets a stateful co-plugin silently change later paragraphs' real output, with no back-off; §3.1's "§6.2's back-off row is what would show it" is wrong. The co-plugin was constructed, and a static read of the 48 sources (direct writes only) found none with such state | opus-high E3, sonnet-max T5; census `r3_state_census*.py` | 2 |
| R8 | every finding-#3 trigger is input plain mdformat 1.0.0 already corrupts; the CLI refuses it | opus-high E4 (24 of 80 cases), opus-xhigh E1, sonnet-high, sonnet-max | 4 |
| R9 | the open-world opener lets mdformat-footnote turn `Sentence one. [^x]: not a definition, just text.` into a definition on pass 2, giving `'Sentence one.\n'` with both notes' text gone | sonnet-max F5 and T6 (using sonnet-high's code), opus-high, opus-xhigh `r1_openers.py`, sonnet-high | 4 |
| R10 | openers beyond the four types are worth 0 lines in real documents (35 for sonnet-max, 31 for opus-xhigh, 5 plugin sets) and 24 gaps in about 150k paragraphs, all sentences opening with a gfm bare URL. Reading C4 strictly, not through the capital test, changes 0 of 81 documents and 0 of 31 files | sonnet-max T7 and T18, opus-xhigh `r1_policy_count.py`, sonnet-high | 3 (strictness: 2) |
| R11 | "last character inside an atom" loses `hand.[^1] This` with mdformat-footnote; the terminator-position test restores it and moves nothing else (4 lines in 81 documents) | opus-xhigh E8, sonnet-high, sonnet-max T8 | 3 |
| R12 | pinning hands mkdocs literal spaces: `The term \[x\](see the y note) is escaped.` changes render in every placement before mkdocs; mkdocs alone does the same at `--wrap keep`; `[text](my url)` is fine | opus-xhigh E9, sonnet-high, sonnet-max T2 and a CLI re-run | 3 |
| R13 | co-plugin line-start definitions need a veto on mdformat's *escaped* text (`\*\[HTML\]:`, `[^x]:`, `(Label)=`); a spaced label (`*[Hyper Text]:`) needs the whole line read, not the next segment; 0 real documents changed | escaped form: sonnet-max T9, opus-xhigh, opus-high `veto.py`. Whole line: opus-xhigh `r2_veto.py`, sonnet-max T14, opus-high `veto2.py` | 3 / 3 |
| R14 | 0 of 48 plugin sources define an `inline` renderer; `paragraph` renderers come from mdformat-hatena and mdformat-sentencebreak; `inline` postprocessors from gfm, mkdocs and openmmlab (a gfm copy with the same `xxxx`) | opus-xhigh E10, sonnet-max T10 (static read) | 2 |
| R15 | D2, a `paragraph` renderer chaining over the inline owner, composes with an `inline` owner but not with a `paragraph` owner; A-rec composes with a `paragraph` owner | sonnet-max T1 | 1 |
| R16 | a `root` postprocessor canary fires exactly when another plugin took the `inline` slot, once per pass, and is silent otherwise; it can name the owner | fires: sonnet-max T11, sonnet-high `r3.py`. Names the owner: sonnet-max T11 | 2 / 1 |
| R17 | A-rec adds about a third to two fifths of the walk's added time: +0.16 to +0.19 s against +0.47 to +0.50 s on 170 KB; +0.26 s against +0.72 s on the 31-file corpus | sonnet-max F4, opus-xhigh E6 | 2 |
| R18 | a dry run of the real paragraph pipeline works from the `inline` slot for render-level hazards (task box, enumerators, `<div>` indent), not for parse-level ones. Compared against a dry run of the all-pinned text, it reproduces §3.5's list exactly: 81 documents under 4 plugin sets and 3 widths, and 696 files under gfm and under mkdocs, 0 differences | works: sonnet-high `verify.py`, sonnet-max T13. All-pinned comparison: sonnet-max T13, T17 | 2 / 1 |
| R19 | R1, R2, R4 and R9 hold on Python 3.10, 3.11, 3.12 and 3.13 | sonnet-max `r2_pycompat.py` | 1 |
| R20 | mdformat 1.0.0 and every co-plugin version tested are the latest releases | sonnet-max (`pip index versions`) | 1 |
| R21 | the S10 fixtures fail where they should; A-rec fails only the R12 fixture; with each fixture's rule disabled, the fixture fails | sonnet-max `r2_gate_fixtures.py` | 1 |
| R22 | a dry-run veto that compares against the *decided* text misfires under mkdocs, whose `inline` postprocessor rewrites `%20` (198 spurious vetoes across 28 of 81 documents; 2 and 4 false vetoes on two inputs) | sonnet-max round 02, sonnet-high `verify.py` round 03 | 2 |

What the decision rests on:

- **The seam question** rests on R1, R2 and R4, each with n ≥ 3.
- **The walk question** rests on R5 and R6 (n = 4), with R7 and R17 (n = 2) in support.
- **The opener rule** rests on R9 (n = 4) and R10 (n = 3).

## 4. Alternatives considered

- **A, the current spec** (renderer seam, re-render walk, env copy): superseded.
  It works today on every plugin tested, but read literally it has three problems:
  - it backs off on some gfm bare URLs and on mkdocs attr lists (R6);
  - it silently corrupts later paragraphs given in-place env state, a mechanism shown with a constructed co-plugin (R7);
  - it costs 2.5 to 3 times the recorder (R17).
- **B** (postprocessor plus walk): fails after gfm, after mkdocs, and on #3 with no co-plugin. Its patches need per-co-plugin undo logic for `xxxx` and U+E000 fillers.
- **C** (postprocessor plus text atoms): fails with mkdocs first (R1) and with gfm first on a rule-bearing first word (R2).
- **C′** (renderer plus text atoms): the fallback if constructing a derived `RenderContext` were rejected.
  It matches the tree on core syntax, but it is wrong on shortcut references (`[fig.]`) and on plugin atoms (`[[Page.]]` gains a wrong break). Under C′ the recorder would stay as a CI oracle.
- **E** (a postprocessor moved to the front of `parser_extension` by `update_mdit`): order-safe in sonnet-max's 680 jobs.
  But it mutates a list mdformat is building, cannot record, and needs text atoms. It is unnecessary while the `inline` slot is free.
- **D2** (a `paragraph` renderer chaining over the `inline` owner): composes with an `inline` owner, but not with a `paragraph` owner (hatena, sentencebreak) (R15). Contingency only (§8).
  The dry-run verify-and-veto (R18) runs from the `inline` slot, so it is no argument for D2.
- **Rejected idea:** forcing `wrap="no"` inside the paragraph subtree. It corrupts gfm task items by desynchronizing gfm's `xxxx` prefix-and-strip pair (sonnet-max F8).

## 5. What it costs

- **K1. One `inline` renderer slot.**
  No known plugin wants it (R14).
  If one appears and loads first, this plugin goes inert behind mdformat's "Plugin conflict" warning, and which plugin wins follows load order (R3).
  The canary (S4) reports it, and D2 is the contingency.
- **K2. A convention, not a contract.**
  A-rec relies on two facts:
  - `RenderTreeNode.render` consults `context.postprocessors.get(type, ())` after the renderer;
  - `RenderContext` has a field named `postprocessors`.

  Read, not executed: those, the default `inline` renderer as a plain join, the `used_refs` reset and the first-plugin-wins rule are identical in the wheels of mdformat 0.7.17, 0.7.22 and 1.0.0.
  The behaviour was executed on 1.0.0 only, on Python 3.10 to 3.13, and 1.0.0 is the newest release (R19, R20).
  Both failure modes are loud in §6.2 and in the job against the newest mdformat:
  - if upstream stops consulting the map, every top-level child is unrecorded and C7 backs off every paragraph;
  - if upstream renames the field, `_replace` raises `ValueError`.

  The re-render walk's equivalent drift was quiet (R7).
- **K3. Missed breaks** where a co-plugin renderer bypasses `child.render` or builds its own context (C3), and before unknown atoms (C4).
  A C3 atom also hides its brackets from pairing, as every atom does, so a prose bracket whose partner lies inside one is left unpaired.
  *Reasoned:* that could let a gap break where the walk would have held it. No real case was constructed: gfm trims an unbalanced trailing `)`, and the URLs tried keep their brackets balanced inside the atom.
- **K4. A known incompatibility (R12).**
  Later postprocessors receive text with no `WRAP_POINT`, the shape they see under `--wrap keep`.
  A co-plugin that is wrong at `--wrap keep` is wrong here, as mdformat-mkdocs 5.3.0's spaced-URL fixer is.
  Who sees what:
  - mkdocs alone: the CLI refuses the file at `--wrap keep` and formats it at `no` and `40`;
  - with this plugin loaded, in either order: the CLI refuses it at `no` and `40`;
  - the API returns the changed text without complaint.

  No placement avoids both R12 and R1.
- **K5. Decisions are made on mdformat's own text**, before co-plugins' `inline` postprocessors.
  A co-plugin that rewrote sentence punctuation there (`...` to `…`) would not be seen; none of the tested ones does.
- **K6. Locating children by find is measured, not proven:** 846 of 846 containers were unambiguous. An ambiguous find means an atom (C3).
- **K7. C4 and C6 overlap on definition-shaped text** such as `[^x]:`, and either one alone prevents the damage. So the gate runs that fixture with each guard turned off in turn, or deleting one guard would leave the gate green.

## 6. What the spec must say

- **S1. §2, module surface and version bound.**
  - The module defines `RENDERERS = {"inline": …}` and, under S4, `POSTPROCESSORS = {"root": …}`.
  - "this plugin defines no postprocessor" becomes "it defines one, the `root` canary"; mdformat reads `POSTPROCESSORS` through `getattr`.
  - The list of unpromised facts behind the `<1.1` bound gains K2's two facts.
  - It also gains the canary's three reads: a flag in `context.env`, `context.do_wrap`, and `context.options["parser_extension"]` for the owner's name. Each read degrades to silence or a nameless message rather than raising.
- **S2. §2.2.**
  - Keep the seam and "Why a renderer".
  - **Rewrite** lines 119 to 120. They explain the `- [ ] Do the first thing…` example by "§3.1's walk does not add up, and §3.6 backs off", which is false once there is no walk.
    The replacement explains the failure by `xxxx` glued to the first word (`- [ ] Mr. Smith left early. Then he came back.`, R2) and puts mkdocs's fillers beside it (R1), both failing §1 by load order alone, with or without a walk.
    sonnet-max's `board/03-sonnet-max.md` §3 E2 has literal text.
  - Replace "The renderer is also what makes §3.1's walk pure, because it runs before the children render and can copy the state they change" with: the renderer hands mdformat a context that records each node's rendering, so nothing is rendered twice.
  - Qualify "composes with them without depending on that order" with K4 and K5.
  - The cost paragraph gains R14, R3's conflict winner, the canary (S4) and D2 as the contingency.
- **S3. §2.2 line 114 and §3.1.**
  - Line 114: "returned unchanged before any segmentation or walk of the node" becomes "…before any segmentation or location of records", plus C2's last bullet (no recorder under `--wrap keep`).
  - "The node is read once, for type and nothing else" and "The walk renders against a copy of the state…" become one paragraph stating C2 and C3: the recorder, the top-level invariant, locating a container's children exactly once, and otherwise an atom.
  - Delete the env copy, the per-container throwaway copy and the co-plugin env-state caveat. Its claim that §6.2's back-off row would show such a failure is wrong (R7).
  - The pseudocode `atoms = walk(node)` (line 247) and "the walk's offsets" (line 260) are renamed to the records.
  - `It cites \[foo\] early. Then [a link][foo] later.` stops being called "a valid paragraph": plain mdformat corrupts it (R8). It stays a harness fixture under the relative oracle.
- **S4. §2.2 or §2.5, recommended: the canary.**
  - A `root` postprocessor logs once per pass (twice per `mdformat.text()`) when paragraphs rendered but this plugin's renderer never ran, naming the plugin that owns `inline`.
  - It stays silent when `context.do_wrap` is false, because the plugin is inert under `--wrap keep` by design.
  - A flag the renderer sets in `context.env` makes the normal case cost nothing (R16).
- **S5. §3.2 and the line-396 passage.**
  - Lines 295 and 297: "the walk" becomes the records, and line 297's containers gain "unless C3 makes it an atom".
  - The atom definition gains C3's kind: a node whose children were not rendered, or cannot be located exactly once in its rendering.
  - "A terminator inside an atom never ends a sentence" is tested at the terminator's position, after the footnote strip and the closer skip (C5).
  - Line 396's "a segment ending inside an atom ends no sentence" keeps its verdict for `held.<sup>1</sup>` but changes its reason: the closer scan stops at `>`, which is not a closer.
- **S6. §3.3.**
  - The opaque-atom bullet opens with: "Only a code span, an image, an autolink or raw inline HTML opens a sentence. A leaf of a type this plugin does not know, or a node whose children were not rendered or cannot be located, is an atom for §3.2 but opens nothing."
  - That sentence includes "not read through the capital test" (C4, strict).
  - "any sentence opening with an image or a URL" becomes "an image or an autolink".
  - The footnote strip is stated to precede the atom test.
- **S7. §3.5.**
  - Add C6 with the tested pattern `\\?\*?\\?\[[^\]\n]*?\\?\]:|\\?\([^\s)]+\)=`, read against the line the newline would open: the rest of the section, with gaps as spaces, in mdformat's escaped text.
  - Name the co-plugin each entry is for: footnote and mkdocs definitions, the myst target.
  - The `(label)=` entry matches a line that *begins* with it, so `Sentence one. (Label)= Then more.` is vetoed although myst would not read a target there. That is deliberate: it costs a missed break, never a wrong one, and 0 real documents changed (R13).
  - Say that the list is closed over the co-plugins the gate loads, and that the source-equality row is the only detector for the rest, because `(Label)=`'s escape is render-equal.
- **S8. §3.6.** C7.
- **S9. §6.2.**
  - Every row runs with gfm, and with mkdocs (including a list item longer than the width), each loaded before and after the plugin, plus mdformat-footnote.
  - The back-off row stays at 0, and its justification reads "container fallbacks and the tripwire".
  - New rows:

    | row | requirement |
    | --- | --- |
    | container fallbacks | C3 atoms occur only for named node types (`gfm_autolink`, the mkdocs attr list); any other fails |
    | positive controls | each S10 fixture that exists for a rule fails when that rule is disabled |
    | overlapping guards | the `[^x]:` fixture runs with C4 off, C6 off, and both off; it fails only with both off (K7) |

  - The source-equality oracle may be implemented as the dry run of R18, compared against the all-pinned text (§8, F1).
- **S10. §6.4 fixtures, executable.**
  The property codes are:
  - **W**: width-independent at no, 20, 40 and 80, in both load orders;
  - **R**: render-equal to the co-plugins alone;
  - **S**: source-equal once the added breaks are undone;
  - **B**: no back-off.

  The expected results are A-rec's, from R21 and sonnet-max's re-run against revision 1.
  `work/sonnet-max/r2_gate_fixtures.py` is a working draft of the harness.

  | fixture | co-plugin | checks | A-rec |
  | --- | --- | --- | --- |
  | `Read https://en.wikipedia.org/wiki/Foo_(bar) first. Then go.`, and the same with `__` and with `*` in the URL | gfm | B, and breaks | pass |
  | a `{…}` attr list in a paragraph with sentence ends | mkdocs | B | pass |
  | `- [ ] Mr. Smith left early. Then he came back.` at `--wrap 40` | gfm, both orders | W | pass |
  | a nested list item longer than the width, at `--wrap 20` and `40` | mkdocs, both orders | W | pass |
  | `The matter at hand.[^1] This is next.` | footnote | breaks after `[^1]` (C5) | pass |
  | `Sentence one. [^x]: not a definition, just text.` plus a real `[^x]:` | footnote | R, with C4 off, C6 off and both off | pass; fails only with both off |
  | `Sentence one. *[HTML]: Hyper Text Markup Language is the term.` and `Sentence one. *[Hyper Text]: is a phrase defined here.` | mkdocs | R, S | pass |
  | `It ended. (Label)=`, with the label alone on the line | myst | S | pass |
  | `Read the docs. [[Page]] has them. Then more.` | wikilink | no break before `[[Page]]` (C4 strict) | pass when C4 is read strictly (sonnet-max T18, opus-xhigh `r4_c4_fixture.py`); a kernel that reads the atom's text through the capital test fails it |
  | `It is done. [X] marks a finished task.` | gfm | S | pass |
  | `Hear from us in 60 days. 1. Tell us your name. 2. Describe the error.` | none | S; `1.` and `2.` end lines | pass |
  | `Do not use it. <div> is a block element.` | none | S | pass |
  | `It cites \[foo\] early. Then [a link][foo] later.` with `[foo]` defined | none | B, under the relative oracle | pass |
  | `The term \[x\](see the y note) is escaped. Then more.` | mkdocs | R, S | **known failure (K4)**; recorded, not gating |

- **S11. `notes/`, after the decision.**
  - The `seam.py` row of `notes/README.md` gains the mkdocs finding.
  - `notes/experiments/` gains a mkdocs reproduction (in the manner of sonnet-max's `seam_mkdocs.py`) and a recorder reference.

## 7. Considered and deferred

- **A `gfm_autolink` opener exception** (opus-xhigh, withdrawn).
  *Reasoned:* it is safe, because a gfm autolink begins with `www.`, a scheme or an email local part, none of which is block syntax when followed by a non-space character.
  It was deferred because its measured value is 24 gaps in about 150k paragraphs (R10), and it would be co-plugin knowledge in the spec.
  It is a one-line addition if users report misses.

## 8. Future work

- **F1. Verify-and-veto by a dry run of the paragraph pipeline.**
  - Two prototypes, sonnet-high's `verify.py` and sonnet-max's, show that it works from the `inline` slot for render-level hazards (R18).
  - Compared against a dry run of the all-pinned text, it reproduces the closed list exactly (n = 1, at scale under gfm and mkdocs).
  - Compared against the decided text, it misfires under mkdocs (R22, n = 2).
  - Parse-level traps (`[^x]:`, `*[HTML]:`) are not rewritten by `paragraph()` and stay on the S7 list.
  - It runs co-plugins' paragraph hooks once more per paragraph with a break, which was untested against hatena and sentencebreak.
  - It is not adopted in this revision; §6.2's source-equality row may use it as its oracle.
- **F2.** The `gfm_autolink` opener of §7.
- **F3.** D2, if an `inline` renderer owner ever appears.

## 9. Known incompatibilities and out-of-scope notes

- **K4's** mkdocs spaced-URL case.
- **mdformat-space-control** replaces `softbreak` with a literal space, so with it loaded an authored line break never reaches the plugin as a gap. This is seam-neutral (sonnet-max T10, reasoned from its source).
- **mdformat-sentencebreak and mdformat-slw** are not mentioned anywhere in DESIGN.md, which compares itself with mdformat-sembr (§2.2, §3.3), rumdl (§6.3), flowmark and Panache.

## 10. Not measured

- Windows and macOS.
- mdformat other than 1.0.0. 0.7.17 and 0.7.22 were read, not run.
- Plugin versions other than the latest (R20).
- The 24 extra PyPI plugin sources were read statically and never loaded. The static state census (R7) covers direct writes only; an aliased `env`, or a field of a module-level object, would be missed.
- R7 shows a mechanism with a constructed co-plugin, not an observed failure.
- The full §3.3 rules: every engine here is a stand-in, and none has the rules table, quote roles or camelCase.
- Prose other than mostly English technical writing.
- The hostile fuzz corpora are of the panel's own design.
- The dry run against `paragraph` owners.
- Coverage of sonnet-high's large corpora:
  - they ran the five variants under gfm and under mkdocs;
  - footnote, wikilink and dollarmath were loaded together in one corpus run only;
  - myst and obsidian were run for atom comparison, not for the line-start rows.

## 11. Process record

- Phase 1 was independent; all four members reached A-rec separately.
- Round 01 elected opus-xhigh as facilitator (2 of 4 nominations) and closed the opener dispute (C4) with four independent runs of R9.
- Round 02 posted the draft, and every member accepted it with line edits.
- Round 03 and `signoff-sonnet-max.md` supplied further line edits and re-runs, folded into this revision 2 (`board/04-opus-xhigh.md`).
- No dissent was recorded.
