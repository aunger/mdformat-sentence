import json, re, urllib.request
names = ["mdformat","mdformat-admon","mdformat-beautysh","mdformat-black","mdformat-config",
"mdformat-deflist","mdformat-footnote","mdformat-frontmatter","mdformat-gfm","mdformat-gfm-alerts",
"mdformat-gofmt","mdformat-mkdocs","mdformat-myst","mdformat-pyproject","mdformat-ruff",
"mdformat-rustfmt","mdformat-shfmt","mdformat-simple-breaks","mdformat-toc","mdformat-web"]
non_mit = []
for n in names:
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{n}/json", timeout=20) as r:
            i = json.load(r)["info"]
    except Exception as e:
        print(f"{n:24s} FETCH FAILED {e}"); continue
    lic = re.sub(r"\s+", " ", (i.get("license_expression") or i.get("license") or "").strip())
    cls = [c.split("::")[-1].strip() for c in i.get("classifiers", []) if c.startswith("License")]
    verdict = "MIT" if ("MIT" in lic.upper() or any("MIT" in c.upper() for c in cls)) else "NOT-MIT/UNKNOWN"
    if verdict != "MIT": non_mit.append(n)
    print(f"{n:24s} {verdict:16s} field={lic[:34] or '(none)':36s} classifier={'; '.join(cls) or '(none)'}")
print("\nnot clearly MIT:", non_mit or "none")
