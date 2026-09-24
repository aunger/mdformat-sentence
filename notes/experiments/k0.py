import re, difflib
SENT=re.compile(r'[.!?](?:["\'’”])?$')
def gaps(ls):
    w=[];b=set()
    for i,l in enumerate(ls):
        w+=l.split()
        if i<len(ls)-1: b.add(len(w))
    return w,b,[j for j in range(1,len(w)) if SENT.search(w[j-1])]
def cov(ls):
    w,b,e=gaps(ls); return 1.0 if not e else sum(1 for j in e if j in b)/len(e)
def rewrap(ls):
    w,_,_=gaps(ls); o=[];c=[]
    for x in w:
        c.append(x)
        if SENT.search(x): o.append(" ".join(c)); c=[]
    return o+([" ".join(c)] if c else [])
def repair(ls):
    w,b,e=gaps(ls); k=b|set(e); o=[];c=[]
    for i,x in enumerate(w):
        c.append(x)
        if i+1 in k: o.append(" ".join(c)); c=[]
    return o+([" ".join(c)] if c else [])
def apply(ls): return rewrap(ls) if cov(ls)==0.0 else repair(ls)   # k = 0 strictly
def dl(a,b): return sum(1 for x in difflib.unified_diff(a,b,lineterm="",n=0) if x[:1] in "+-" and x[:3] not in ("+++","---"))

P=["Because the cascade picks by width,","an edit upstream can change which candidate wins,",
   "and cascade down the paragraph.","The tool reports success,","and the author sees a diff,",
   "which is the failure this design prevents."]          # 1 internal sentence end, covered
print(f"hand sembr, {len(P)} lines, internal sentence ends = {len(gaps(P)[2])}, coverage = {cov(P):.2f}")
print(f"  clean run: unchanged = {apply(P)==P}\n")

EDITS = {
 "A: append a sentence to a line (don't break it)":
   [*P[:2], "and cascade down the paragraph. Nobody notices at first.", *P[3:]],
 "B: join the two lines at the sentence boundary":
   ["Because the cascade picks by width,","an edit upstream can change which candidate wins,",
    "and cascade down the paragraph. The tool reports success,","and the author sees a diff,",
    "which is the failure this design prevents."],
}
for name,E in EDITS.items():
    out=apply(E)
    clause_before=sum(1 for l in P[:-1] if l.rstrip().endswith(","))
    clause_after=sum(1 for l in out[:-1] if l.rstrip().endswith(","))
    print(f"{name}")
    print(f"   coverage {cov(P):.2f} -> {cov(E):.2f}   branch = {'REWRAP' if cov(E)==0.0 else 'repair'}")
    print(f"   diff {dl(apply(P),out):2d} lines   clause breaks {clause_before} -> {clause_after}")
    for l in out: print("      |",l)
    print()
