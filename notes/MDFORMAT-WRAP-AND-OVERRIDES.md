# mdformat's wrap arguments, its plugin interface, and what a plugin can override

A reference, not a decision, and not a specification.
`DESIGN.md` is normative; nothing here amends it, and where the two disagree this note's section 9 says so rather than settling it.

It exists for three questions that are still open and will be asked later: whether to patch mdformat, whether to file an upstream request for a wrap mode, and how to implement the warning `DESIGN.md` section 2.5 specifies.
It answers what mdformat does and what a plugin is able to reach, and stops there.

Everything below was measured by execution against mdformat 1.0.0 unless it is marked **Reasoned**, which marks argument rather than measurement.
Every `file:line` was re-read against `v/lib/python3.11/site-packages/mdformat/` on 2026-09-17; paths below are relative to that directory.
Some citations moved from the ones in earlier notes, so re-read rather than trust these too.

| program | what it establishes |
| --- | --- |
| `experiments/wrapkeep.py` | What a plugin can and cannot see about `wrap`, and the three routes to overriding it. Sections 2 and 3. |
| `experiments/secondpass.py` | That a `POSTPROCESSORS["root"]` re-render restores mdformat's second pass, over a bare paragraph and over a document with a list, a blockquote and a fenced block. Section 4. |
| `experiments/wraparg.py` | `wrap` as an *argument*: the two validators, `--wrap sentence` today, and where a renderer warning actually goes. Sections 5 and 7. |

All three need mdformat 1.0.0.
`experiments/probe.py` is the prior measurement of what reaches the hook point under each mode, and section 1 does not repeat it.

______________________________________________________________________

## 1. Where the wrap value is read

It is read in several places, and no two of them agree on how to read it.

**The default.** `DEFAULT_OPTS` in `_conf.py:11-22` is a `MappingProxyType`, and `wrap` is `"keep"` at `_conf.py:13`.

**CLI validation.** `validate_wrap_arg` at `_cli.py:189-195` returns `"keep"` or `"no"` unchanged, otherwise calls `int(value)` and rejects anything below 1.
It is wired as argparse's `type=` at `_cli.py:233-238`, so a bad value is a parse error and never reaches a file.

**TOML validation.** `_validate_values` at `_conf.py:56-63` is a second, independent gate: `wrap` must be an `int` **greater than 1**, or `"keep"`, or `"no"`.
`_validate_keys` at `_conf.py:99-105` separately rejects any key not in `DEFAULT_OPTS`.

The two gates disagree on `1`: `--wrap 1` is accepted, `wrap = 1` in `.mdformat.toml` raises `InvalidConfError`.
Measured, `wraparg.py` check 1.
It is a pre-existing inconsistency and harmless here; it is recorded only because it shows the two are separate code paths, which section 5 depends on.

**The renderer's predicate.** `RenderContext.do_wrap` at `renderer/_context.py:641-644`:

```python
wrap_mode = self.options.get("mdformat", {}).get("wrap", DEFAULT_OPTS["wrap"])
return isinstance(wrap_mode, int) or wrap_mode == "no"
```

Note the two `.get()`s with defaults.
This is what makes `do_wrap` safe to evaluate when the key is absent, which section 2 shows can happen.

**The renderer's use of the value.** `paragraph` at `renderer/_context.py:390-406` reads `context.options["mdformat"]["wrap"]` at line 395 with a bare subscript and no default, guarded only by `if context.do_wrap` on line 394.
An `int` is reduced by `context.env["indent_width"]` and floored at 1, then the value goes to `_wrap` as `width`.
`_wrap` at `renderer/_context.py:348-362` has an explicit `if width == "no"` branch that returns after `_prepare_wrap`, and otherwise hands the value to `cached_textwrapper` (`renderer/_context.py:337-345`) as a `textwrap.TextWrapper` width.

So `do_wrap` decides *whether*, and the same option decides *what*, and they are read independently.
Section 3.2 is what that costs.

The observable behavior of the three modes is `DESIGN.md` section 2.5's table and is not repeated here.

______________________________________________________________________

## 2. What a plugin can see about `wrap`

