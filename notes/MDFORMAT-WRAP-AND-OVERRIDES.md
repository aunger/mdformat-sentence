# mdformat's wrap arguments, its plugin interface, and what a plugin can override

A reference, not a decision, and not a specification.
`DESIGN.md` is normative; nothing here amends it, and where the two disagree §9 says so rather than settling it.

It exists for three questions that are still open and will be asked later: whether to patch mdformat, whether to file an upstream request for a wrap mode, and how to implement the warning `DESIGN.md` §2.5 specifies.
It answers what mdformat does and what a plugin is able to reach, and stops there.

Everything below was measured by execution against mdformat 1.0.0 unless it is marked **Reasoned**, which marks argument rather than measurement.
Every `file:line` was re-read against `v/lib/python3.11/site-packages/mdformat/` on 2026-09-17; paths below are relative to that directory.
Some citations moved from the ones in earlier notes, so re-read rather than trust these too.

| program | what it establishes |
| --- | --- |
| `experiments/wrapkeep.py` | What a plugin can and cannot see about `wrap`, and the three routes to overriding it. §2 and §3. |
| `experiments/secondpass.py` | That a `POSTPROCESSORS["root"]` re-render restores mdformat's second pass, over a bare paragraph and over a document with a list, a blockquote and a fenced block. §4. |
| `experiments/wraparg.py` | `wrap` as an *argument*: the two validators, `--wrap sentence` today, and where a renderer warning actually goes. §5 and §7. |

All three need mdformat 1.0.0.
`experiments/probe.py` is the prior measurement of what reaches the seam under each mode, and §1 does not repeat it.

______________________________________________________________________

## 1. Where the wrap value is read

Five places, and no two of them agree on how to read it.

**The default.** `DEFAULT_OPTS` in `_conf.py:11-22` is a `MappingProxyType`, and `wrap` is `"keep"` at `_conf.py:13`.

**CLI validation.** `validate_wrap_arg` at `_cli.py:189-195` returns `"keep"` or `"no"` unchanged, otherwise calls `int(value)` and rejects anything below 1.
It is wired as argparse's `type=` at `_cli.py:233-238`, so a bad value is a parse error and never reaches a file.

**TOML validation.** `_validate_values` at `_conf.py:56-63` is a second, independent gate: `wrap` must be an `int` **greater than 1**, or `"keep"`, or `"no"`.
`_validate_keys` at `_conf.py:99-105` separately rejects any key not in `DEFAULT_OPTS`.

The two gates disagree on `1`: `--wrap 1` is accepted, `wrap = 1` in `.mdformat.toml` raises `InvalidConfError`.
Measured, `wraparg.py` §1.
It is a pre-existing inconsistency and harmless here; it is recorded only because it proves the two are genuinely separate code paths, which §5 depends on.

**The renderer's predicate.** `RenderContext.do_wrap` at `renderer/_context.py:641-644`:

```python
wrap_mode = self.options.get("mdformat", {}).get("wrap", DEFAULT_OPTS["wrap"])
return isinstance(wrap_mode, int) or wrap_mode == "no"
```

Note the two `.get()`s with defaults.
This is what makes `do_wrap` safe to evaluate when the key is absent, which §2 shows is a real case.

**The renderer's use of the value.** `paragraph` at `renderer/_context.py:390-406` reads `context.options["mdformat"]["wrap"]` at line 395 with a bare subscript and no default, guarded only by `if context.do_wrap` on line 394.
An `int` is reduced by `context.env["indent_width"]` and floored at 1, then the value goes to `_wrap` as `width`.
`_wrap` at `renderer/_context.py:348-362` has an explicit `if width == "no"` branch that returns after `_prepare_wrap`, and otherwise hands the value to `cached_textwrapper` (`renderer/_context.py:337-345`) as a `textwrap.TextWrapper` width.

So `do_wrap` decides *whether*, and the same option decides *what*, and they are read independently.
§3.2 is what that costs.

The observable behaviour of the three modes is `DESIGN.md` §2.5's table and is not repeated here.

______________________________________________________________________

## 2. What a plugin can see about `wrap`

Measured, `wrapkeep.py`, from an inline postprocessor reading `context.options["mdformat"]`.

| how mdformat was invoked | `"wrap"` in `options["mdformat"]` | value |
| --- | --- | --- |
| `mdformat.text(src)` | **absent** | — |
| `mdformat.text(src, options={"wrap": "keep"})` | present | `"keep"` |
| CLI, no `--wrap` | present | `"keep"` |
| CLI, `--wrap keep` | present | `"keep"` |
| `wrap = "keep"` in `.mdformat.toml` | present | `"keep"` |

