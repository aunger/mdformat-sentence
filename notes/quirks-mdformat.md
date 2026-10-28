# Quirks: mdformat

A note, not a specification.
Behavior of mdformat itself that `DESIGN.md` works around, or that may be worth an upstream issue.
Version 1.0.0 unless an entry says otherwise; *verified* means run, *read* means read from source.

Each entry is either a **compatibility risk**, which the design works around, or a **filing candidate**, which may also deserve an issue upstream.
Nothing here has been filed.

______________________________________________________________________

## Escaped brackets become a live reference

**Filing candidate.** *Verified* 2026-10-06, no plugins loaded.

```
It cites \[foo\] early. Then [a link][foo] later.

[foo]: https://x.y
```

formats to `It cites [foo] early. …`, which turns escaped text into a shortcut reference link and changes the render.
The CLI refuses the file ("Formatted Markdown renders to different HTML than input Markdown"), exit 1; `mdformat.text()` returns the changed text.
The cause is that `text()` escapes brackets according to `env["used_refs"]`, which grows as rendering proceeds, so text rendered before the link that uses `foo` is not escaped.

The same state makes rendering impure: a second render of the children sees a grown set and renders differently, 49 characters against 47 here.
`DESIGN.md` section 3.1 avoids rendering twice for this reason (`experiments/recorder.py`, `experiments/seam.py` check 3).

## A tilde fence at a line start is not escaped

**Filing candidate.** *Verified* 2026-10-06, no plugins loaded.
`Some text here and ~~~ more text after it.` at `--wrap 10` comes back as a fenced code block, because `paragraph()` escapes other block syntax at a line start but not a run of three or more tildes.
Section 3.5 refuses a break before such a run.

## Unicode whitespace is deleted at a wrapped line edge

**Filing candidate.** *Verified* 2026-10-07, no plugins loaded.

```python
import mdformat
from mdformat._util import is_md_equal

src = "aaaa bbbb\u00a0 cccc dddd\n"
out = mdformat.text(src, options={"wrap": 10}, extensions=set())
print(repr(out), is_md_equal(src, out))
# 'aaaa bbbb\ncccc dddd\n' True
```

The U+00A0 is gone, and `is_md_equal` returns `True`; the CLI, which validates by default, accepts the same input with exit 0 and the character gone.
U+1680 and U+2000 are deleted the same way, and at `--wrap 30` all three survive, because the character is then in the middle of a line.
`paragraph()` strips each line after wrapping (`lines[i] = lines[i].strip()`, *read* in `renderer/_context.py`), and `str.strip()` removes far more than the three characters mdformat turns into wrap points (`quirks-cpython.md`).
`is_md_equal` compares HTML after collapsing every run of `\s+` to one space (*read* in `_util.py`), so validation passes and the loss is silent.
Section 3.5's edge-safety check exists because of this.

mdformat's changelog lists an earlier fix nearby, under 0.7.15: "`--wrap` converts Unicode whitespace to regular spaces and line feeds."
`tests/data/wrap_width_50.md` also has a case titled "Only use space, tab and line feed as wrap points".
Both were *read* at mdformat `56b24ef0c6cfdab501844925971204f858185547`, and they are the reason this does not look intended.

## Emphasis escaping is not idempotent at narrow widths

**Filing candidate.** *Verified* 2026-10-07, no plugins loaded.

```python
import mdformat

s = "A * * b\n"
for _ in range(3):
    s = mdformat.text(s, options={"wrap": 5}, extensions=set())
    print(repr(s))
# 'A *\n\\* b\n'
# 'A \\*\n\\* b\n'
# 'A \\*\n\\* b\n'
```

The second format changes what the first produced, so `mdformat --check --wrap 5` exits 1 on a file that mdformat itself wrote.
The third is stable.
The `*` that changes is the one ending the first line: pass 1 already escapes the one that starts the second line, and pass 2 turns `A *` into `A \*`.
No narrow width is needed to show it, only a bare `*` at the end of a line:

