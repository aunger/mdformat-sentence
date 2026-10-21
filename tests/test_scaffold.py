"""Packaging, the module surface and the inline renderer's guards (§2, §2.2)."""

import mdformat
import mdformat.plugins

import mdformat_sentence


def test_entry_point_loads_the_module():
    assert mdformat.plugins.PARSER_EXTENSIONS["sentence"] is mdformat_sentence


def test_module_surface():
    assert set(mdformat_sentence.RENDERERS) == {"inline"}
    assert set(mdformat_sentence.POSTPROCESSORS) == {"root"}
    assert mdformat_sentence.CHANGES_AST is False
    assert callable(mdformat_sentence.update_mdit)
    assert callable(mdformat_sentence.add_cli_argument_group)


def baseline(md, wrap, extensions=()):
    return mdformat.text(md, options={"wrap": wrap}, extensions=[*extensions])


def plugin(md, wrap, extensions=()):
    return mdformat.text(
        md, options={"wrap": wrap}, extensions=[*extensions, "sentence"]
    )


def test_headings_and_table_cells_are_left_as_mdformat_renders_them():
    heading = "# It ended. Then it began.\n"
    table = "| It ended. Then it began. |\n| -- |\n| a |\n"
    for wrap in ("keep", "no", 20):
        assert plugin(heading, wrap) == baseline(heading, wrap)
        assert plugin(table, wrap, ["gfm"]) == baseline(table, wrap, ["gfm"])


def test_inert_under_keep():
    md = (
        "It ended.\nThen it began. Again.\n\n"
        "- It ended. Then it began.\n\n> It ended.\n> Then it began.\n"
    )
    assert plugin(md, "keep") == baseline(md, "keep")


def test_a_paragraph_with_no_wrap_point_is_unchanged():
    md = "Ended.\n"
    for wrap in ("keep", "no", 20):
        assert plugin(md, wrap) == baseline(md, wrap)
