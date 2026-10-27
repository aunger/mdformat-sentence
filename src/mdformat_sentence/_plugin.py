"""The module surface mdformat reads, the inline renderer and the canary.

Section numbers refer to `DESIGN.md`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mdformat.renderer import DEFAULT_RENDERERS, LOGGER, WRAP_POINT

if TYPE_CHECKING:
    import argparse

    from markdown_it import MarkdownIt
    from mdformat.renderer import RenderContext, RenderTreeNode

PLUGIN_ID = "sentence"

# Set in `context.env`, which markdown-it creates afresh for every render,
# so it resets per file with no state kept here.
_RAN = "mdformat_sentence.ran"

KEEP_WARNING = "mdformat-sentence does nothing under --wrap keep; use --wrap no"

CHANGES_AST = False


def update_mdit(mdit: MarkdownIt) -> None:
    """Do nothing: the plugin adds no syntax (section 2)."""


def add_cli_argument_group(group: argparse._ArgumentGroup) -> None:
    """Add this plugin's flags (section 2.4); section 4 defines them."""


def _render_inline(node: RenderTreeNode, context: RenderContext) -> str:
    """The `inline` renderer of section 2.2."""
    if node.parent is None or node.parent.type != "paragraph":
        return DEFAULT_RENDERERS["inline"](node, context)
    context.env[_RAN] = True
    text = DEFAULT_RENDERERS["inline"](node, context)
    if WRAP_POINT not in text:
        return text
    # Segmentation (section 3.1) and emission (section 3.4) decide the gaps here; until
    # they are built, the text goes back as mdformat rendered it.
    return text


def _canary(text: str, node: RenderTreeNode, context: RenderContext) -> str:
    """Once per render pass, report a lost `inline` slot (section 2.2), or warn
    that `--extensions` named the plugin under `--wrap keep` (section 2.5).

    Every read degrades to silence or a nameless message rather than
    raising.
    """
    try:
        ran = context.env.get(_RAN)
        if not context.do_wrap:
            ext = context.options["mdformat"].get("extensions")
            if ran and ext is not None and PLUGIN_ID in ext:
                LOGGER.warning(KEEP_WARNING)
            return text
        if ran:
            return text
        if not any(n.type == "paragraph" for n in node.walk()):
            return text
    except Exception:
        return text
    owner = _inline_owner(context)
    detail = (
        "paragraphs were rendered without its inline renderer"
        if owner is None
        else f"plugin {owner!r} owns the inline renderer"
    )
    LOGGER.warning(f"mdformat-sentence did not run: {detail}")
    return text


def _inline_owner(context: RenderContext) -> str | None:
    """Name the plugin mdformat kept as the `inline` renderer, if it can.

    The owner is the first loaded plugin whose renderer is the one
    `context.renderers` holds, so two plugins sharing one function
    cannot name the one that lost the conflict.
    """
    try:
        import mdformat.plugins

        renderer = context.renderers["inline"]
        if renderer is _render_inline:
            return None
        owner = next(
            plugin
            for plugin in context.options["parser_extension"]
            if plugin.RENDERERS.get("inline") is renderer
        )
        for plugin_id, plugin in mdformat.plugins.PARSER_EXTENSIONS.items():
            if plugin is owner:
                return str(plugin_id)
    except Exception:
        pass
    return None


RENDERERS = {"inline": _render_inline}
POSTPROCESSORS = {"root": _canary}