Measured, `wrapkeep.py`, from an inline postprocessor reading `context.options["mdformat"]`.

| how mdformat was invoked | `"wrap"` in `options["mdformat"]` | value |
| --- | --- | --- |
| `mdformat.text(src)` | **absent** | none |
| `mdformat.text(src, options={"wrap": "keep"})` | present | `"keep"` |
| CLI, no `--wrap` | present | `"keep"` |
| CLI, `--wrap keep` | present | `"keep"` |
| `wrap = "keep"` in `.mdformat.toml` | present | `"keep"` |

The API row is absent because `build_mdit` at `_util.py:32-42` assigns the caller's mapping verbatim at line 33, `mdit.options["mdformat"] = mdformat_opts`, with no defaults merged into it.
The three CLI rows are identical because `_cli.py:56` builds `{**DEFAULT_OPTS, **toml_opts, **cli_core_opts}` and `_cli.py:32-34` drops every argparse value that is `None`, so an unset `--wrap` contributes nothing to the merge.

**A plugin can therefore distinguish an explicit `keep` from a defaulted one through the Python API and cannot through the CLI.**
CI runs the CLI.

`extensions` is a usable signal **on the CLI and TOML paths only**, because `DEFAULT_OPTS["extensions"]` is `None` (`_conf.py:19`) and `_cli.py:82-88` only replaces the full plugin mapping when it is not `None`.
A non-`None` `options["mdformat"]["extensions"]` therefore means someone typed the flag or wrote the TOML key.
That is the condition `DESIGN.md` section 2.5's warning keys off, and it is the reason it keys off `--extensions` rather than off `wrap`.

**It is not a signal on the Python API path at all**, and an earlier draft of this note and of `wrapkeep.py` said it was.
`mdformat.text(src, extensions={"probe"})` passes the set as its own argument to `build_mdit` (`_util.py:32-42`); it never reaches `options["mdformat"]`, so the key is absent and `.get("extensions")` is `None`.
Measured, `wrapkeep.py`: `'<absent>'` on both API rows, `['probe']` on the CLI row.
The consequence for `DESIGN.md` section 2.5 is that its warning can never fire for a library caller, whichever wrap mode they chose, so `DESIGN.md` section 2.5's account of where a library caller's warning lands describes an unreachable case.

______________________________________________________________________

## 3. Overriding `wrap` from a plugin

The question this section answers is narrow: *can* a plugin make itself work under `--wrap keep`, where `DESIGN.md` section 2.5's table says it is inert.
It can.
`DESIGN.md` declines to, and this note's section 3.1 shows why.

### 3.1 Route B: assign the option in `update_mdit`

Two lines, through a published hook:

```python
def update_mdit(mdit):
    mdit.options["mdformat"]["wrap"] = "no"
```

Measured, `wrapkeep.py`.
Under a caller who asked for `keep`, the baseline sees zero wrap points and returns the input byte for byte; with the assignment, 17 wrap points reach the hook point and the paragraph comes out on two lines.
It works because `build_mdit` calls `plugin.update_mdit(mdit)` at `_util.py:42`, after `mdit.options["mdformat"]` has been assigned at line 33 and before anything renders.

The consequences, all measured or read:

1. **The second pass does not fire.**
   `_api.py:39` tests `options.get("wrap", DEFAULT_OPTS["wrap"]) != "keep"` against the **caller's** mapping, which still says `keep`, so the re-render at `_api.py:40` is skipped.
   Calls at the hook point stay at 1 where an ordinary `--wrap no` gives 2.
   That is the pass `DESIGN.md` section 2.3 relies on.
1. **The option is global to the render.**
   There is one `mdit.options["mdformat"]` and every enabled plugin reads it, so they all see `wrap="no"` too.
1. **It silently overrides an explicit instruction.**
   A user who typed `--wrap keep` gets wrapping, and `--check` then reports the file unformatted to someone who asked for none.

### 3.2 Route C: patch the renderer

Patching `RenderContext.do_wrap` to a property returning `True` and leaving the option alone raises:

```
TypeError: '<=' not supported between instances of 'str' and 'int'
```

