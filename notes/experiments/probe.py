import re, types, mdformat, mdformat.plugins as P
from mdformat.renderer import WRAP_POINT

seen = []
def inline_pp(text, node, context):
    if node.parent is not None and node.parent.type == "paragraph":
        seen.append(text)
    return text

probe = types.SimpleNamespace(
    CHANGES_AST=False,
    RENDERERS={},
    POSTPROCESSORS={"inline": inline_pp},
    add_cli_argument_group=lambda group: None,
    update_mdit=lambda mdit: None,
)
P.PARSER_EXTENSIONS  # materialise
P.PARSER_EXTENSIONS["probe"] = probe

SRC = ("First sentence here and it is quite long. Second sentence here.\n"
       "Already broken onto its own line. And a second one after it.\n")
print("SOURCE:", repr(SRC), "\n")
for wrap in ("keep", "no", 40):
    seen.clear()
    out = mdformat.text(SRC, options={"wrap": wrap}, extensions={"probe"})
    n = sum(s.count(WRAP_POINT) for s in seen)
    print(f"--- wrap={wrap!r} ---")
    print("  seam sees   :", " | ".join(repr(s).replace("\\x00","<WP>") for s in seen))
    print("  wrap points :", n)
    print("  output      :", repr(out))
    print()
