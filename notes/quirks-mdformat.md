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
`DESIGN.md` §3.1 avoids rendering twice for this reason (`experiments/recorder.py`, `experiments/seam.py` §3).

## A tilde fence at a line start is not escaped

**Filing candidate.** *Verified* 2026-10-06, no plugins loaded.
`Some text here and ~~~ more text after it.` at `--wrap 10` comes back as a fenced code block, because `paragraph()` escapes other block syntax at a line start but not a run of three or more tildes.
§3.5 refuses a break before such a run.

## The CLI and TOML disagree on `wrap = 1`

**Compatibility risk, harmless here.** *Read.*
`_cli.py`'s `validate_wrap_arg` accepts a width of 1 or more; `_conf.py` requires more than 1.
This plugin's output is the same at every integer width (§2.5), so nothing depends on the difference.

## Renderer conflicts keep the first plugin loaded

**Compatibility risk.** *Read* in `renderer/__init__.py`.
When two plugins define a renderer for the same syntax, mdformat logs "Plugin conflict" and keeps the first; which is first follows load order, and through the API the iteration order of the set passed in, which varies with `PYTHONHASHSEED`.
§2.2's canary reports when this plugin loses the `inline` slot.

## Postprocessors run in load order the plugin cannot choose

**Compatibility risk.** *Verified* (`experiments/seam.py`, `experiments/seam_mkdocs.py`).
A node type's postprocessors run in plugin-load order, so a postprocessor cannot know whether another plugin rewrote its input first.
This is why the plugin is a renderer (§2.2).

## Validation has gaps

**Compatibility risk.** *Read.*
`--check` compares strings and returns before the validation branch; `changes_ast` is OR-ed across every enabled plugin, so one plugin declaring `True` disables validation for all; and the Python API never validates.
§2.2 lists these.

## `mdformat.file()` passes a filename but reads no config

**Compatibility risk.** *Read* in `_api.py`.
A plugin that walks up from the filename to find `.mdformat.toml` finds the file the CLI would have read, which mdformat itself did not (§4).

## Plugin options reach the hook point through an undocumented splat

**Compatibility risk.** *Read* (`_api.py`).
`options={"plugin": {"sentence": {...}}}` reaches `context.options` through `mdformat.text()`, which is not a supported interface; the test harnesses use it (§4).

## Plugin errors are not caught

**Compatibility risk.** *Read.*
Nothing in `_api.py` or `_cli.py` wraps plugin code in `try`/`except`, so a malformed rules file surfaces as a traceback, and `sys.exit()` from a plugin would end an API caller's process (§4).