Measured, `wrapkeep.py`.
The cause is section 1's split: `do_wrap` now says yes, `paragraph` at `renderer/_context.py:395` still reads `"keep"`, and `textwrap` is handed the string as a width.
Both have to be patched together, which means patching `paragraph` as well.

`DEFAULT_RENDERERS` is a `mappingproxy`, so it cannot be assigned into from outside.
The supported way to replace a renderer is a plugin's own `RENDERERS` mapping, which `render_tree` merges at `renderer/__init__.py:89`.
That is the `paragraph` renderer hook `DESIGN.md` section 2.2 rejects on unrelated grounds, so route C is already ruled out.

______________________________________________________________________

## 4. Restoring the second pass from a root postprocessor

If route B were ever taken, the pass it skips can be put back.
Measured, `secondpass.py`.

Of the four node types tried, `root`, `document`, `inline` and `paragraph`, three fire and `document` does not.
`root` is the whole rendered document, applied by `RenderTreeNode.render` at `renderer/_tree.py:9-14` like any other postprocessor.

A guarded re-render from `POSTPROCESSORS["root"]` takes calls at the hook point from 1 back to 2 and produces output identical to an ordinary `--wrap no`, on a bare paragraph and on a document containing a list, a blockquote and a fenced code block.

Caveats:

- **The trailing newline doubles.**
  A root postprocessor is handed already-finalized output: `render_tree` appends the final `"\n"` at `renderer/__init__.py:94-99`, so re-rendering it finalizes twice.
  `.rstrip("\n")` on the way in and on the way out fixes it; without that the output ends `'.\n\n'` and no longer matches.
- **It needs a re-entrancy guard.**
  The re-render runs the same plugin, including this postprocessor.
  Unguarded, it recurses to `RecursionError`.
- **The second pass has to be given the first pass's whole configuration, and the measurement did not give it one.**
  `secondpass.py` calls `mdformat.text(..., options={"wrap": "keep"}, extensions={"probe"})` with both hardcoded, which silently drops every other enabled plugin, every code formatter and every other option from the pass it is restoring.
  That is harmless in a measurement with one plugin and no options, and it is not harmless in a plugin: a real implementation has only `context.options` to rebuild them from, and `codeformatters` is not in there at all.
  Nothing below about matching an ordinary `--wrap no` transfers past the one-plugin case.

**Limit on the claim.** Route B *alone* already matched an ordinary `--wrap no` byte for byte on both documents tried.
No input has been exhibited here where one pass and two disagree.
The re-render restores the pass, not a known output difference; mdformat runs two because escaping depends on wrapping (`_api.py:35-40`), so this is insurance against that class of case rather than a fix for a measured one.

______________________________________________________________________

## 5. What to ask upstream

### 5.1 The primary defect: `--wrap no` becomes false

Once this plugin is installed, `--wrap no` misdescribes what the tool does.
The user asked for no wrapping and got wrapping: line breaks inserted at computed positions, at sentence boundaries rather than at a column, but inserted all the same.

What makes that more than cosmetic is that `no` is the **only** wrap value whose meaning the plugin redefines.
`--wrap keep` means the same thing with the plugin installed as without it.
`--wrap 80` means the same thing.
`--wrap no` means "one line per paragraph" alone and "one sentence per line" with this plugin present, so the same flag value produces two different documents depending on what is installed, with nothing on the command line to say which one you got.

### 5.2 The second defect: `--wrap no` without the plugin is silent and destructive

Run `--wrap no` on a hand-broken corpus without the plugin installed and mdformat collapses every paragraph to a single line, with no warning.
That is `DESIGN.md` section 2.5's cost, measured in `experiments/handwritten.py`, and it is the failure mode of a CI config that names `--wrap no` on a machine where the plugin did not install.

`--wrap sentence` fails loud instead.
Measured, `wraparg.py` check 2: today it exits 2 at argument parsing with `argument --wrap: invalid validate_wrap_arg value: 'sentence'`, before a file is opened.
An unrecognized wrap mode is rejected; `no` is always recognized, and means something destructive.

### 5.3 The common cause

