# Trade-offs: costs the design accepts

A note, not a specification.
Each entry names a cost `DESIGN.md` takes on deliberately, what it buys, and where the spec states it.
Work postponed rather than costs accepted is in `FUTURE-WORK.md`.

Most of these costs are missed breaks: a long line where the plugin cannot be sure, which reads as prose, rather than a wrong break, which reads as a mistake.
The entries that are not missed breaks say so.

______________________________________________________________________

## The hook point and the recorder (§2.2, §3.1, §3.6)

| cost | what it buys | kind |
| --- | --- | --- |
| The plugin owns `RENDERERS["inline"]`, which only one plugin can own. If another loads first, this plugin goes inert behind mdformat's "Plugin conflict" warning, and which wins follows load order. | Decisions on mdformat's own text, whatever co-plugins are installed. | inert, with a warning and the canary |
| The recorder rides on a convention, not a contract: `RenderTreeNode.render` consults `context.postprocessors.get(type, ())`, and `RenderContext` has a `postprocessors` field. | One render instead of two, no copied state. If upstream drops the convention, every paragraph backs off and the gate fails; if it renames the field, `_replace` raises. | loud failure on drift |
| A node whose children were not rendered, or cannot be located exactly once, is an atom. | No back-off on gfm bare URLs or mkdocs attribute lists. | missed breaks |
| An atom hides its brackets from pairing, so a prose bracket whose partner lies inside one is left unpaired. Reasoned only; no real case was found. | The same atom rule everywhere. | possibly a wrong break |
| Locating a container's children by finding their joined records is measured, not proven: 846 of 846 containers were unambiguous in the hook-point review. | No re-render. An ambiguous find makes an atom. | missed breaks |
| Later postprocessors receive text with no wrap point, the shape they see under `--wrap keep`. mdformat-mkdocs 5.3.0's spaced-URL fixer is wrong at `--wrap keep`, so with this plugin loaded it misfires at `--wrap no` too: `The term \[x\](see the y note) is escaped.` becomes a link. The CLI refuses the file; the API changes the render without complaint. No hook placement avoids both this and the load-order failure. | Width independence under every load order. | a known incompatibility, see `quirks-mdformat-mkdocs.md` |
| A co-plugin that rewrote sentence punctuation in its own `inline` postprocessor would not be seen. None tested does. | The same. | unseen input |
| A `root` postprocessor, the canary, is part of the module surface. | A lost `inline` slot is reported rather than silent. | surface |

## Detection (§3.2, §3.3, §3.5)

| cost | what it buys | kind |
| --- | --- | --- |
| Only a code span, an image, an autolink or a tag-only raw HTML segment opens a sentence regardless of case. A sentence opening with inline math or a wikilink, `…holds. $x$ is positive.`, is not broken. Measured at no lines on technical documentation; math-heavy prose was not measured. | An open list let mdformat-footnote delete text. | missed breaks, see `MATH-AND-OPENERS.md` |
| Co-plugin definition syntax at a line start, `[label]:`, `*[label]:`, `(label)=`, is a closed list over the co-plugins the gate loads. `(label)=` is held wherever it begins a line, even where myst would not read a target. | No definitions created by a break. | missed breaks; an unlisted plugin's syntax is unguarded |
| A task box `[ ]`, `[x]` or `[X]` is refused at a line start even without gfm loaded. | No check that depends on what else is installed. | missed breaks |
| A run of lone marks whose newline would land on an unsafe position is pinned whole. | No mark stranded where a line cannot start or end. | missed breaks |
| Dotted initialisms of one or two letters per piece join the next sentence when they end one: `in the U.S. The next day`, `at 5 p.m. Then`, and a short bare filename, `x.py.` A longer piece, `M.Phil.`, is not covered and breaks. | `Node.js`, `github.com` and longer filenames break where they end a sentence. | missed breaks, and rarely a wrong one |
| Titles match only with a capital first letter: all-caps `MR. SMITH` breaks after the title. | `5 ms.` breaks. | a wrong break in all-caps prose |
| The pronoun `I.` joins the next sentence, `So did I. Then we left.` | `I. M. Pei` holds together. | missed breaks |
| Brackets pair per kind; an unclosed opener can be adopted by a later closer across a sentence end, `It failed :(. Then came a) and b).` | An unclosed `:(` or `1(a` no longer silences the rest of the paragraph. | a missed break |
| A Greek question, ending in `;`, never ends a sentence. | The terminators stay a Unicode property, and English semicolons never break. | missed breaks |
| A citation marker after the period, `held.[1] Then` or `held.<sup>1</sup> Then`, ends no sentence. | The footnote strip stays exact. | missed breaks |
| A sentence opening with a symbol or a dialogue dash, `$HOME is set.`, `— Oui.`, is not broken. | The capital test stays one rule. | missed breaks |

## Configuration (§4)

| cost | what it buys | kind |
| --- | --- | --- |
| `include` takes names only, so the projects of a monorepo cannot share one set by path. | One resolution rule, and sets that travel together. | duplication |
| `--sentence-include` is hidden and unstable. | No published promise while its design settles. | no supported flag for ad hoc sets |
| `base_rules` is boolean only, and `default` cannot be named in `include`. | One switch for the shipped rules, and room for later values. | none in practice |
| The dependency is pinned to `mdformat>=1.0.0,<1.1`. | No silent output change from an mdformat release. | users wait for the bound to move |

## The gate (§6)

| cost | what it buys | kind |
| --- | --- | --- |
| Every row runs with mdformat-gfm, mdformat-mkdocs and mdformat-footnote, each before and after the plugin. That multiplies CI time, mkdocs brings dependencies of its own, and a co-plugin that declares an incompatible mdformat range, as mdformat-dollarmath 0.0.5 does, must be installed without dependency checks. | The gate sees the load-order and definition-syntax failures that a plugin-alone gate cannot. | CI time and setup friction |
| A fixture whose damage two guards each prevent runs with each guard off in turn. | Deleting one guard does not leave the gate green. | more runs |