The API row is absent because `build_mdit` at `_util.py:32-42` assigns the caller's mapping verbatim at line 33 — `mdit.options["mdformat"] = mdformat_opts` — with no defaults merged into it.
The three CLI rows are identical because `_cli.py:56` builds `{**DEFAULT_OPTS, **toml_opts, **cli_core_opts}` and `_cli.py:32-34` drops every argparse value that is `None`, so an unset `--wrap` contributes nothing to the merge.

**A plugin can therefore distinguish an explicit `keep` from a defaulted one through the Python API and cannot through the CLI.**
CI runs the CLI.

`extensions` is a usable signal on both paths, because `DEFAULT_OPTS["extensions"]` is `None` (`_conf.py:19`) and `_cli.py:82-88` only replaces the full plugin mapping when it is not `None`.
A non-`None` `options["mdformat"]["extensions"]` therefore means someone typed the flag or wrote the TOML key.
That is the condition `DESIGN.md` §2.5's warning keys off, and it is the reason it keys off `--extensions` rather than off `wrap`.

______________________________________________________________________

## 3. Overriding `wrap` from a plugin

The question this section answers is narrow: *can* a plugin make itself work under `--wrap keep`, where §2.5's table says it is inert.
It can.
`DESIGN.md` declines to, and §3.1's three consequences are why.

### 3.1 Route B: assign the option in `update_mdit`

Two lines, through a published hook:

```python
def update_mdit(mdit):
    mdit.options["mdformat"]["wrap"] = "no"
```

Measured, `wrapkeep.py`.
Under a caller who asked for `keep`, the baseline sees zero wrap points and returns the input byte for byte; with the assignment, 17 wrap points reach the seam and the paragraph comes out on two lines.
It works because `build_mdit` calls `plugin.update_mdit(mdit)` at `_util.py:42`, after `mdit.options["mdformat"]` has been assigned at line 33 and before anything renders.

Three consequences, all measured or read:

1. **The second pass does not fire.**
   `_api.py:39` tests `options.get("wrap", DEFAULT_OPTS["wrap"]) != "keep"` against the **caller's** mapping, which still says `keep`, so the re-render at `_api.py:40` is skipped.
   Seam calls stay at 1 where the honest `--wrap no` gives 2.
   That is the pass `DESIGN.md` §2.3 relies on.
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
The cause is §1's split: `do_wrap` now says yes, `paragraph` at `renderer/_context.py:395` still reads `"keep"`, and `textwrap` is handed the string as a width.
Both have to be patched together, which means patching `paragraph` as well.

`DEFAULT_RENDERERS` is a `mappingproxy`, so it cannot be assigned into from outside.
The supported way to replace a renderer is a plugin's own `RENDERERS` mapping, which `render_tree` merges at `renderer/__init__.py:89`.
That is the `paragraph` renderer hook `DESIGN.md` §2.2 rejects on unrelated grounds, so route C arrives at a door already closed.

______________________________________________________________________

## 4. Restoring the second pass from a root postprocessor

If route B were ever taken, the pass it skips can be put back.
Measured, `secondpass.py`.

Of the four node types tried — `root`, `document`, `inline`, `paragraph` — three fire and `document` does not.
`root` is the whole rendered document, applied by `RenderTreeNode.render` at `renderer/_tree.py:9-14` like any other postprocessor.

A guarded re-render from `POSTPROCESSORS["root"]` takes seam calls from 1 back to 2 and produces output identical to the honest `--wrap no`, on a bare paragraph and on a document containing a list, a blockquote and a fenced code block.

Two caveats, both measured:

- **The trailing newline doubles.**
  A root postprocessor is handed already-finalised output — `render_tree` appends the final `"\n"` at `renderer/__init__.py:94-99` — so re-rendering it finalises twice.
  `.rstrip("\n")` on the way in and on the way out fixes it; without that the output ends `'.\n\n'` and no longer matches.
- **It needs a re-entrancy guard.**
  The re-render runs the same plugin, including this postprocessor.
  Unguarded, it recurses to `RecursionError`.

**Honest limit on the claim.** Route B *alone* already matched the honest `--wrap no` byte for byte on both documents tried.
No input has been exhibited here where one pass and two disagree.
The re-render restores the pass, not a known output difference; mdformat runs two because escaping depends on wrapping (`_api.py:35-40`), so this is insurance against that class of case rather than a fix for a measured one.

______________________________________________________________________

## 5. `--wrap sentence` as an upstream request

