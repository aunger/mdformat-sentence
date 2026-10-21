"""The root canary of §2.2."""

import logging
import types

import mdformat
import mdformat.plugins
from mdformat.renderer import DEFAULT_RENDERERS, RenderContext
import pytest

import mdformat_sentence

PARAGRAPHS = "It ended. Then it began.\n\nOne more.\n\nAnd another.\n"


@pytest.fixture
def owner(monkeypatch):
    """Register a plugin `owner` that also renders `inline` nodes."""
    plugin = types.SimpleNamespace(
        RENDERERS={"inline": DEFAULT_RENDERERS["inline"]},
        update_mdit=lambda mdit: None,
    )
    monkeypatch.setitem(mdformat.plugins.PARSER_EXTENSIONS, "owner", plugin)
    return plugin


def canary_messages(caplog):
    return [
        r.getMessage()
        for r in caplog.records
        if r.getMessage().startswith("mdformat-sentence did not run")
    ]


def render(md, wrap, extensions):
    return mdformat.text(md, options={"wrap": wrap}, extensions=extensions)


def test_reports_a_lost_slot_once_per_render_pass(owner, caplog):
    with caplog.at_level(logging.WARNING, logger="mdformat"):
        render(PARAGRAPHS, "no", ["owner", "sentence"])
    # `mdformat.text` renders twice when wrapping (§2.3).
    assert canary_messages(caplog) == [
        "mdformat-sentence did not run: plugin 'owner' owns the inline renderer"
    ] * 2


@pytest.mark.parametrize("wrap", ["no", 40])
def test_silent_when_the_plugin_owns_the_slot(owner, caplog, wrap):
    with caplog.at_level(logging.WARNING, logger="mdformat"):
        render(PARAGRAPHS, wrap, ["sentence"])
        render(PARAGRAPHS, wrap, ["sentence", "owner"])
    assert canary_messages(caplog) == []


def test_silent_under_keep(owner, caplog):
    with caplog.at_level(logging.WARNING, logger="mdformat"):
        render(PARAGRAPHS, "keep", ["owner", "sentence"])
    assert canary_messages(caplog) == []


def test_silent_when_no_paragraph_was_rendered(owner, caplog):
    with caplog.at_level(logging.WARNING, logger="mdformat"):
        render("# A heading. Only.\n", "no", ["owner", "sentence"])
    assert canary_messages(caplog) == []


def tree(md):
    from mdformat.renderer import RenderTreeNode
    from markdown_it import MarkdownIt

    return RenderTreeNode(MarkdownIt().parse(md))


def context(inline=DEFAULT_RENDERERS["inline"], **options):
    return RenderContext(
        {"inline": inline}, {}, {"mdformat": {"wrap": "no"}, **options}, {}
    )


canary = mdformat_sentence.POSTPROCESSORS["root"]


def test_an_unreadable_owner_gives_a_nameless_message(caplog):
    nameless = "mdformat-sentence did not run: paragraphs were rendered"
    unregistered = types.SimpleNamespace(
        RENDERERS={"inline": DEFAULT_RENDERERS["inline"]}
    )
    for ctx in (
        types.SimpleNamespace(env={}, options={}, do_wrap=True),
        context(),
        context(parser_extension=None),
        context(parser_extension=[object()]),
        context(parser_extension=[types.SimpleNamespace(RENDERERS={"inline": 0})]),
        context(parser_extension=[unregistered]),
        context(
            inline=mdformat_sentence.RENDERERS["inline"],
            parser_extension=[mdformat_sentence],
        ),
    ):
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger="mdformat"):
            assert canary("text", tree("A b.\n"), ctx) == "text"
        assert [m[: len(nameless)] for m in canary_messages(caplog)] == [nameless]


def test_an_unreadable_context_gives_silence(caplog):
    with caplog.at_level(logging.WARNING, logger="mdformat"):
        assert canary("text", tree("A b.\n"), object()) == "text"
        assert canary("text", object(), context()) == "text"
    assert canary_messages(caplog) == []
