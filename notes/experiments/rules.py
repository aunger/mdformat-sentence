"""Classify every author line break in the corpus by which sembr rule put it
there: sentence end (4), clause punctuation (5), hyperlink or inline-markup
boundary (10, 11), or none of the above (6).

Produces the table in DESIGN.md 5.2. Breaks are classified by first match, so
the rows are disjoint by construction; the count at the end says how many of
them had a second claim on them, which is 2 here rather than 0.

The block-opener test excludes `[label]: url` definitions, NOT every line that
starts with `[`. See breaks.py for what the broader form cost.
"""
import os, re
CORPUS = os.path.join(os.path.dirname(__file__), '..', 'corpus', 'sembr.md')
SENT=re.compile(r'[.!?]["\'’”]?$'); CLAUSE=re.compile(r'[,;:—]$')
ME=re.compile(r'(\]\([^)]*\)|\]\[[^\]]*\]|>|`|[*_]{1,2})$'); MS=re.compile(r'^(\[|<|`|[*_]{1,2}\w)')
def paras(p):
    out,cur,f=[],[],False
    for l in open(p,encoding='utf-8'):
        s=l.rstrip('\n')
        if re.match(r'^\s*(```|~~~)',s): f=not f; continue
        if f or not s.strip() or re.match(r'^\s*(#|\||\[[^\]]*\]:|>|\d+\.|[-*+] |<)',s):
            if cur: out.append(cur); cur=[]
            continue
        cur.append(s)
    if cur: out.append(cur)
    return [x for x in out if len(x)>1]
c={'4':0,'5':0,'10/11':0,'6':0}; overlap=0
for p in paras(CORPUS):
    for i,l in enumerate(p[:-1]):
        raw=l.rstrip(); s=re.sub(r'`[^`]*`','X',raw).rstrip(); nxt=p[i+1].strip()
        markup = bool(ME.search(raw)) or bool(MS.match(nxt))
        if SENT.search(s):   c['4']+=1;  overlap += markup
        elif CLAUSE.search(s): c['5']+=1; overlap += markup
        elif markup:         c['10/11']+=1
        else:                c['6']+=1
t=sum(c.values())
print(f"total author line breaks: {t}")
for k in ('4','5','10/11','6'):
    print(f"  rule {k:5s}: {c[k]:3d}  ({100*c[k]/t:.0f}%)")
print(f"\n  breaks classified 4 or 5 that are ALSO at a markup boundary: {overlap}")