**Reasoned.** Both defects are the same thing seen from two sides: `no` is being used as a carrier for "let the plugin decide", which is not what it says.
A value that names the behavior rather than negating a different one fixes both, because a name that is wrong when the plugin is absent can be rejected, and a name that is right when it is present does not have to be read as a lie.

Nothing here claims `--wrap sentence` would disambiguate between two break-inserting plugins.
Postprocessors chain (`renderer/__init__.py:84-88`), so two such plugins compose under any wrap value, and how they compose was not measured.

### 5.4 What the change would touch

Mechanically `--wrap sentence` is identical to `--wrap no` plus this plugin, because `no` already means "emit wrap points, do not width-wrap", which is `_wrap`'s early return at `renderer/_context.py:356-357`.
It adds a name and a rejection, not a mechanism.

**Four call sites, not three.**

| site | change |
| --- | --- |
| `_cli.py:189-195`, `validate_wrap_arg` | accept `"sentence"` alongside `"keep"` and `"no"` |
| `_conf.py:56-63`, `_validate_values` | accept it in the TOML gate, which is separate code |
| `renderer/_context.py:641-644`, `do_wrap` | return `True` for it |
| `renderer/_context.py:348-362`, `_wrap` | treat it like `"no"` |

The TOML gate is the one the earlier summary of this work missed.
Measured, `wraparg.py` check 1: `wrap = "sentence"` in `.mdformat.toml` raises `InvalidConfError` today, so changing only the CLI would leave the mode unreachable from a config file, which is how a repo pins its formatter.

`_api.py:39`'s `!= "keep"` already triggers the second pass for any new value, so that site needs nothing.

**No plugin hook reaches any of the four.**
A plugin implementing this would be patching mdformat, not extending it.

### 5.5 A generic form the maintainer is likelier to accept

**Reasoned**, except where marked.

The trouble with asking for `"sentence"` by name is that it makes mdformat learn a concept it has no reason to hold, and it invites an unbounded enum as other plugins want theirs.
Two generic forms avoid both, and neither requires mdformat to know what any mode means.

**Variant B, `--wrap <plugin-id>`.**
Any enabled parser extension's entry-point id becomes a legal wrap value, meaning: `do_wrap` is true, mdformat performs no width wrapping, and the named plugin is the designated line-breaker.
It introduces no new namespace, because that id already names the plugin in `--extensions`, in `[plugin.<id>]` and at the entry point.

The validation this needs is available at the moment it is needed.
`run` at `_cli.py:26-33` passes `mdformat.plugins.PARSER_EXTENSIONS` into `make_arg_parser` *before* calling `parse_args`, so `validate_wrap_arg` can be given the registry to check against.
Measured: with a plugin registered, the mapping reaching `make_arg_parser` already contains its id.

For this plugin the entry-point id is `sentence` (`DESIGN.md` section 2), so variant B yields the exact spelling that this note's section 5 wants, `--wrap sentence`, at no cost in ergonomics.

**Variant C, the plugin declares its modes.**
Add an optional `WRAP_MODES: Iterable[str]` to the `ParserExtensionInterface` Protocol (section 6), and let mdformat accept any value an enabled plugin declared.
This extends the existing extension point rather than overloading the id space, and it allows one plugin to offer more than one mode.
A larger ask than B, and a cleaner shape.

Both still touch the four sites in section 5.4; what changes is that the accepted set is computed rather than hardcoded, which is the part that makes it a mechanism instead of a favor.

**What neither variant provides.**
The flag would *designate* but not *enforce*.
Postprocessors chain (`renderer/__init__.py:84-88`), so a plugin that is not the named one still runs unless plugins cooperate by checking whether they were named.
That makes it a convention, and section 5.3's disclaimer stands unchanged.

**Costs to state in any request.**
Variant B needs `keep` and `no` reserved against a plugin id colliding with them.
Both make a shared `.mdformat.toml` valid on one machine and invalid on another, since the value's legality depends on what is installed, which is arguably correct since the plugin is required, but it is a new failure mode for a checked-in config.

### 5.6 The smaller ask: split wrap-point production from width wrapping

This one does not touch the option space at all, and it is the smallest change that gives the plugin what it needs.

**The conflation.** `do_wrap` is one predicate serving two questions, and `renderer/_context.py` uses it at five places (plus the definition at :641-644) which divide four to one:

