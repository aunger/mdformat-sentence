import re, difflib
SENT=re.compile(r'[.!?](?:["\'’”])?$')

P = ["Because the cascade picks by width,",
     "an edit upstream can change which candidate wins,",
     "and cascade down the paragraph.",
     "The tool then reports success,",
     "and the author sees a diff they did not ask for,",
     "which is the failure this design exists to prevent.",
     "A short closing sentence follows."]

def gaps(lines):
    words=[];brk=set()
    for i,l in enumerate(lines):
        words+=l.split()
        if i<len(lines)-1: brk.add(len(words))
    ends=[j for j in range(1,len(words)) if SENT.search(words[j-1])]
    return words,brk,ends

def triage(lines):
    w,brk,ends=gaps(lines)
    if all(j in brk for j in ends): return lines           # PRESERVE
    out,cur=[],[]                                          # REWRAP sentence-per-line
    for i,x in enumerate(w):
        cur.append(x)
        if SENT.search(x): out.append(" ".join(cur)); cur=[]
    if cur: out.append(" ".join(cur))
    return out

def repair(lines):
    """same detector, minimal remedy: add only the missing sentence breaks"""
    w,brk,ends=gaps(lines)
    keep=brk|set(ends)
    out,cur=[],[]
    for i,x in enumerate(w):
        cur.append(x)
        if i+1 in keep: out.append(" ".join(cur)); cur=[]
    if cur: out.append(" ".join(cur))
    return out

# the edit: author appends a sentence to line 3 without breaking it
E=list(P); E[2]="and cascade down the paragraph. They rarely notice at first."

def diff(a,b): return sum(1 for d in difflib.unified_diff(a,b,lineterm="",n=0) if d[:1] in "+-" and d[:3] not in ("+++","---"))

for name,f in (("triage (rewrap whole para)",triage),("repair (add missing break)",repair)):
    before,after=f(P),f(E)
    print(f"=== {name} ===")
    print(f"  clean paragraph unchanged : {before==P}")
    print(f"  idempotent                : {f(after)==after}")
    print(f"  diff lines from the edit  : {diff(before,after)}")
    print("  output after the edit:")
    for l in after: print("    |",l)
    print()
print("clause breaks surviving the edit:  triage",
      sum(1 for l in triage(E)[:-1] if l.rstrip().endswith(",")),
      " repair", sum(1 for l in repair(E)[:-1] if l.rstrip().endswith(",")),
      f" (original had {sum(1 for l in P[:-1] if l.rstrip().endswith(','))})")
