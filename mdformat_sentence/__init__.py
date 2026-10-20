"""An mdformat plugin that puts one sentence on each line."""

__version__ = "0.0.0"

from mdformat_sentence._plugin import (
    CHANGES_AST,
    POSTPROCESSORS,
    RENDERERS,
    add_cli_argument_group,
    update_mdit,
)

__all__ = [
    "CHANGES_AST",
    "POSTPROCESSORS",
    "RENDERERS",
    "add_cli_argument_group",
    "update_mdit",
]
