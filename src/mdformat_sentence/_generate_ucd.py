"""Generate `_ucd.py` from the vendored `unicode/SentenceBreakProperty.txt`
(section 3.3).

Run `python -m mdformat_sentence._generate_ucd` after replacing the
vendored file; a test regenerates and diffs, so the two cannot drift.

Section numbers refer to `DESIGN.md`.
"""

from __future__ import annotations

from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "unicode" / "SentenceBreakProperty.txt"
TARGET = HERE / "_ucd.py"

# The Sentence_Break values that section 3.3 names as `$` classes, in its
# order.
VALUES = (
    "Upper",
    "Lower",
    "OLetter",
    "Numeric",
    "Extend",
    "STerm",
    "ATerm",
    "SContinue",
    "Close",
)

_LINE = re.compile(r"([0-9A-F]{4,6})(?:\.\.([0-9A-F]{4,6}))?\s*;\s*(\w+)")
_VERSION = re.compile(r"# SentenceBreakProperty-([0-9.]+)\.txt")


def generate(source: str) -> str:
    """The text of `_ucd.py` for the contents of a SentenceBreakProperty file."""
    version = _VERSION.match(source)
    if version is None:
        raise ValueError("not a SentenceBreakProperty file")
    listed: dict[str, list[tuple[int, int]]] = {value: [] for value in VALUES}
    for line in source.splitlines():
        match = _LINE.match(line)
        if match is not None and match[3] in listed:
            first = int(match[1], 16)
            listed[match[3]].append((first, int(match[2] or match[1], 16)))
    ranges: dict[str, list[list[int]]] = {value: [] for value in VALUES}
    for value, pairs in listed.items():
        merged = ranges[value]
        # The file splits a value's ranges by general category, so adjacent
        # ones are merged, in code point order whatever order it lists them.
        for first, last in sorted(pairs):
            if merged and merged[-1][1] + 1 == first:
                merged[-1][1] = last
            else:
                merged.append([first, last])
    out = [
        f'"""Sentence_Break ranges from UCD {version[1]}, generated from',
        "`unicode/SentenceBreakProperty.txt` by `_generate_ucd.py`; do not edit.",
        "",
        "The data is © Unicode, Inc., under the Unicode License v3 in",
        "`unicode/LICENSE.txt`.",
        '"""',
        "",
        f'VERSION = "{version[1]}"',
    ]
    for value in VALUES:
        out += ["", f"{value.upper()} = ("]
        out += [f"    (0x{first:04X}, 0x{last:04X})," for first, last in ranges[value]]
        out.append(")")
    return "\n".join(out) + "\n"


def main() -> None:
    TARGET.write_text(generate(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")


if __name__ == "__main__":
    main()
