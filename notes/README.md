# Notes

Working material behind `DESIGN.md`. Nothing here is normative.

`DESIGN.md` is the specification and stands alone; these are the corpus and the
throwaway programs that produced the numbers quoted in it, kept so that anyone
can re-run them rather than take them on trust.

| | |
| --- | --- |
| `PRESERVE-MODE.md` | Why the plugin does not try to preserve an author's existing line breaks. The longest-running open question about this design, answered. |
| `MDFORMAT-WRAP-AND-OVERRIDES.md` | Where mdformat reads `wrap`, what a plugin can see and override about it, and what `--wrap sentence` would cost upstream. A reference for whoever later decides whether to patch, to ask, or how to implement §2.5's warning. |
| `QUOTE-ROLES.md` | Which quotation marks always open or always close, in any language. Only the CJK marks do, which is why §3.3 reads them and the guillemets by glyph and every other lone mark by what precedes it. |
| `corpus/` | The one corpus that gives honest answers about layout heuristics, and why. |
| `experiments/` | Twenty-three short programs. Twelve need mdformat or its parser, and eleven are stdlib only; three need the network, and one needs seven documentation repositories cloned. |

## Running them

```
python3 -m venv v && ./v/bin/pip install 'mdformat==1.0.0'
./v/bin/python notes/experiments/probe.py
```

`seam.py` also needs `mdformat-gfm==1.0.0`.

Pin mdformat to 1.0.0. Every seam fact in `DESIGN.md` §2 was measured against
that version, and the wrap-point mechanics these programs depend on are internal
to it.

| program | needs mdformat | what it establishes |
| --- | --- | --- |
| `probe.py` | yes | What reaches the `POSTPROCESSORS["inline"]` seam under each `--wrap` mode. Zero wrap points under `keep`, 44 under `no` and under an integer width. |
| `handwritten.py` | yes | `--wrap no` collapses a hand-broken paragraph to one line before any plugin sees it. The basis of `DESIGN.md` §2.5's warning. |
| `addonly.py` | yes | The author's line breaks survive to the seam as `softbreak` children on pass 1 and are gone on pass 2. |
| `proto.py` | yes | A working add-only postprocessor. Idempotent, width-independent, and not a pure function of the text. |
| `proto2.py` | yes | The same harness with a pluggable decision function. The shape every later experiment varies. |
| `breaks.py` | no | **45% of real sembr line breaks carry no punctuation at all.** A break-word list recovers 12 of the 32 that are not at markup either; 23% of all breaks stay undetectable. The reason rule 5 cannot be recovered from layout. |
| `triage2.py` | no | Sentence coverage separates hand sembr from geometric wrapping almost perfectly on this corpus: all 9 real paragraphs score 1.00 and 24 of the 27 hard-wrapped ones score 0.00, the exceptions being two at 0.50 and one at 1.00. It prints the full distribution, because min/median/max hides exactly the middle that decides this. |
| `cov.py` | no | What "coverage" means, on worked cases, including a width-wrapped paragraph that scores 1.00 by coincidence. |
| `thresh.py` | no | Any coverage *threshold* reintroduces paragraph-sized diffs: one edit, 18 changed lines. |
| `k0.py` | no | At a threshold of exactly zero, appending a sentence is safe (1 diff line) but removing a sentence break is not (8 lines, all clause breaks lost). |
| `edit.py` | no | Rewrapping a paragraph versus adding only the missing break: 9 diff lines against 1, 0 clause breaks surviving against 4. |
| `rules.py` | no | Every author break in the corpus by which sembr rule put it there: 12% rule 4, 42% rule 5, 9% rules 10 and 11, 36% rule 6. The table in `DESIGN.md` §5.2. |
| `wrapkeep.py` | yes | Whether a plugin can defeat `--wrap keep`. It can, in two lines, through a supported hook, and the script lists the three consequences that are why `DESIGN.md` does not. Also: what the plugin can and cannot see about `wrap`, which is what §2.5's warning keys off. |
| `secondpass.py` | yes | A `POSTPROCESSORS["root"]` hook can re-render, restoring mdformat's second pass when it would otherwise be skipped. Output matches the honest `--wrap no` exactly, over a bare paragraph and over lists, blockquotes and fenced code, once the already-finalized trailing newline is handled. |
| `wrapsplit.py` | yes | Simulates splitting `do_wrap` into "produce wrap points" and "width-wrap". Under `--wrap keep` the plugin works, mdformat adds no geometric wrapping, and links survive as atoms. The feasibility check behind §5.6 of the wrap note. |
| `wraparg.py` | yes | `wrap` as an *argument* rather than at the seam. The CLI and TOML validators are separate code and disagree; `--wrap sentence` is rejected at argument parsing today; and a renderer warning reaches stderr through `logging.lastResort` even with no handler attached, once per paragraph. |
| `sourceeq.py` | yes | §6.2's source-equality row, run with a postprocessor that has no line-start rule. Ten container cases pass, nested and numbered lists among them; the HTML indent and the escape before `-` fail, and render equality passes all three. Stripping every leading `>` and whitespace instead of the containers' own prefix passes the HTML indent. |
| `seam.py` | yes, and mdformat-gfm | Why the plugin is an `inline` renderer and not an `inline` postprocessor. Postprocessors run in load order, which under the API varies with `PYTHONHASHSEED`; with gfm first, a postprocessor backs off on a task-list item at `--wrap 40` and not at `--wrap no`, and a renderer backs off in no order. Re-rendering against the live state gives 49 characters where the real render gave 47, and a copy taken before the children render makes them equal. gfm escapes a task box at the start of a line a break created, in either order. |
| `ngram.py` | no (network) | For each abbreviation, the share of its top Google Books continuations that are numerals. `et al` 100%, `Vol` 100%, `Fig` 97%, `No`/`no` 0%. The evidence behind §3.3's abbreviation classes. Needs outbound HTTPS. |
| `lonemark.py` | no | §3.3's lone-mark rules, simulated. Nineteen fixtures hold, two of them runs that §3.5 pins because the newline would land where a line cannot safely start or end, and a mark's role moves only the mark, alone or side by side: 120 readings of twenty-two texts. |
| `camelcase.py` | parser | Sentence openers in 13.0 million words of English documentation: 113 camelCase words such as `iOS`, all but two real sentence starts and those two already held by brackets, and about thirty lowercase names such as `npm`. `camelcase.tsv` holds each camelCase position with its verdict. Needs the corpora its docstring names. |
| `cldrquotes.py` | no (network) | Each quotation mark's roles across CLDR 48.2's 766 locales. Only the corner brackets and the low marks `„` `‚` have one role there, and `《` `》` `〈` `〉` `‟` `‛` have none. Needs outbound HTTPS. |
| `lic.py` | no (network) | Every plugin in mdformat's curated list is MIT, and so is mdformat. Needs outbound HTTPS; a package it cannot fetch is reported as not clearly MIT rather than skipped. |

The programs are throwaway quality on purpose. They exist to produce a number
once, not to become a test suite. `DESIGN.md` §6 specifies the real gate.
