"""How `[plugin.sentence]` reaches the plugin: two claims from DESIGN.md §4, run.

1. mdformat validates only that `plugin` is a table of tables, so the nested
   `[[plugin.sentence.rule]]` and `[[plugin.sentence.rule.example]]` arrays
   reach the plugin intact; at the root of `.mdformat.toml` the same array
   is rejected, because the root allows only mdformat's own eight keys.
2. mdformat merges command-line plugin options over the config file's with a
   plain dict update (`opts["plugin"][plugin_id] |= plugin_opts`), so a flag
   whose `dest` is `include` replaces the config's `include` list outright,
   while a flag whose `dest` is `cli_include` leaves both lists in place.

A probe plugin registered as `sentence` captures the options it is handed.

Needs mdformat 1.0.0.
"""
import contextlib
import io
import os
import tempfile
import types

import mdformat.plugins as P
from mdformat._cli import run

SEEN = []


def pp(text, node, context):
    if node.parent is not None and node.parent.type == "paragraph":
        SEEN.append(dict(context.options["mdformat"]["plugin"].get("sentence", {})))
    return text


def add_cli_argument_group(group):
    group.add_argument("--sentence-include", dest="cli_include",
                       action="append", default=None)
    # The shape DESIGN.md §4 declines, kept here only to show why.
    group.add_argument("--sentence-include-replacing", dest="include",
                       action="append", default=None)


P.PARSER_EXTENSIONS["sentence"] = types.SimpleNamespace(
    CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS={"inline": pp},
    add_cli_argument_group=add_cli_argument_group, update_mdit=lambda m: None)

NESTED = """\
wrap = "no"

[plugin.sentence]
schema  = 1
include = ['team']

[[plugin.sentence.rule]]
at    = '(?i:dr)'
break = 'allow'

  [[plugin.sentence.rule.example]]
  input = '''
He lives on Elm Dr. Then he left.
'''
  output = '''
He lives on Elm Dr.
Then he left.
'''
"""

ROOT = """\
wrap = "no"

[[rule]]
at    = '(?i:dr)'
break = 'allow'
"""


def cli(toml, *args):
    """Run the CLI on a one-paragraph file beside this .mdformat.toml."""
    SEEN.clear()
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, ".mdformat.toml"), "w") as f:
            f.write(toml)
        md = os.path.join(d, "t.md")
        with open(md, "w") as f:
            f.write("One. Two.\n")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = run([*args, md], cache_toml=False)
    return code, err.getvalue().strip(), SEEN[0] if SEEN else None


print("1. nested arrays under [plugin.sentence] reach the plugin; at the root they are rejected\n")
code, err, opts = cli(NESTED)
print(f"   [plugin.sentence] with [[plugin.sentence.rule]]: exit {code}")
print(f"   the plugin was handed: {opts}\n")
code, err, opts = cli(ROOT)
print(f"   [[rule]] at the root: exit {code}")
print(f"   {' '.join(err.split())}\n")

print("2. a CLI flag merges over the config file's [plugin.sentence] by dict update\n")
code, err, opts = cli(NESTED, "--sentence-include", "lab")
print(f"   --sentence-include lab, dest cli_include: {opts}")
code, err, opts = cli(NESTED, "--sentence-include-replacing", "lab")
print(f"   --sentence-include-replacing lab, dest include: {opts}")
print("\n   Under its own key both lists survive; writing to `include` replaces the"
      "\n   config's list outright. That is why DESIGN.md §4's flag uses `cli_include`.")
