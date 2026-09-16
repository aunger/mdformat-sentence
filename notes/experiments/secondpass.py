import types, mdformat, mdformat.plugins as P
from mdformat.renderer import WRAP_POINT
ENDS = lambda s: s.rstrip().endswith((".","!","?"))
SRC = ("Because the cascade picks by width,\n"
       "an edit upstream can change which candidate wins. The tool reports success.\n")

def build(override_wrap, root_second_pass):
    state = {"depth": 0, "inline_calls": 0}
    def inline_pp(text, node, context):
        if node.parent is None or node.parent.type != "paragraph": return text
        state["inline_calls"] += 1
        if WRAP_POINT not in text: return text
        segs = text.split(WRAP_POINT); out=[segs[0]]
        for s in segs[1:]:
            out.append("\n" if ENDS(out[-1]) else " "); out.append(s)
        return "".join(out)
    def root_pp(text, node, context):
        if not root_second_pass or state["depth"]: return text
        state["depth"] += 1
        try:
            return mdformat.text(text.rstrip("\n"), options={"wrap":"keep"}, extensions={"probe"}).rstrip("\n")
        finally:
            state["depth"] -= 1
    post = {"inline": inline_pp}
    if root_second_pass: post["root"] = root_pp
    return types.SimpleNamespace(CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS=post,
        add_cli_options=lambda p: None,
        update_mdit=(lambda m: m.options["mdformat"].__setitem__("wrap","no")) if override_wrap else (lambda m: None)), state

P.PARSER_EXTENSIONS
print("reference: honest --wrap no, mdformat's own double render")
plug, st = build(False, False); P.PARSER_EXTENSIONS["probe"]=plug
ref = mdformat.text(SRC, options={"wrap":"no"}, extensions={"probe"})
print(f"   inline seam calls: {st['inline_calls']}")
print(f"   output: {ref!r}\n")

for label, rsp in (("route B alone (no second pass)", False),
                   ("route B + root postprocessor re-render", True)):
    plug, st = build(True, rsp); P.PARSER_EXTENSIONS["probe"]=plug
    out = mdformat.text(SRC, options={"wrap":"keep"}, extensions={"probe"})
    print(label)
    print(f"   inline seam calls: {st['inline_calls']}")
    print(f"   matches reference: {out == ref}")
    print(f"   output: {out!r}\n")