| use | job |
| --- | --- |
| `softbreak` :109, `text` :153 | **produce** wrap points |
| `image` :204, `link` :267 | collapse interior wrap points, which only matters once they are produced |
| `paragraph` :394 | **width-wrap**, using the value as a column |

A plugin that converts wrap points to newlines needs the first group and has no opinion about the second.
There is no way to ask for that today except `no`, which to a user without the plugin means "put every paragraph on one line".
So `no` does double duty, and that is the defect underneath sections 5.1 and 5.2 both.

**The ask.** Let a plugin declare that it requires wrap points, through a new Protocol member such as `NEEDS_WRAP_POINTS` or a separately named postprocessor hook, and gate the production group on `do_wrap or any(plugin declared it)` while leaving `paragraph`'s width-wrapping gated on `do_wrap` alone.
Opt-in by declaration, so every existing plugin is unaffected and the default behavior of every existing invocation is unchanged.

**Measured feasible**, `experiments/wrapsplit.py`.
Forcing the production group true while `paragraph` honors the user's real mode, under `--wrap keep`, yields sentence-per-line output with no width wrapping, links surviving as single atoms, and no stray wrap points in the result.

**What it fixes and what it does not.**
It fixes the mechanism: a plugin gets what it needs through a declared, typed, documented channel instead of section 3.1's assignment into someone else's config, and it stops `no` being the only way to spell "produce but do not wrap".
It does not fix the naming.
Under this ask `--wrap keep` still stops keeping when such a plugin is installed, which is section 5.1's complaint relocated rather than answered.

**The two asks compose, and in one direction.**
The split is what makes a named mode cheap: with production and width separately gated, `--wrap sentence` or `--wrap <plugin-id>` becomes "production on, width off, this plugin named", which is a value that selects an existing combination rather than a new code path.
Asked in the other order, the named mode has to carry the split inside it.
**Reasoned.** If only one is filed, the split is the better first ask: smaller, opt-in, invisible to existing users, and it is the one the other depends on.

### 5.7 Prior art

Searched on 2026-09-17, on the mdformat issue tracker, for issues about `--wrap`, wrap modes, and plugins controlling wrapping.
An earlier pass over that search concluded that nothing proposes new wrap modes, plugin-defined wrap modes or semantic line breaks, and that this was greenfield.
**That was wrong.**
The search term was `--wrap`; the prior art is filed under *sentence*, and re-running the search on 2026-09-17 with that word returns four issues:

**None of these four was read past its title and opening comment.**
Everything attributed to them below is from that much and no more, so any later comment, counter-proposal, maintainer decision or linked PR in any of the four threads is unknown to this note.
Read them before acting on this section.

- **#4** `Sentence-based word wrapping`: **open**, opened by hukkin, the maintainer, labeled `Enhancement`, `Plugin`, `Research`. *Opening comment only.*
  It proposes sentence-based wrapping as an optional mode that does not change the default, and reaches for NLTK to segment sentences.
  Whether the NLTK dependency was later argued about, and whether the `Plugin` label reflects a settled position or an initial guess, are exactly the kind of thing the unread remainder would say.
- **#374** `Allow wrapping option of 1 sentence per line`: closed as a **duplicate** of #4. *Title and opening comment only.*
  It asks for `--wrap sentence` as a new enum value, which is section 5.4's ask verbatim.
  Who closed it, and whether anything was said while closing it, is unread.
- **#222** `Support enforcing line breaks after 'end of sentence'`: closed. *Title and opening comment only.*
  It asks for a flag implementing sembr#1 through sembr#4 of the Semantic Line Breaks specification, which is this plugin's scope.
  Why it was closed is unread, and a stated reason there would bear directly on this whole section.
- **#422** `Word-wrap on sentence (punctuation) and width.`: closed. *Title only; not opened at all.*

So there is an existing thread to join and it is the maintainer's own, the `Plugin` label on it is his own triage of where this belongs, and the exact spelling that section 5.4 proposes has already been asked for once and folded into #4.
Nothing found is a *rejection*: #4 is open and #374 was closed only as a duplicate.
What changes is the shape of the ask, a comment on #4 rather than a new issue, and section 5.6's split becomes the part that is new, since no issue proposes separating wrap-point production from width wrapping.
The reading limit stated above applies to every claim in this subsection.

