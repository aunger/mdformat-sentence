"""Shared by rules.py and breaks.py: the author line breaks of corpus/sembr.md.

The corpus is parsed with markdown-it (the `commonmark` preset plus `table`,
which is what mdformat-gfm adds and what the pipe table at the end needs; without
it that table parses as a paragraph). Every paragraph is in scope, including those
inside list items and the blockquote, because the rule list is the specification's
own prose. A break is a newline inside one paragraph's inline content, so nothing
inside a code block, an HTML block, a table or a heading is ever counted.

`top_level=True` keeps only paragraphs that are direct children of the document,
for comparison: it is the narrower scope a line-based extractor approximated.
"""
import os
from markdown_it import MarkdownIt

CORPUS = os.path.join(os.path.dirname(__file__), '..', 'corpus', 'sembr.md')


def paragraphs(top_level=False):
    """Each paragraph's lines, as markdown-it gives its inline content."""
    md = MarkdownIt('commonmark').enable('table')
    tokens = md.parse(open(CORPUS, encoding='utf-8').read())
    out = []
    for i, t in enumerate(tokens):
        if t.type != 'paragraph_open' or (top_level and t.level != 0):
            continue
        out.append(tokens[i + 1].content.split('\n'))
    return out


def breaks(top_level=False):
    """(line before the break, line after it), for every author break."""
    return [(p[i], p[i + 1]) for p in paragraphs(top_level) for i in range(len(p) - 1)]
