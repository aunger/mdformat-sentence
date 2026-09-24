"""Simulate splitting mdformat's do_wrap into two predicates.

Today one property gates both "are wrap points produced" (softbreak:109,
text:153, and the link:267 / image:204 collapses that depend on them) and
"does mdformat width-wrap" (paragraph:394).

Here the first group is forced True while the second follows the user's real
wrap mode, to see whether a plugin can work under --wrap keep without mdformat
adding any geometric wrapping of its own.
"""
import types, mdformat, mdformat.plugins as P
import mdformat.renderer._context as C
from mdformat.renderer import WRAP_POINT, DEFAULT_RENDERERS

SRC = ("Because the cascade picks by width,\n"
       "an edit upstream can change which candidate wins. The tool reports success.\n\n"
       "See the [docs](https://example.com/a) for more. A second sentence here.\n")
ENDS = lambda s: s.rstrip().endswith((".", "!", "?"))

def inline_pp(text, node, context):
    if node.parent is None or node.parent.type != "paragraph": return text
    if WRAP_POINT not in text: return text
    segs = text.split(WRAP_POINT); out = [segs[0]]
    for s in segs[1:]:
        out.append("\n" if ENDS(out[-1]) else " "); out.append(s)
    return "".join(out)

def paragraph_honouring_real_mode(node, context):
    """What mdformat's paragraph() would do if width-wrapping had its own gate."""
    real = context.options["mdformat"].get("wrap", "keep")
    if isinstance(real, int) or real == "no":
        return DEFAULT_RENDERERS["paragraph"](node, context)
    # user said keep: emit the inline text, no width wrapping at all
    inline = node.children[0].render(context)
    return inline

plug = types.SimpleNamespace(CHANGES_AST=False,
    RENDERERS={"paragraph": paragraph_honouring_real_mode},
    POSTPROCESSORS={"inline": inline_pp},
    add_cli_argument_group=lambda g: None, update_mdit=lambda m: None)
P.PARSER_EXTENSIONS; P.PARSER_EXTENSIONS["probe"] = plug

orig = C.RenderContext.do_wrap
C.RenderContext.do_wrap = property(lambda self: True)   # producers always on
try:
    out = mdformat.text(SRC, options={"wrap": "keep"}, extensions={"probe"})
finally:
    C.RenderContext.do_wrap = orig

print("source:"); [print("   ", l) for l in SRC.rstrip("\n").split("\n")]
print("\nunder --wrap keep, with production split from width-wrapping:")
[print("   ", l) for l in out.rstrip("\n").split("\n")]
print("\n  link survived as one atom:", "[docs](https://example.com/a)" in out)
print("  no stray wrap points:", WRAP_POINT not in out)
