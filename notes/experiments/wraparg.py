"""Four facts about `wrap` as an *argument*, as opposed to `wrap` at the seam.

1. TOML validation is a separate gate from CLI validation, and they disagree.
2. `--wrap sentence` is rejected by argparse today, which is the fail-loud
   property that makes it worth asking for upstream.
3. mdformat.renderer.LOGGER has no handler of its own, so a warning raised
   outside the CLI's first pass is printed by logging.lastResort, not swallowed.
4. A warning raised at the inline seam fires once per paragraph per pass.

Needs mdformat 1.0.0.
"""
import contextlib, io, logging, os, sys, tempfile, types
from pathlib import Path

import mdformat, mdformat.plugins as P
from mdformat._cli import run, validate_wrap_arg
from mdformat._conf import InvalidConfError, read_toml_opts
from mdformat.renderer import LOGGER

print("1. the two validators disagree about `wrap`\n")
print(f"   {'value':<12} {'--wrap (CLI)':<34} .mdformat.toml")
for lit, txt in (('"keep"', "keep"), ('"no"', "no"), ('"sentence"', "sentence"),
                 ("1", "1"), ("2", "2"), ("80", "80")):
    try:
        cli = repr(validate_wrap_arg(txt))
    except ValueError as e:
        cli = f"ValueError: {e}"
    with tempfile.TemporaryDirectory() as d:
        Path(d, ".mdformat.toml").write_text(f"wrap = {lit}\n")
        try:
            toml = repr(read_toml_opts.__wrapped__(Path(d))[0]["wrap"])
        except InvalidConfError:
            toml = "InvalidConfError"
    print(f"   {lit:<12} {cli:<34} {toml}")
print("\n   `--wrap 1` is accepted and `wrap = 1` is not: _cli.py:193 tests"
      "\n   `width < 1`, _conf.py:60 tests `wrap_value > 1`. Pre-existing, ours"
      "\n   only in that it shows the two gates are genuinely separate code.\n")

print("2. `--wrap sentence` today\n")
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "t.md"); open(f, "w").write("One. Two.\n")
    try:
        with contextlib.redirect_stderr(io.StringIO()) as err:
            run(["--wrap", "sentence", f])
        print("   returned without SystemExit (unexpected)")
    except SystemExit as e:
        print(f"   SystemExit({e.code}): {err.getvalue().strip().splitlines()[-1]}")
print("   Rejected at argument parsing, before a file is read. That is the"
      "\n   property `--wrap no` does not have.\n")

print("3. where a renderer warning goes\n")
print(f"   LOGGER.handlers  = {LOGGER.handlers}")
print(f"   LOGGER.propagate = {LOGGER.propagate}")
print(f"   logging.lastResort = {logging.lastResort} at "
      f"{logging.getLevelName(logging.lastResort.level)}")
saved, logging.lastResort = logging.lastResort, None
buf = io.StringIO()
with contextlib.redirect_stderr(buf):
    LOGGER.warning("probe")
logging.lastResort = saved
print(f"   with lastResort disabled, stderr = {buf.getvalue()!r}")
print("   -> lastResort is what prints it. An mdformat.text() caller DOES see"
      "\n   the message on stderr, unprefixed, without configuring logging.\n")

calls = []
def warner(text, node, context):
    if node.parent is not None and node.parent.type == "paragraph":
        calls.append(text)
        LOGGER.warning("does nothing under --wrap keep")
    return text
P.PARSER_EXTENSIONS
P.PARSER_EXTENSIONS["probe"] = types.SimpleNamespace(
    CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS={"inline": warner},
    add_cli_argument_group=lambda g: None, update_mdit=lambda m: None)

SRC = "Alpha one.\n\nBeta two.\n\n- Gamma three.\n"
print("4. how loud is the warning\n")
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "t.md"); open(f, "w").write(SRC)
    for label, argv in (("CLI, --wrap keep (one pass) ", ["--extensions", "probe", f]),
                        ("CLI, --wrap no  (two passes)", ["--extensions", "probe", "--wrap", "no", f])):
        calls.clear()
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()) as err:
            run(argv)
        text = err.getvalue()
        print(f"   {label}: seam calls {len(calls)}, "
              f"lines on stderr {len(text.splitlines())}, "
              f"with the CLI prefix {text.count('Warning:')}")
print("\n   Three paragraphs, three warnings: it fires per paragraph, not per"
      "\n   document. Under `--wrap no` the second pass doubles that, and those"
      "\n   copies miss the `Warning: ` prefix because _cli.py:137 applies the"
      "\n   handler to the first pass only (_api.py:26).")
