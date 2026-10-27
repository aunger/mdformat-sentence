"""What each paragraph-level hook point receives, against the `inline` slot. MDFORMAT-WRAP-AND-OVERRIDES.md §5.8.

Needs mdformat 1.0.0.

One paragraph is rendered at --wrap no through three stand-in plugins, each breaking at a wrap
point after a period and pinning every other wrap point to a space, as DESIGN.md §3.4 does:
  a. a `paragraph` postprocessor alone;
  b. the `inline` renderer of DESIGN.md §2.2;
  c. a `paragraph` renderer that injects (b) into the context and calls mdformat's own
     `paragraph()`, the contingency of DESIGN.md §2.2 and notes/FUTURE-WORK.md.

It establishes three things:
  1. a `paragraph` postprocessor receives the paragraph as one line with no wrap point left in
     it, after `_wrap` and line-start escaping, so it has nothing to decide among and would have
     to re-derive both;
  2. the `inline` renderer receives the same paragraph with a wrap point at every gap;
  3. a `paragraph` renderer reaches those wrap points only by injecting an `inline` renderer,
     which is the same hook point with one more layer, and its output is identical to (b)'s
     (the script compares them and prints the result). Line-start escaping is not exercised: the
     input has no line start to escape, so "after escaping" in 1. is read from `paragraph()`.

It prints what each hook receives, the number of wrap points in it, and the final output.
"""
import types

import mdformat
from mdformat.plugins import PARSER_EXTENSIONS
from mdformat.renderer import DEFAULT_RENDERERS, WRAP_POINT

SRC = "See `a b`. Next [x y](u) here.\nThen *two* ends. Done.\n"
SEEN = {}


def inline_renderer(node, context):
    text = DEFAULT_RENDERERS["inline"](node, context)
    if node.parent is None or node.parent.type != "paragraph":
        return text
    SEEN["inline renderer"] = text
    parts = text.split(WRAP_POINT)
    out = [parts[0]]
    for part in parts[1:]:
        out.append("\n" if out[-1].endswith(".") else " ")
        out.append(part)
    return "".join(out)


def paragraph_renderer(node, context):
    injected = context._replace(renderers={**context.renderers, "inline": inline_renderer})
    return DEFAULT_RENDERERS["paragraph"](node, injected)


def paragraph_postprocessor(text, node, context):
    SEEN["paragraph postprocessor"] = text
    return text


def run(label, renderers, postprocessors):
    SEEN.clear()
    PARSER_EXTENSIONS["x"] = types.SimpleNamespace(
        RENDERERS=renderers,
        POSTPROCESSORS=postprocessors,
        CHANGES_AST=False,
        update_mdit=lambda mdit: None,
    )
    try:
        out = mdformat.text(SRC, options={"wrap": "no"}, extensions={"x"})
    finally:
        del PARSER_EXTENSIONS["x"]
    print(f"== {label}")
    for hook, text in SEEN.items():
        print(f"  {hook} receives {text!r}  (wrap points: {text.count(WRAP_POINT)})")
    print(f"  output: {out!r}")
    return out


PP = {"paragraph": paragraph_postprocessor}
run("a. paragraph postprocessor alone", {}, PP)
out_b = run("b. inline renderer", {"inline": inline_renderer}, PP)
out_c = run("c. paragraph renderer injecting an inline renderer", {"paragraph": paragraph_renderer}, PP)
print(f"== output of c identical to output of b: {out_b == out_c}")
