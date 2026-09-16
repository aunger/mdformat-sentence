import types, mdformat, mdformat.plugins as P
from mdformat.renderer import WRAP_POINT

calls = []
def inline_pp(text, node, context):
    if node.parent is not None and node.parent.type == "paragraph":
        kids = [c.type for c in node.children]
        calls.append((text, kids, type(context).__name__,
                      hasattr(context, "_replace"), sorted(context.renderers)[:6]))
    return text

probe = types.SimpleNamespace(CHANGES_AST=False, RENDERERS={},
    POSTPROCESSORS={"inline": inline_pp},
    add_cli_options=lambda p: None, update_mdit=lambda m: None)
P.PARSER_EXTENSIONS
P.PARSER_EXTENSIONS["probe"] = probe

SRC = "Alpha beta gamma.\nDelta epsilon. Zeta eta.\n"
print("SOURCE:", repr(SRC), "\n")
out = mdformat.text(SRC, options={"wrap": "no"}, extensions={"probe"})
for i,(t,kids,ctxt,repl,rends) in enumerate(calls,1):
    print(f"pass {i}")
    print("   seam text :", repr(t).replace("\\x00","<WP>"))
    print("   children  :", kids)
    print("   context   :", ctxt, "| _replace available:", repl)
    print("   renderers :", rends, "...")
print("\noutput:", repr(out))
