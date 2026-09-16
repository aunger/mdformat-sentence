import re, difflib
SENT=re.compile(r'[.!?](?:["\'’”])?$')
def gaps(ls):
    w=[];b=set()
    for i,l in enumerate(ls):
        w+=l.split()
        if i<len(ls)-1: b.add(len(w))
    return w,b,[j for j in range(1,len(w)) if SENT.search(w[j-1])]
def cov(ls):
    w,b,e=gaps(ls); return (sum(1 for j in e if j in b)/len(e)) if e else 1.0
def rewrap(ls):
    w,_,_=gaps(ls); out=[];c=[]
    for x in w:
        c.append(x)
        if SENT.search(x): out.append(" ".join(c)); c=[]
    if c: out.append(" ".join(c))
    return out
def repair(ls):
    w,b,e=gaps(ls); keep=b|set(e); out=[];c=[]
    for i,x in enumerate(w):
        c.append(x)
        if i+1 in keep: out.append(" ".join(c)); c=[]
    if c: out.append(" ".join(c))
    return out
def apply(ls,k): return rewrap(ls) if cov(ls) < k else repair(ls)
def d(a,b): return sum(1 for x in difflib.unified_diff(a,b,lineterm="",n=0) if x[:1] in "+-" and x[:3] not in ("+++","---"))

# 12-line paragraph, clause-broken, 4 internal sentence ends, 2 of them covered -> cov .50
BASE=["Alpha one runs on,","and continues here,","and ends here. Beta two starts,",
      "and runs on,","and ends here.","Gamma three starts,","and runs on,",
      "and ends here. Delta four starts,","and runs on,","and continues,",
      "and runs further,","and ends here."]
print(f"paragraph: {len(BASE)} lines, coverage = {cov(BASE):.2f}\n")
for k in (0.4, 0.5, 0.6):
    before = apply(BASE,k)
    # the edit: author breaks ONE more sentence by hand, nudging coverage up one notch
    E=list(BASE); E[2]="and ends here."; E.insert(3,"Beta two starts,")
    after = apply(E,k)
    print(f"k={k}:  cov {cov(BASE):.2f} -> {cov(E):.2f}   "
          f"remedy {'REWRAP' if cov(BASE)<k else 'repair'} -> {'REWRAP' if cov(E)<k else 'repair'}"
          f"   diff from that one edit: {d(before,after):2d} lines")
