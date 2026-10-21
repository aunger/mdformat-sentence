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

# Keys this plugin sets in `context.env`, which markdown-it creates afresh
# for every render, so each resets per file with no state kept here.
_RAN = "mdformat_sentence.ran"
_KEEP_CHECKED = "mdformat_sentence.keep_checked"

KEEP_WARNING = "mdformat-sentence does nothing under --wrap keep; use --wrap no"

CHANGES_AST = False


def update_mdit(mdit: MarkdownIt) -> None:
    """Do nothing: the plugin adds no syntax (§2)."""


def add_cli_argument_group(group: argparse._ArgumentGroup) -> None:
    """Add this plugin's flags (§2.4); §4 defines them."""


def _render_inline(node: RenderTreeNode, context: RenderContext) -> str:
    """The `inline` renderer of §2.2."""
    if node.parent is None or node.parent.type != "paragraph":
        return DEFAULT_RENDERERS["inline"](node, context)
    context.env[_RAN] = True
    if not context.do_wrap:
        _warn_if_named(context)
        return DEFAULT_RENDERERS["inline"](node, context)
    text = DEFAULT_RENDERERS["inline"](node, context)
    if WRAP_POINT not in text:
        return text
    # Segmentation (§3.1) and emission (§3.4) decide the gaps here; until
    # they are built, the text goes back as mdformat rendered it.
    return text


def _warn_if_named(context: RenderContext) -> None:
    """Warn once per render when `--extensions` names the plugin (§2.5).

    The latch is set on the first check, so later paragraphs skip it.
    """
    if context.env.get(_KEEP_CHECKED):
        return
    context.env[_KEEP_CHECKED] = True
    ext = context.options.get("mdformat", {}).get("extensions")
    if ext is not None and PLUGIN_ID in ext:
        LOGGER.warning(KEEP_WARNING)


def _canary(text: str, node: RenderTreeNode, context: RenderContext) -> str:
    """Report a lost `inline` slot once per render pass (§2.2).

    Every read degrades to silence or a nameless message rather than
    raising.
    """
    try:
        if context.env.get(_RAN) or not context.do_wrap:
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

    The owner is the plugin whose renderer `context.renderers` holds,
    rather than one found by re-deriving mdformat's conflict policy.
    """
    try:
        import mdformat.plugins

        renderer = context.renderers["inline"]
        if renderer is _render_inline:
            return None
        loaded = context.options["parser_extension"]
        for plugin_id, plugin in mdformat.plugins.PARSER_EXTENSIONS.items():
            if plugin in loaded and plugin.RENDERERS.get("inline") is renderer:
                return str(plugin_id)
    except Exception:
        pass
    return None


RENDERERS = {"inline": _render_inline}
POSTPROCESSORS = {"root": _canary}
