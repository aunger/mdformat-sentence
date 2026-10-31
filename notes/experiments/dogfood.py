"""A rough stand-in for DESIGN.md section 6.2's dogfood row, until the plugin exists.

Needs markdown-it-py only, which mdformat installs.
Takes one or more Markdown files as arguments.

The plugin keeps a line break inside a paragraph only where it would break: at a sentence end
followed by a sentence opener. Every other authored break is joined. This program approximates
that decision for each soft break in each paragraph, so a writer can see which of their line breaks
the shipped default would join, before the plugin is there to run:
  - the line before must end in a terminator `.` `!` `?` `。` `！` `？`, after any closing quotes,
    brackets and emphasis markers and any footnote references; a terminator inside a code span
    does not count;
  - the line after must open, after any opening quotes, brackets and emphasis markers, with a
    capital, a digit, a camelCase word, a code span, an image or a tag, or with a word that matches
    the shipped rule `after = 'mdformat\\S*'`.
It knows no abbreviation, initial or line-start check, so it misses joins that sections 3.3 and 3.5
would make, and it looks only at breaks the author made, so it reports joins only, never a sentence
end inside a line that the plugin would split.

It prints, per file, one tuple for each break that would be joined: the line number, `no-end` or
`no-cap`, the end of the line before and the start of the line after; then the number of joins.
"""
import re
import sys

from markdown_it import MarkdownIt

CLOSE = set("\"'’”»›«‹“‘‟‛„」』》〉*_~])")
OPEN = set("\"'’”“‘‟‛«‹»›¿¡„‚「『《〈*_~[(\\")
TERM = set(".!?。！？")
NAMES = re.compile(r"mdformat\S*")


def ends_sentence(line):
    masked = re.sub(r"(`+)(.+?)\1", lambda m: "X" * len(m.group(0)), line)
    masked = re.sub(r"(\[\^[^\]\s]+\])+$", "", masked)
    j = len(masked) - 1
    while j >= 0 and masked[j] in CLOSE:
        j -= 1
    return j >= 0 and masked[j] in TERM


def opens_sentence(line):
    if line.startswith(("`", "![", "<")):
        return True
    w = line.lstrip("".join(OPEN))
    word = w.split(" ")[0]
    c = w[:1]
    return (bool(c) and (c.isdigit() or (c.isalpha() and not c.islower()))
            or bool(NAMES.fullmatch(re.sub(r"[,;:.!?)\]*_]+$", "", word)))
            or bool(re.match(r"[a-z]+[A-Z]", word)))


def joins(src):
    toks = MarkdownIt("commonmark").enable("table").parse(src)
    for i, t in enumerate(toks):
        if t.type != "inline" or i == 0 or toks[i - 1].type != "paragraph_open":
            continue
        lines = t.content.split("\n")
        first = toks[i - 1].map[0]
        for k in range(len(lines) - 1):
            a, b = lines[k].rstrip(), lines[k + 1].strip()
            end = ends_sentence(a)
            if not (end and opens_sentence(b)):
                yield first + k + 1, "no-cap" if end else "no-end", a[-50:], b[:40]


for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as f:
        found = list(joins(f.read()))
    print(path)
    for j in found:
        print(" ", j)
    print(f"  {len(found)} joins")
