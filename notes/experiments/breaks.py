"""The decisive measurement: what fraction of real sembr line breaks carry no
punctuation at all, and how many of those a break-word list could recover.

Produces the unpunctuated share and the break-word figures in DESIGN.md 5.2.
The scope is every paragraph, as markdown-it parses them (_corpus.py); pass
--top-level for the paragraphs outside lists and the blockquote only.

An earlier, line-based version of this script decided by hand which lines were
paragraph text. It skipped list-marker lines and the blockquote while keeping
the continuation lines under them, and kept lines inside <pre> blocks, so its
counts were of no well-defined scope. Before that, a still broader block-opener
test dropped every line starting with `[`, which deleted the prose lines that
open with a reference link, exactly the positions rules 10 and 11 describe.
Parsing removes both kinds of error: the scope is whatever markdown-it calls a
paragraph.
"""
import re, sys
from _corpus import breaks, paragraphs

TOP = '--top-level' in sys.argv
SENT = re.compile(r'[.!?]["\'’”]?$')
CLAUSE = re.compile(r'[,;:—]$')
CORE = "which who whom whose because although though unless since while whereas however therefore moreover furthermore nevertheless meanwhile when where whether until once".split()
EXT  = "and or but nor yet so for that if as after before then than".split()
ADMITTED = "because although though unless whereas whether if while who whom whose which when where".split()
# rules 10 and 11 break around hyperlinks and inline markup; those positions ARE
# matchable, unlike rule 6's dependent clauses. Measured separately below.
MARKUP_END   = re.compile(r'(\]\([^)]*\)|\]\[[^\]]*\]|>|`|[*_]{1,2})$')
MARKUP_START = re.compile(r'^(\[|<|`|[*_]{1,2}\w)')

unpunct, total = [], 0
for l, nxt_raw in breaks(TOP):
    s = re.sub(r'`[^`]*`', 'X', l).rstrip(); total += 1
    if SENT.search(s) or CLAUSE.search(s): continue
    nxt_raw = nxt_raw.strip()
    nxt = re.sub(r'[^\w\s]', '', nxt_raw).split()
    markup = bool(MARKUP_END.search(l.rstrip())) or bool(MARKUP_START.match(nxt_raw))
    unpunct.append((nxt[0].lower() if nxt else '', markup))

print(f"scope: {'top-level paragraphs' if TOP else 'all paragraphs'}")
print(f"author line breaks        : {total}")
print(f"  unpunctuated            : {len(unpunct)}  ({100*len(unpunct)/total:.0f}%)")
mk = sum(1 for _, m in unpunct if m)
print(f"    of those, at a link / code span / emphasis boundary (rules 10, 11): {mk}")
lines = [l for p in paragraphs(TOP) for l in p]
prose = "\n".join(lines)
refs = len(re.findall(r'\[[^\]]+\]\[[^\]]*\]', prose))
spans = len(re.findall(r'`[^`]+`', prose))
emph = len(re.findall(r'(?<![*_\w])([*_]{1,2})(?=\S)(.+?)(?<=\S)\1(?![*_\w])', prose))
opening = sum(1 for l in lines if l.lstrip().startswith("["))
print(f"      -> the corpus prose carries {refs} reference links, {spans} code spans and {emph}")
print(f"         emphasis runs across {len(lines)} lines, and {opening} of those lines open with")
print("         a link, so these are real rule 10/11 positions rather than an")
print("         absence of material. It still uses links lightly for a document")
print("         of its length, so treat the share, not the count, as the result.")
rest = [w for w, m in unpunct if not m]
print(f"\n  removing those leaves {len(rest)} breaks with no punctuation and no markup,")
print("  which is the row a break-word list is actually aimed at.")
print("\nrecovered by a break-word list (word following the break):")
for name, ws in (("core+extended (36)", CORE+EXT), ("admitted (14)", ADMITTED)):
    ws = set(ws)
    hu = sum(1 for w, _ in unpunct if w in ws)
    h6 = sum(1 for w in rest if w in ws)
    print(f"  {name:20s} unpunctuated {hu:3d}/{len(unpunct)}   no markup either {h6:3d}/{len(rest)}"
          f"   residual: {len(rest)-h6}/{total}"
          f" = {100*(len(rest)-h6)/total:.0f}% of all breaks still undetectable")
