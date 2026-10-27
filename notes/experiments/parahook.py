r"""What each paragraph-level hook point receives, against the `inline` slot. MDFORMAT-WRAP-AND-OVERRIDES.md §5.8.

Needs mdformat 1.0.0.

One paragraph is rendered at --wrap no through four stand-in plugins, each breaking at a wrap
point after a period and pinning every other wrap point to a space, as DESIGN.md §3.4 does:
  a. a `paragraph` postprocessor alone;
  b. the `inline` renderer of DESIGN.md §2.2;
  c. a `paragraph` renderer that injects (b) into the context and calls mdformat's own
     `paragraph()`, the contingency of DESIGN.md §2.2 and notes/FUTURE-WORK.md;
  d. a `paragraph` renderer that injects the same decision as an `inline` postprocessor instead,
     through `context._replace(postprocessors=...)`, DESIGN.md §3.1's own mechanism.
The paragraph holds a sentence that ends in `1.`, so a break after it puts `1.` at a line start,
where `paragraph()` must escape it.

It establishes three things:
  1. a `paragraph` postprocessor receives the paragraph as one line with no wrap point left in
     it, after `_wrap` and line-start escaping, so it has nothing to decide among and would have
     to re-derive both;
  2. the `inline` renderer receives the same paragraph with a wrap point at every gap;
  3. a `paragraph` renderer reaches those wrap points only through the `inline` slot, as a
     renderer (c) or as a postprocessor (d), which is the same hook point with one more layer;
     both keep `paragraph()`'s escaping, and both outputs are identical to (b)'s, the `1\.`
     escape included (the script compares them and prints the result).

It prints what each hook receives, the number of wrap points in it, and the final output.
"""
import types

import mdformat
from mdformat.plugins import PARSER_EXTENSIONS
from mdformat.renderer import DEFAULT_RENDERERS, WRAP_POINT

SRC = "See `a b`. Next [x y](u) here.\nThen *two* ends. 1. Done.\n"
SEEN = {}


def decide(text, node, hook):
    if node.parent is None or node.parent.type != "paragraph":
        return text
    SEEN[hook] = text
    parts = text.split(WRAP_POINT)
    out = [parts[0]]
    for part in parts[1:]:
        out.append("\n" if out[-1].endswith(".") else " ")
        out.append(part)
    return "".join(out)


def inline_renderer(node, context):
    return decide(DEFAULT_RENDERERS["inline"](node, context), node, "inline renderer")


def inline_postprocessor(text, node, context):
    return decide(text, node, "inline postprocessor")


def paragraph_renderer(node, context):
    injected = context._replace(renderers={**context.renderers, "inline": inline_renderer})
    return DEFAULT_RENDERERS["paragraph"](node, injected)


def paragraph_renderer_pp(node, context):
    pps = dict(context.postprocessors)
    pps["inline"] = (*pps.get("inline", ()), inline_postprocessor)
    return DEFAULT_RENDERERS["paragraph"](node, context._replace(postprocessors=pps))


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
out_d = run("d. paragraph renderer injecting an inline postprocessor", {"paragraph": paragraph_renderer_pp}, PP)
print(f"== outputs of c and d identical to output of b: {out_b == out_c == out_d}")