Three further open issues are adjacent and are listed only by title, without characterizing them further:

- **#590** `--wrap can turn a paragraph into a code fence (~~~ reaching line start)`
- **#589** `--wrap silently deletes a non-breaking space at a wrapped line edge`
- **#588** `mdformat --check fails on a file mdformat just formatted (small --wrap)`

The first two correspond to the two upstream defects `DESIGN.md` section 3.5 already works around, the tilde fence and the whitespace deletion.
Who filed them was not checked.

### 5.8 A larger ask: a line-breaking step in `paragraph()`

**Reasoned**, except where marked.

Section 5.6's split gives a plugin wrap points without width wrapping, but the plugin still decides line layout before `paragraph()` runs, and hands it down as `\n` and pinned spaces.
`paragraph()` splits its text on `\n` and fills each line with `_wrap` (`renderer/_context.py:390-406`), and none of section 6's five members can supply that one step.
A plugin can replace the whole `paragraph` renderer, which `DESIGN.md` section 2.2 rejects because mdformat-hatena and mdformat-sentencebreak already own it, or post-process its output, after line-start escaping has run.

**The convention it would retire.**
Deciding layout in the `inline` slot rests on breakable whitespace reaching it as `WRAP_POINT`, which mdformat does not promise.
mdformat-space-control breaks it: its `softbreak` renderer returns a literal space, and with it loaded the plugin adds no break of its own.
Measured, `experiments/spacecontrol.py`; `quirks-mdformat-space-control.md` has the detail.

**The ask.** A step that `paragraph()` calls in place of `_wrap` for each line, supplied by a plugin, so that the plugin decides the breaks while `paragraph()` keeps its line-start escaping and the containers keep their indentation.
Given the inline node as well as the text, the step could treat an authored `softbreak` as a gap whatever a co-plugin rendered it as, since the tree still marks one (`DESIGN.md` section 3.1); that is untried.

**What the step would still lack, and what the ask has to carry.**
A node and a string do not give offsets.
`DESIGN.md` section 3.2's atoms, a link, a code span, a footnote reference, are placed by the recorder of `DESIGN.md` section 3.1, and the recorder works only because the `inline` renderer controls the context its children render through.
A step that `paragraph()` calls after the inline render controls nothing upstream of it, so handed the text alone it would have to render the children again, which `DESIGN.md` section 3.1 rejects as impure, or find atoms in the text, which `DESIGN.md` section 2.2 tried and found wrong on `[fig.]` and on wikilinks.
So the ask has to carry the structure as well as the step: either `paragraph()` records each node's rendering as the inline child renders and passes the span map to the step, or `paragraph()` lets the plugin supply the context its inline child renders through, so that the step records for itself.
The second is not the `inline` slot as it stands.
In that slot the plugin is the renderer, so its recording and its layout decision are one function whose result goes down to `_wrap` as `\n` and pinned spaces, and a second plugin that owns `inline` displaces both; under this ask the plugin owns no renderer, `paragraph()` renders its child through whatever `inline` renderer is loaded, and an `inline` owner no longer displaces the step.
**Reasoned.** It can still starve it: `DESIGN.md` section 3.1's records add up to the text only because mdformat's own `inline` renderer joins its children's renders with nothing between them, so a foreign owner that does not pass the supplied context to its children, or a foreign owner or an `inline` postprocessor that transforms the joined text, as mdformat-mkdocs's postprocessor does with its fillers (`quirks-mdformat-mkdocs.md`), leaves the whole node an atom under section 3.1's rule, and the step keeps its escaping and loses every break in that paragraph.
That last case is not special to the second alternative: `RenderTreeNode.render` runs a node's postprocessors inside its render, so a step that `paragraph()` calls after rendering its inline child runs after every `inline` postprocessor under either alternative, downstream of the load-order seam `DESIGN.md` section 2.2 chose the renderer slot to stay ahead of, and the ask should say whether the step runs before them.
**Reasoned.** The first is the smaller interface, and it is the one under which two plugins' steps would read the same map.

