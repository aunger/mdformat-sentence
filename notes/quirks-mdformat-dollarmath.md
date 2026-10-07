# Quirks: mdformat-dollarmath

A note, not a specification.
Behavior of mdformat-dollarmath that affects this design, or that may be worth an upstream issue.
Version 0.0.5, the newest release, with mdformat 1.0.0 and mdit-py-plugins 0.6.1; *verified* means run.
Nothing here has been filed.

______________________________________________________________________

## It declares an mdformat range that excludes 1.0

**Filing candidate.** *Verified* 2026-10-06.
Its metadata requires `mdformat<0.8.0,>=0.7.0`, so pip downgrades mdformat to 0.7.22 when it is installed next to mdformat 1.0.0, or refuses the combination.
Installed with `--no-deps`, it loads and runs under mdformat 1.0.0.
`DESIGN.md` §6.2 records this as a cost of the gate's environment.

## Escaped dollar signs lose their backslash

**Filing candidate.** *Verified* 2026-10-06, dollarmath alone, at `--wrap keep`.
`It costs \$5 and \$6 today.` formats to `It costs $5 and $6 today.`, which now parses as inline math between the two dollars, and the render changes.
With one dollar sign the output is still render-equal, `It costs $5 today.`, but a later edit adding a second would turn it into math.
This plugin does not change the outcome.

## Display math inside a paragraph becomes a block

**Compatibility note.** *Verified.*
`It holds. $$x$$ is positive.` is parsed as a paragraph, a math block and a paragraph, with or without this plugin, so `$$…$$` never reaches the plugin as inline text.
`MATH-AND-OPENERS.md` relies on this.