### 5.1 The primary defect: `--wrap no` becomes false

Once this plugin is installed, `--wrap no` misdescribes what the tool does.
The user asked for no wrapping and got wrapping: line breaks inserted at computed positions, at sentence boundaries rather than at a column, but inserted all the same.

What makes that more than cosmetic is that `no` is the **only** wrap value whose meaning the plugin redefines.
`--wrap keep` means the same thing with the plugin installed as without it.
`--wrap 80` means the same thing.
`--wrap no` means "one line per paragraph" alone and "one sentence per line" with this plugin present, so the same flag value produces two categorically different documents depending on what is installed, with nothing on the command line to say which one you got.

### 5.2 The second defect: `--wrap no` without the plugin is silent and destructive

Run `--wrap no` on a hand-broken corpus without the plugin installed and mdformat collapses every paragraph to a single line, with no warning.
That is `DESIGN.md` §2.5's cost, measured in `experiments/handwritten.py`, and it is the failure mode of a CI config that names `--wrap no` on a machine where the plugin did not install.

`--wrap sentence` fails loud instead.
Measured, `wraparg.py` §2: today it exits 2 at argument parsing with `argument --wrap: invalid validate_wrap_arg value: 'sentence'`, before a file is opened.
An unrecognised wrap mode is rejected; `no` is always recognised, and means something destructive.

### 5.3 The common cause

**Reasoned.** Both defects are the same thing seen from two sides: `no` is being used as a carrier for "let the plugin decide", which is not what it says.
A value that names the behaviour rather than negating a different one fixes both, because a name that is wrong when the plugin is absent can be rejected, and a name that is right when it is present does not have to be read as a lie.

Nothing here claims `--wrap sentence` would disambiguate between two break-inserting plugins.
Postprocessors chain (`renderer/__init__.py:84-88`), so two such plugins compose under any wrap value, and how they compose was not measured.

### 5.4 What the change would touch

Mechanically `--wrap sentence` is identical to `--wrap no` plus this plugin, because `no` already means "emit wrap points, do not width-wrap" — `_wrap`'s early return at `renderer/_context.py:356-357`.
It adds a name and a rejection, not a mechanism.

**Four call sites, not three.**

| site | change |
| --- | --- |
| `_cli.py:189-195`, `validate_wrap_arg` | accept `"sentence"` alongside `"keep"` and `"no"` |
| `_conf.py:56-63`, `_validate_values` | accept it in the TOML gate, which is separate code |
| `renderer/_context.py:641-644`, `do_wrap` | return `True` for it |
| `renderer/_context.py:348-362`, `_wrap` | treat it like `"no"` |

The TOML gate is the one the earlier summary of this work missed.
Measured, `wraparg.py` §1: `wrap = "sentence"` in `.mdformat.toml` raises `InvalidConfError` today, so changing only the CLI would leave the mode unreachable from a config file — which is how a repo actually pins its formatter.

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

For this plugin the entry-point id is `sentence` (`DESIGN.md` §2), so variant B yields the exact spelling §5 wants, `--wrap sentence`, at no cost in ergonomics.

**Variant C, the plugin declares its modes.**
Add an optional `WRAP_MODES: Iterable[str]` to the `ParserExtensionInterface` Protocol (§6), and let mdformat accept any value an enabled plugin declared.
This extends the existing extension point rather than overloading the id space, and it allows one plugin to offer more than one mode.
A larger ask than B, and a cleaner shape.

Both still touch the four sites in §5.4; what changes is that the accepted set is computed rather than hardcoded, which is the part that makes it a mechanism instead of a favour.

**What neither variant buys.**
The flag would *designate* but not *enforce*.
Postprocessors chain (`renderer/__init__.py:84-88`), so a plugin that is not the named one still runs unless plugins cooperate by checking whether they were named.
That makes it a convention, and §5.3's disclaimer stands unchanged.

**Two costs to state in any request.**
Variant B needs `keep` and `no` reserved against a plugin id colliding with them.
Both make a shared `.mdformat.toml` valid on one machine and invalid on another, since the value's legality depends on what is installed — arguably correct, since the plugin genuinely is required, but it is a new failure mode for a checked-in config.

### 5.6 Prior art

Searched on 2026-09-17, on the mdformat issue tracker, for issues about `--wrap`, wrap modes, and plugins controlling wrapping.
**Nothing proposes new wrap modes, plugin-defined wrap modes, or semantic line breaks.**
So this is greenfield: there is no prior rejection to work around, and no existing thread to join.

Three open issues are adjacent and are listed only by title, without characterising them further:

