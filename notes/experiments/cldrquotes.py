"""Which quotation marks open, and which close, in CLDR's locale data.

Downloads cldr-misc-full 48.2.0 from the npm registry (network), reads every
locale's delimiters.json, and prints each quotation character with the roles
CLDR gives it. The JSON is resolved, so a locale that sets nothing inherits
root's “…” and ‘…’; that inflates the counts but cannot change a role.

Stdlib only. Establishes the CLDR half of DESIGN.md §3.3's claim about the
corner brackets, and that CLDR gives 《 》 〈 〉 ‟ ‛ no quotation role at all.
"""
import io
import json
import tarfile
import unicodedata
import urllib.request
from collections import defaultdict

URL = "https://registry.npmjs.org/cldr-misc-full/-/cldr-misc-full-48.2.0.tgz"
FIELDS = {
    "quotationStart": "open",
    "alternateQuotationStart": "open",
    "quotationEnd": "close",
    "alternateQuotationEnd": "close",
}

with urllib.request.urlopen(URL, timeout=60) as r:
    tgz = tarfile.open(fileobj=io.BytesIO(r.read()), mode="r:gz")

roles = defaultdict(lambda: defaultdict(set))  # char -> role -> locales
locales = 0
for member in tgz.getmembers():
    if not member.name.endswith("/delimiters.json"):
        continue
    locales += 1
    (loc, body), = json.load(tgz.extractfile(member))["main"].items()
    for field, role in FIELDS.items():
        for ch in body["delimiters"][field]:
            roles[ch][role].add(loc)

print(f"cldr-misc-full 48.2.0: {locales} locales\n")
print(f"{'':3}{'code':8}{'gc':4}{'opens in':>9}{'closes in':>11}  verdict")
for ch in sorted(roles, key=ord):
    o, c = len(roles[ch]["open"]), len(roles[ch]["close"])
    verdict = "both" if o and c else "open only" if o else "close only"
    print(f"{ch:3}U+{ord(ch):04X}  {unicodedata.category(ch):4}{o:>9}{c:>11}  {verdict}")

absent = [ch for ch in "《》〈〉‟‛" if ch not in roles]
print("\nnever a quotation delimiter in any locale:", " ".join(absent) or "none")
