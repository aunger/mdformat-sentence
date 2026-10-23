"""Classify every author line break in the corpus by which sembr provision put it
there: sentence end (4), clause punctuation (5), hyperlink or inline-markup
boundary (10, 11), or none of the above.

Produces the table in DESIGN.md 5.2. Breaks are classified by first match, so
the rows are disjoint by construction; the count after the table says how many
of them had a second claim on them. The last row is every break with no
punctuation and no markup at it, of which provision 6's dependent clauses are only a
part, so it carries no provision number.

The scope is every paragraph, as markdown-it parses them (_corpus.py); pass
--top-level for the paragraphs outside lists and the blockquote only.

It also counts what a naive provision 5 would do, for DESIGN.md 5.1: every clause
mark followed by whitespace, split by whether the author broke the line there.
Marks at a line end are the breaks a provision 5 would find; marks mid-line are
positions it would break at where the author did not.
"""
import re, sys
from _corpus import breaks, paragraphs

TOP = '--top-level' in sys.argv
SENT = re.compile(r'[.!?]["\'’”]?$'); CLAUSE = re.compile(r'[,;:—]$')
ME = re.compile(r'(\]\([^)]*\)|\]\[[^\]]*\]|>|`|[*_]{1,2})$'); MS = re.compile(r'^(\[|<|`|[*_]{1,2}\w)')
mask = lambda s: re.sub(r'`[^`]*`', 'X', s).rstrip()

c = {'4': 0, '5': 0, '10/11': 0, 'none': 0}; overlap = 0
for line, nxt in breaks(TOP):
    raw = line.rstrip(); s = mask(raw); nxt = nxt.strip()
    markup = bool(ME.search(raw)) or bool(MS.match(nxt))
    if SENT.search(s):     c['4'] += 1;  overlap += markup
    elif CLAUSE.search(s): c['5'] += 1;  overlap += markup
    elif markup:           c['10/11'] += 1
    else:                  c['none'] += 1
t = sum(c.values())
print(f"scope: {'top-level paragraphs' if TOP else 'all paragraphs'}")
print(f"total author line breaks: {t}")
for k in c:
    print(f"  rule {k:5s}: {c[k]:3d}  ({100*c[k]/t:.1f}%)")
print(f"\n  breaks classified 4 or 5 that are ALSO at a markup boundary: {overlap}")

end = mid = 0
for p in paragraphs(TOP):
    for i, l in enumerate(p):
        s = mask(l)
        mid += len(re.findall(r'[,;:—](?=\s)', s))
        end += bool(CLAUSE.search(s)) and i < len(p) - 1
print(f"\nclause marks followed by whitespace: {end} at an author break, {mid} mid-line")
print(f"  a naive rule 5 breaks at {end + mid}, of which {mid} ({100*mid/(end+mid):.0f}%) the author did not")