- **#590** `--wrap can turn a paragraph into a code fence (~~~ reaching line start)`
- **#589** `--wrap silently deletes a non-breaking space at a wrapped line edge`
- **#588** `mdformat --check fails on a file mdformat just formatted (small --wrap)`

The first two correspond to the two upstream defects `DESIGN.md` §3.5 already works around, the tilde fence and the whitespace deletion.
Who filed them was not checked.

______________________________________________________________________

## 6. The plugin interface

`ParserExtensionInterface` is a `Protocol` at `plugins.py:34-71`, with five members: `CHANGES_AST`, `RENDERERS`, `POSTPROCESSORS`, `add_cli_argument_group` and `update_mdit`.
Plugins are loaded by entry point into a plain dict at `plugins.py:25`, which is §2.1's silent-collision fact.

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

**Reasoned.** The framing worth carrying forward: the door is official, the room behind it is not.
`update_mdit` is published, supported and typed; what route B does inside it is untyped, undocumented and visible to every other plugin in the render.
A plugin writing `mdit.options["mdformat"]["wrap"]` is not doing anything mdformat forbids, and it is not doing anything mdformat offers either.

______________________________________________________________________

## 7. The diagnostic channel

`mdformat.renderer.LOGGER` at `renderer/__init__.py:26` is a standard `logging.getLogger(__name__)`.
mdformat itself uses it once, to warn about renderer conflicts between plugins (`renderer/__init__.py:78-81`).

`RendererWarningPrinter` at `_cli.py:20-23` is a `logging.Handler` whose `emit` writes `f"Warning: {record.msg}\n"` to stderr for `WARNING` and above.
It is attached by `log_handler_applied` (`_cli.py:438-446`) and passed as `_first_pass_contextmanager` at `_cli.py:137`.

Two details that change how a warning behaves, both measured in `wraparg.py` §3-4 and neither of them obvious from the code:

- **It wraps the first pass only.**
  `_api.py:26-33` runs the build and the first render inside that context manager; the second render at `_api.py:40` is outside it.
  So under `--wrap no`, half the copies of a warning are emitted with the handler already removed.
- **An unhandled warning is still printed.**
  `LOGGER` has no handlers of its own and `propagate` is `True`, so with no root configuration Python's `logging.lastResort` handler prints the bare message to stderr at `WARNING`.
  Disabling `lastResort` makes the output vanish, which is the test that it was the printer.

The consequence for `DESIGN.md` §2.5: an `mdformat.text()` caller **does** see the warning on stderr, as an unprefixed line, without configuring logging.
What the CLI adds is the `Warning: ` prefix and only on the first pass.
§9 records this as the one place this note and `DESIGN.md` disagree.

**Volume.** The warning §2.5 specifies is raised from the inline postprocessor, so it fires once per paragraph, not once per document: three paragraphs give three lines on stderr under `--wrap keep`, and six under `--wrap no` where the second pass doubles them.
Whoever implements §2.5 needs a once-per-render latch; the option mapping is shared and mutable, so there is somewhere to put one.

______________________________________________________________________

## 8. Reproducing

```
python3 -m venv v && ./v/bin/pip install 'mdformat==1.0.0'
./v/bin/python notes/experiments/wrapkeep.py
./v/bin/python notes/experiments/secondpass.py
./v/bin/python notes/experiments/wraparg.py
```

Pin 1.0.0.
Every line number in this note is a 1.0.0 line number and none of these are public API.

______________________________________________________________________

## 9. Where this note and `DESIGN.md` disagree, and what was not checked

**Resolved.** This note found that `DESIGN.md` §2.5 claimed `mdformat.text()` callers "see nothing unless they configure logging themselves".
The first half was right and the second was not: with no handler configured, `logging.lastResort` writes the message to stderr anyway (§7).
`DESIGN.md` §2.5 has since been corrected, and gained a second point found the same way: the warning fires once per render pass, so twice under any wrapping mode.

**Not checked:**

- Whether mdformat upstream has been asked for a sentence wrap mode already.
  An issue search was run on 2026-09-17 and is recorded in §5.6.
- How two break-inserting postprocessors compose. §5.3 declines the claim for this reason.
- Any mdformat version other than 1.0.0.
  The 2.x line, if it exists, was not looked at.
- Whether route B behaves the same when the plugin is enabled implicitly (no `--extensions`) rather than explicitly.
  Every measurement here named the plugin explicitly, because the test harness has to.
- `--check` and `--validate` interaction with any of this, beyond what `DESIGN.md` §2.2 already records.
