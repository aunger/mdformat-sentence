"""The interface sentence detection consults for rules (sections 3.3
and 4), and a stub of it until the rules files are loaded.

Section numbers refer to `DESIGN.md`.
"""

from __future__ import annotations

import re
from typing import Protocol

from mdformat_sentence._detect import NBSP, OPENERS
from mdformat_sentence._verdicts import ALLOW, NO

__all__ = ["ALLOW", "NO", "STUB", "Rules"]


class Rules(Protocol):
    def verdict(self, at: str, before: str, after: str) -> str:
        """The decision list's verdict, `NO` or `ALLOW`, at a candidate gap
        after ATerm.

        It receives the raw words the keys of section 3.3 read: the word
        carrying the terminator, the word before it, or `""` where that
        word opens its paragraph part, and the word after the gap, each
        counted past any run of lone marks. Stripping is its own.
        """

    def lowercase_name(self, word: str) -> bool:
        """Whether `lowercase_names` lets `word`, the raw word after a
        candidate gap, pass the capital test."""


class Stub:
    """Rules standing in for the shipped default until it is loaded: no
    rule, and the default file's `lowercase_names = 'mdformat\\S*'`."""

    _skip = "".join(OPENERS | NBSP)
    _names = re.compile(r"mdformat\S*")

    def verdict(self, at: str, before: str, after: str) -> str:
        return ALLOW

    def lowercase_name(self, word: str) -> bool:
        # Only the leading strip can matter to a pattern ending in `\S*`.
        return self._names.fullmatch(word.lstrip(self._skip)) is not None


STUB = Stub()
