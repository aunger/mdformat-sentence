"""Can a plugin defeat `--wrap keep`, under which it is otherwise inert?

Three routes tried. Route B works through a supported hook and is two lines.
The section headed CONSEQUENCES is the reason DESIGN.md does not take it.

Needs mdformat 1.0.0.
"""
import types
import mdformat, mdformat.plugins as P
from mdformat.renderer import WRAP_POINT
import mdformat.renderer._context as C

SRC = ("Because the cascade picks by width,\n"
       "an edit upstream can change which candidate wins. The tool reports success.\n")
ENDS = lambda s: s.rstrip().endswith((".", "!", "?"))

def plugin(override_wrap):
    """A stand-in for the real plugin: breaks at sentence ends, pins the rest."""
    calls = []
    def pp(text, node, context):
        if node.parent is None or node.parent.type != "paragraph":
            return text
        calls.append(text)
        if WRAP_POINT not in text:
            return text
        segs = text.split(WRAP_POINT)
        out = [segs[0]]
        for s in segs[1:]:
            out.append("\n" if ENDS(out[-1]) else " ")
            out.append(s)
        return "".join(out)
    def update_mdit(mdit):
        if override_wrap:
            mdit.options["mdformat"]["wrap"] = "no"     # <- the whole trick
    return types.SimpleNamespace(
        CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS={"inline": pp},
        add_cli_argument_group=lambda g: None, update_mdit=update_mdit), calls

P.PARSER_EXTENSIONS
print("source:", repr(SRC), "\n")

for label, override in (("A  baseline: wrap=keep, no trick", False),
                        ("B  plugin sets mdit.options['mdformat']['wrap']='no'", True)):
    plug, calls = plugin(override)
    P.PARSER_EXTENSIONS["probe"] = plug
    out = mdformat.text(SRC, options={"wrap": "keep"}, extensions={"probe"})
    print(label)
    print(f"   seam calls      : {len(calls)}   (2 = mdformat's double render fired)")
    print(f"   wrap points seen: {sum(c.count(WRAP_POINT) for c in calls)}")
    print(f"   output          : {out!r}\n")

print("C  monkeypatch RenderContext.do_wrap -> True, leaving wrap_mode alone")
plug, _ = plugin(False); P.PARSER_EXTENSIONS["probe"] = plug
orig = C.RenderContext.do_wrap
C.RenderContext.do_wrap = property(lambda self: True)
try:
    mdformat.text(SRC, options={"wrap": "keep"}, extensions={"probe"})
    print("   unexpectedly succeeded\n")
except TypeError as e:
    print(f"   TypeError: {e}")
    print("   do_wrap and wrap_mode are read independently, so paragraph() hands")
    print("   textwrap the string 'keep' as a width. Patching one without the")
    print("   other does not work.\n")
finally:
    C.RenderContext.do_wrap = orig
print("   DEFAULT_RENDERERS is a", type(C.DEFAULT_RENDERERS).__name__,
      "- not assignable, so the renderer must be replaced via a plugin's own")
print("   RENDERERS mapping, which is the paragraph hook DESIGN.md 2.2 rejects.\n")

print("WHAT THE PLUGIN CAN AND CANNOT SEE ABOUT wrap\n")
import io, contextlib
seen = []
def spy(text, node, context):
    if node.parent is not None and node.parent.type == "paragraph":
        o = context.options.get("mdformat", {})
        seen.append(("wrap" in o, o.get("wrap", "<absent>"), o.get("extensions", "<absent>")))
    return text
P.PARSER_EXTENSIONS["probe"] = types.SimpleNamespace(
    CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS={"inline": spy},
    add_cli_argument_group=lambda g: None, update_mdit=lambda m: None)
def row(label):
    wrap_present, wrap_value, ext = seen[0]
    print(f"  {label}  'wrap' present={wrap_present!s:5}  value={wrap_value!r:8}"
          f"  options['mdformat']['extensions']={ext!r}")

for label, kw in (("API, no wrap given       ", {}),
                  ("API, wrap='keep' explicit", {"wrap": "keep"})):
    seen.clear(); mdformat.text(SRC, options=kw, extensions={"probe"})
    row(label)

import tempfile, os
from mdformat._cli import run
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "t.md")
    open(f, "w").write("One sentence. Two sentences.\n")
    for label, argv in (("CLI, no --extensions     ", [f]),
                        ("CLI, no --wrap           ", ["--extensions", "probe", f]),
                        ("CLI, --wrap keep         ", ["--extensions", "probe", "--wrap", "keep", f])):
        seen.clear()
        with contextlib.redirect_stdout(io.StringIO()): run(argv)
        row(label)

print("""
  So: explicit vs defaulted 'keep' is distinguishable through mdformat.text(),
  because build_mdit assigns the caller's dict with no defaults merged. It is
  NOT distinguishable through the CLI, because _cli.py:56 merges DEFAULT_OPTS
  first and argparse drops unset values. CI uses the CLI.

  'extensions' is a usable signal on the CLI and TOML paths, and ONLY there:
  DEFAULT_OPTS['extensions'] is None, so a non-None value means someone typed
  --extensions. Through mdformat.text() the argument goes straight to
  build_mdit and never lands in options['mdformat'] at all -- the rows above
  show '<absent>' -- so DESIGN.md 2.5's warning can never fire for a library
  caller, however explicitly they named the plugin.
""")

print("CONSEQUENCES of route B, all measured above or in _api.py:")
print("  1. The double render does not fire. _api.text decides on the CALLER's")
print("     options (_api.py:38), which still say 'keep', so the second pass that")
print("     DESIGN.md 2.3 relies on for idempotency is skipped.")
print("  2. Options are global to the render, so every other enabled plugin sees")
print("     wrap='no' too.")
print("  3. It silently overrides an explicit user instruction, and --check will")
print("     then report the file as unformatted to someone who asked for no wrap.")
