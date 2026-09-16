"""The decisive measurement: what fraction of real sembr line breaks carry no
punctuation at all, and how many of those a break-word list could recover.

Produces the 42% figure. Paragraph extraction is line-based, not a markdown
parse, so counts are approximate to within a few paragraphs; the ratio is
stable across extractors (36/85 and 31/75 were measured under two variants).
"""
import os, re
CORPUS = os.path.join(os.path.dirname(__file__), '..', 'corpus', 'sembr.md')
SENT = re.compile(r'[.!?]["\'’”]?$')
CLAUSE = re.compile(r'[,;:—]$')
CORE = "which who whom whose because although though unless since while whereas however therefore moreover furthermore nevertheless meanwhile when where whether until once".split()
EXT  = "and or but nor yet so for that if as after before then than".split()
ADMITTED = "because although though unless whereas whether if while who whom whose which when where".split()

def paras(path):
    out, cur, fence = [], [], False
    for l in open(path, encoding='utf-8'):
        s = l.rstrip('\n')
        if re.match(r'^\s*(```|~~~)', s): fence = not fence; continue
        if fence or not s.strip() or re.match(r'^\s*(#|\||\[|>|\d+\.|[-*+] |<)', s):
            if cur: out.append(cur); cur = []
            continue
        cur.append(s)
    if cur: out.append(cur)
    return [p for p in out if len(p) > 1]

unpunct, total = [], 0
for p in paras(CORPUS):
    for i, l in enumerate(p[:-1]):
        s = re.sub(r'`[^`]*`', 'X', l).rstrip(); total += 1
        if SENT.search(s) or CLAUSE.search(s): continue
        nxt = re.sub(r'[^\w\s]', '', p[i+1].strip()).split()
        unpunct.append((s, nxt[0].lower() if nxt else ''))

print(f"author line breaks        : {total}")
print(f"  unpunctuated            : {len(unpunct)}  ({100*len(unpunct)/total:.0f}%)")
print("\nrecovered by a break-word list (word following the break):")
for name, ws in (("core+extended (36)", CORE+EXT), ("admitted (14)", ADMITTED)):
    h = sum(1 for _, w in unpunct if w in set(ws))
    print(f"  {name:20s} {h:3d}/{len(unpunct)}   residual: {len(unpunct)-h}/{total}"
          f" = {100*(len(unpunct)-h)/total:.0f}% of all breaks still undetectable")