```python
print(repr(mdformat.text("A *\nb\n", options={"wrap": "keep"}, extensions=set())))
# 'A \\*\nb\n'
```

The cause is *read* from source: `escape_asterisk_emphasis` in `mdformat/renderer/_util.py` escapes every literal `*` unless the characters on both sides of it are whitespace, and it reads the edge of a text leaf, which a line break is, as neither.
`escape_underscore_emphasis` does the same to a lone `_`.

mdformat's `tests/test_commonmark_spec.py` asserts that a second pass changes nothing (`md_new == md_2nd_pass`), but it parametrizes `wrap` over `["keep", "no", 60]` only (*read* at the same commit), so no test reaches a width this narrow.

This plugin's output does not depend on width (section 2.5), so it never asks mdformat to wrap at 5.
A `*` attached to a terminator is escaped on pass 1, `Done.* Next` giving `Done.\* Next` (*verified*), so it cannot reach this.
A lone `*` or `_` can, since section 3.3 places a run of lone marks on either side of a newline: `It ended. * Then more.` broken after `ended.` came back with `\*` opening its second line, a source change that renders the same (*verified* 2026-10-28, `experiments/edgeescape.py`).
Section 3.5's edge safety therefore refuses a break beside a literal `*` or `_`.
If section 6.2's "idempotency vs baseline" row ever fails, check this entry before the plugin.

## The CLI and TOML disagree on `wrap = 1`

**Compatibility risk, harmless here.** *Read.*
`_cli.py`'s `validate_wrap_arg` accepts a width of 1 or more; `_conf.py` requires more than 1.
This plugin's output is the same at every integer width (section 2.5), so nothing depends on the difference.

## Renderer conflicts keep the first plugin loaded

**Compatibility risk.** *Read* in `renderer/__init__.py`.
When two plugins define a renderer for the same syntax, mdformat logs "Plugin conflict" and keeps the first; which is first follows load order, and through the API the iteration order of the set passed in, which varies with `PYTHONHASHSEED`.
Section 2.2's canary reports when this plugin loses the `inline` slot.

## Postprocessors run in load order the plugin cannot choose

**Compatibility risk.** *Verified* (`experiments/seam.py`, `experiments/seam_mkdocs.py`).
A node type's postprocessors run in plugin-load order, so a postprocessor cannot know whether another plugin rewrote its input first.
This is why the plugin is a renderer (section 2.2).

## Validation has gaps

**Compatibility risk.** *Read.*
`--check` compares strings and returns before the validation branch; `changes_ast` is OR-ed across every enabled plugin, so one plugin declaring `True` disables validation for all; and the Python API never validates.
Section 2.2 lists these.

## `mdformat.file()` passes a filename but reads no config

**Compatibility risk.** *Read* in `_api.py`.
A plugin that walks up from the filename to find `.mdformat.toml` finds the file the CLI would have read, which mdformat itself did not (section 4).

## Plugin options reach the hook point through an undocumented splat

**Compatibility risk.** *Read* (`_api.py`).
`options={"plugin": {"sentence": {...}}}` reaches `context.options` through `mdformat.text()`, which is not a supported interface; the test harnesses use it (section 4).

## Plugin option flags have cases that section 2.4 does not cover

**Compatibility risk.** *Verified* 2026-10-07, and again 2026-10-12 (the unhashable default 2026-10-16), by calling `make_arg_parser` from `mdformat/_cli.py` with the stand-in plugins below, no plugin installed.
Section 2.4 covers the `dest` rewrite and the requirement that a default must be `None` or `argparse.SUPPRESS`.
Further cases:

- **`store_true` trips the default warning by itself.** Its default is `False`, so the plugin's own flag, with no other mistake, triggers a warning that begins `` DeprecationWarning: The `default` (False) for ['--demo-flag'] from the 'demo' plugin, will always override any value configured in TOML. `` Under the default warning filters it is not shown: `warn_explicit` attributes it to the plugin's source file, and those filters show a `DeprecationWarning` only when it is attributed to `__main__`. It prints under `-W default` and raises under `-W error::DeprecationWarning`; `-W error::UserWarning` does not catch it. The practical hazard is what the message says, without the message being seen: with `demo_flag = true` under `[plugin.demo]` in `.mdformat.toml`, the stand-in plugin received `False` from the CLI's `run`, which returned 0 and showed no warning (the second snippet below). Write `default=None` beside `store_true`, or use `store_const` with `const=True, default=None`.
- **An unhashable default crashes the CLI.** With `default=[]`, `make_arg_parser` raises `TypeError: unhashable type: 'list'` from the very test that decides whether to warn, `action.default not in {None, argparse.SUPPRESS}`, and since `run` builds the parser with every installed plugin, one such plugin takes down the whole CLI for anyone who has it installed.
- **The default metavar comes from the rewritten `dest`.** An option added as `--demo-count` with `type=int` and no `metavar` shows in `--help` as `--demo-count PLUGIN.DEMO.DEMO_COUNT`. Pass `metavar=`.
- **Flag strings are not namespaced, so two plugins that register the same one collide.** `make_arg_parser` raises `ArgumentError: argument --only: conflicting option string: --only`. `run` calls it before reading any argument, with every installed plugin (`PARSER_EXTENSIONS`), enabled or not, so a user who has both installed loses the whole CLI. The Python API never references `_cli.py` and is unaffected.

The stand-ins, run as a script; the comments are its output under each filter:

```python
import argparse
from mdformat._cli import make_arg_parser


class Demo:
    def add_cli_argument_group(group):
        group.add_argument("--demo-flag", action="store_true")
        group.add_argument("--demo-count", type=int)
        group.add_argument("--only", action="store_const", const=True)


class Other:
    def add_cli_argument_group(group):
        group.add_argument("--only", action="store_const", const=True)


help_text = make_arg_parser({}, {}, {"demo": Demo}).format_help()
print("--demo-count PLUGIN.DEMO.DEMO_COUNT" in help_text)
try:
    make_arg_parser({}, {}, {"demo": Demo, "other": Other})
except argparse.ArgumentError as e:
    print(e)
# python demo.py, and python -W error::UserWarning demo.py, exit 0:
#   True
#   argument --only: conflicting option string: --only
# python -W default demo.py prints the same two lines, and the
#   DeprecationWarning to stderr (twice, once per make_arg_parser call),
#   attributed to demo.py at `class Demo:`
# python -W error::DeprecationWarning demo.py ends in a traceback, exit 1
```

The TOML override, run in a directory holding `a.md` with `Text.` and a `.mdformat.toml` with `demo_flag = true` under `[plugin.demo]`:

```python
import mdformat.plugins
from mdformat._cli import run


class Demo:
    CHANGES_AST = False
    RENDERERS = {}

    def update_mdit(mdit):
        pass

    def add_cli_argument_group(group):
        group.add_argument("--demo-flag", action="store_true")

    def _seen(text, node, context):
        print(context.options["mdformat"]["plugin"]["demo"])
        return text

    POSTPROCESSORS = {"paragraph": _seen}


mdformat.plugins.PARSER_EXTENSIONS["demo"] = Demo
print(run(["a.md"]))
# {'demo_flag': False}
# 0
```

## Plugin errors are not caught

**Compatibility risk.** *Read.*
Nothing in `_api.py` or `_cli.py` wraps plugin code in `try`/`except`, so a malformed rules file surfaces as a traceback, and `sys.exit()` from a plugin would end an API caller's process (section 4).

## `mdformat.renderer.LOGGER` reaches stderr without a handler

**Compatibility risk.** *Verified* by `experiments/wraparg.py`.
`_cli.py` attaches a handler to the logger that prefixes `Warning: ` and writes to stderr, and that handler is CLI-only.
A library caller is not silent anyway: with no handler configured, `logging.lastResort` writes a warning to stderr unprefixed.
`DESIGN.md` section 2.5's own warning cannot reach an API caller for another reason, its guard, so this matters only to other messages the plugin might log.