**Measured**, `experiments/parahook.py`, at `--wrap no` on one paragraph with a code span, a link, emphasis and a sentence ending in `1.`, which a break puts at a line start.
A `paragraph` postprocessor receives one line with no wrap point in it, after `_wrap`; when an `inline` decision has put `1.` at a line start, as in the three variants below, it receives `1\.`, so it also runs after line-start escaping.
The `inline` renderer receives the same paragraph with a wrap point at each of its nine gaps.
A `paragraph` renderer that leaves mdformat's `paragraph()` to do the line-start escaping reaches those nine only through the `inline` slot: it injects into the context it hands `paragraph()` either an `inline` renderer or an `inline` postprocessor, which `RenderTreeNode.render` runs inside the inline child's render and so before `_wrap`.
Both produce output identical to the `inline` renderer's, the escaped `1\.` included; the first is `DESIGN.md` section 2.2's contingency for a lost `inline` slot, and neither is a placement with anything of its own.
**Reasoned.** A `paragraph` renderer could also render its inline child itself, as `paragraph()` does, and see the same nine, but it would then have to reimplement the escaping; that variant was not run.
So within 1.0.0 the `inline` slot of a paragraph's only child is the paragraph-level hook that keeps `paragraph()`'s escaping, the renderer rather than the postprocessor for the load-order reason `experiments/seam.py` measures, and this ask is for the slot that does not exist, not for a move the plugin could make today.

**How it relates to the other asks.**
It builds on section 5.6 rather than replacing it, since the step needs wrap points to choose among, and a plugin named as the line-breaker, as section 5.5's variants would name it, is the one whose step runs.
It is the largest of the asks and changes the renderer rather than the option space, so section 5.6 stays the better first ask.
Under section 5.7 it belongs in a comment on #4, after that thread has been read past its opening comment.
Nothing has been filed.

______________________________________________________________________

## 6. The plugin interface

`ParserExtensionInterface` is a `Protocol` at `plugins.py:34-71`, with five members: `CHANGES_AST`, `RENDERERS`, `POSTPROCESSORS`, `add_cli_argument_group` and `update_mdit`.
Plugins are loaded by entry point into a plain dict at `plugins.py:25`, which is `DESIGN.md` section 2.1's silent-collision fact.

`update_mdit`'s entire docstring, verbatim (`plugins.py:69-71`):

```python
@staticmethod
def update_mdit(mdit: MarkdownIt) -> None:
    """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""
```

One line, and it is about the parser.
`mdit.options["mdformat"]` is mdformat's own configuration, and it happens to hang off the same object that hook is handed, with no access control of any kind.

Contrast `add_cli_argument_group` (`plugins.py:54-67`), whose docstring specifies exactly where values land:

```
Call `group.add_argument()` to add CLI arguments (signature is
the same as argparse.ArgumentParser.add_argument). Values will be
stored in a mapping under mdit.options["mdformat"]["plugin"][<plugin_id>]
where <plugin_id> equals entry point name of the plugin.

The mapping will be merged with values read from TOML config file
section [plugin.<plugin_id>].
```

That is a namespace, enforced at `_cli.py:286-301`, where each action's `dest` is rewritten to `plugin.<plugin_id>.<dest>` and a non-`None` default earns a `DeprecationWarning`.
`wrap` is a core option and sits outside that namespace entirely.

**Reasoned.** A supported hook gives access to unsupported state.
`update_mdit` is published, supported and typed; what route B does inside it is untyped, undocumented and visible to every other plugin in the render.
A plugin writing `mdit.options["mdformat"]["wrap"]` is not doing anything mdformat forbids, and it is not doing anything mdformat offers either.

______________________________________________________________________

## 7. The diagnostic channel

`mdformat.renderer.LOGGER` at `renderer/__init__.py:26` is a standard `logging.getLogger(__name__)`.
mdformat itself uses it once, to warn about renderer conflicts between plugins (`renderer/__init__.py:78-81`).

