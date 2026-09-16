import mdformat
# a paragraph a writer broke at clause level by hand, sembr style
SRC = ("Because the cascade picks by width,\n"
       "an edit upstream can change which candidate wins,\n"
       "and cascade down the paragraph. The next sentence starts here.\n")
for wrap in ("keep", "no"):
    print(f"--- wrap={wrap!r} (no plugin) ---")
    print(mdformat.text(SRC, options={"wrap": wrap}))
