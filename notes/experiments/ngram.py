import json, re, time, urllib.parse, urllib.request, statistics
URL="https://books.google.com/ngrams/json"
def q(c,y0=1990,y1=2019):
    p=urllib.parse.urlencode({"content":c,"year_start":y0,"year_end":y1,"corpus":"en-2019","smoothing":3})
    with urllib.request.urlopen(f"{URL}?{p}",timeout=45) as r: return json.load(r)
def series(c):
    try: d=q(c)
    except Exception: return {}
    return {e["ngram"]: statistics.mean(e["timeseries"]) for e in d
            if e.get("type")!="NGRAM_COLLECTION" and e.get("timeseries")}
def digit_share(tok):
    """Of the top continuations of '<tok>', what share are numerals?"""
    s = series(f"{tok} *")
    if not s: return None, ""
    tot = sum(s.values()) or 1
    dig = sum(v for k,v in s.items() if re.fullmatch(re.escape(tok)+r" (\d+|[IVXLCDM]{1,4})", k))
    top = ", ".join(k.split(" ",1)[1] for k,_ in sorted(s.items(), key=lambda x:-x[1])[:5])
    return 100*dig/tot, top
def noun_use(tok):
    """'a X' + 'the X' -- only a count noun takes these."""
    s = series(f"a {tok}"); s.update(series(f"the {tok}"))
    return sum(s.values())

print(f"{'token':6s} {'followed by a number':>21s}   {'used as a noun':>14s}   top continuations")
for tok in ["Fig","fig","No","no","Vol","Ch","Sec","sec","vs","St","Dr","al"]:
    d, top = digit_share(tok); time.sleep(1.2)
    n = noun_use(tok); time.sleep(1.2)
    ds = f"{d:.0f}%" if d is not None else "n/a"
    print(f"{tok:6s} {ds:>21s}   {n:14.2e}   {top[:46]}")