`RendererWarningPrinter` at `_cli.py:20-23` is a `logging.Handler` whose `emit` writes `f"Warning: {record.msg}\n"` to stderr for `WARNING` and above.
It is attached by `log_handler_applied` (`_cli.py:438-446`) and passed as `_first_pass_contextmanager` at `_cli.py:137`.

Two details that change how a warning behaves, both measured in `wraparg.py` checks 3 and 4 and neither of them obvious from the code:

- **It wraps the first pass only.**
  `_api.py:26-33` runs the build and the first render inside that context manager; the second render at `_api.py:40` is outside it.
  So under `--wrap no`, half the copies of a warning are emitted with the handler already removed.
- **An unhandled warning is still printed.**
  `LOGGER` has no handlers of its own and `propagate` is `True`, so with no root configuration Python's `logging.lastResort` handler prints the bare message to stderr at `WARNING`.
  Disabling `lastResort` makes the output vanish, which is the test that it was the printer.

The consequence for `DESIGN.md` section 2.5: an `mdformat.text()` caller **does** see the warning on stderr, as an unprefixed line, without configuring logging.
What the CLI adds is the `Warning: ` prefix and only on the first pass.
Section 9 records this as the one place this note and `DESIGN.md` disagree.

**Volume.** The warning that `DESIGN.md` section 2.5 specifies is raised from the inline postprocessor, so it fires once per paragraph, not once per document: three paragraphs give three lines on stderr.
Whoever implements `DESIGN.md` section 2.5 needs a once-per-render latch; the option mapping is shared and mutable, so there is somewhere to put one.

The second pass does *not* double it, although `wraparg.py` check 4 measures three lines under `--wrap keep` and six under `--wrap no`.
That experiment warns unconditionally; `DESIGN.md` section 2.5's warning is guarded by `not context.do_wrap`, which is true only under `keep`, and `_api.py:39` re-renders only when `wrap != "keep"`.
The two conditions are complementary, so the pass that doubles a warning is never the pass that raises this one.
The latch is needed per paragraph, not across passes.

______________________________________________________________________

## 8. Reproducing

```
python3 -m venv v && ./v/bin/pip install 'mdformat==1.0.0'
./v/bin/python notes/experiments/wrapkeep.py
./v/bin/python notes/experiments/secondpass.py
./v/bin/python notes/experiments/wraparg.py
```

Use exactly 1.0.0.
Every line number in this note is a 1.0.0 line number and none of these are public API.

______________________________________________________________________

## 9. Where this note and `DESIGN.md` disagree, and what was not checked

**Resolved.** This note found that `DESIGN.md` section 2.5 claimed `mdformat.text()` callers "see nothing unless they configure logging themselves".
The first half was right and the second was not: with no handler configured, `logging.lastResort` writes the message to stderr anyway (section 7).
`DESIGN.md` section 2.5 has since been corrected.
It briefly gained a second point, that the warning fires twice under any wrapping mode because the render runs twice; that was withdrawn, because section 7 shows the double render and the warning's guard are complementary and never coincide.

**Resolved.** Section 2 claimed `extensions` was a usable signal "on both paths", and `wrapkeep.py` printed the same conclusion without ever measuring the API row it was about.
It is absent from `options["mdformat"]` on the API path, so the warning is reachable from the CLI and from TOML only; both section 2 and the script now say so, and `DESIGN.md` section 2.5 records the consequence.

**Resolved.** Section 4 listed two caveats on the root-postprocessor re-render and there are three: `secondpass.py` hardcodes the options and the extension set of the pass it restores, which a real implementation cannot do.

**Not checked:**

- How far the prior art in section 5.7 goes.
  It has been established that mdformat upstream *has* been asked for a sentence wrap mode, three times, and that #4 is open; none of those threads was read past its opening comment.
- How two break-inserting postprocessors compose. Section 5.3 declines the claim for this reason.
- Any mdformat version other than 1.0.0.
  The 2.x line, if it exists, was not looked at.
- Whether route B behaves the same when the plugin is enabled implicitly (no `--extensions`) rather than explicitly.
  Every measurement here named the plugin explicitly, because the test harness has to.
- `--check` and `--validate` interaction with any of this, beyond what `DESIGN.md` section 2.2 already records.
