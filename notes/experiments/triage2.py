import re, textwrap, os
CORPUS = os.path.join(os.path.dirname(__file__), '..', 'corpus', 'sembr.md')
SENT = re.compile(r'[.!?](?:["\'’”])?$')

def paras(path):
    out=[];cur=[];fence=False
    for l in open(path,encoding='utf-8'):
        s=l.rstrip('\n')
        if re.match(r'^\s*(```|~~~)',s): fence=not fence; continue
        if fence or not s.strip() or re.match(r'^\s*(#|\||\[|>|\d+\.|[-*+] |<)',s):
            if cur: out.append(cur); cur=[]
            continue
        cur.append(s)
    if cur: out.append(cur)
    return [p for p in out if len(p)>1]

def coverage(lines):
    """fraction of internal sentence ends that are followed by a line break"""
    words=[]; brk=set()
    for i,l in enumerate(lines):
        w=re.sub(r'`[^`]*`','X',l).split()
        words+=w
        if i<len(lines)-1: brk.add(len(words))     # gap index after this line
    ends=[j for j in range(1,len(words)) if SENT.search(words[j-1])]
    if not ends: return None, 0
    return sum(1 for j in ends if j in brk)/len(ends), len(ends)

print("coverage = internal sentence ends that ARE followed by a line break\n")
real=[c for c,_ in (coverage(p) for p in paras(CORPUS)) if c is not None]
print(f"real hand-written sembr   n={len(real):3d}   min={min(real):.2f}  "
      f"median={sorted(real)[len(real)//2]:.2f}  max={max(real):.2f}   "
      f"at 1.00: {sum(1 for c in real if c==1.0)}/{len(real)}")

for width in (62,72,80):
    hw=[]
    for p in paras(CORPUS):
        text=" ".join(" ".join(p).split())
        c,n = coverage(textwrap.wrap(text,width))
        if c is not None: hw.append(c)
    print(f"same text hard-wrapped@{width} n={len(hw):3d}   min={min(hw):.2f}  "
          f"median={sorted(hw)[len(hw)//2]:.2f}  max={max(hw):.2f}   "
          f"at 1.00: {sum(1 for c in hw if c==1.0)}/{len(hw)}")
