# Site copy

All the non-trivial wording on the site, extracted for editing. Edit these files freely and tell Claude to
incorporate them back into the site. Each file says where its text lives in the code, so edits map back mechanically.

| File | What's in it |
|---|---|
| `metric-descriptions.md` | The short "What it measures" / "Caveats for this metric" panels under the graph, for all 11 metrics (+ metric names and family titles) |
| `worked-squared.md` | Long description of the working for Kendall's W, mean Spearman ρ, standard deviation of ranks |
| `worked-gaps.md` | Long description for Spearman footrule, mean absolute deviation |
| `worked-head-to-head.md` | Long description for the two Kendall τ metrics |
| `worked-top-n.md` | Long description for the overlap / Jaccard @ 3 metrics (with and without chance correction) |
| `dialog-about.md` | The "About" dialog |
| `dialog-limitations.md` | The limitations dialog |
| `dialog-working.md` | The frame of the "How is this calculated?" dialog around the worked text |
| `dialog-profile.md` | The scoresheet profile dialog |
| `interface.md` | Everything else: page title, banner, footer, top bar, filters, chart captions, tooltips, percentile wording, scoresheet picker |

## Conventions used in these files

- `{m}`, `{n}`, `{W}` etc. in curly braces are **values filled in per scoresheet** (m = number of judges,
  n = number of competitors). Keep them where they are, or move them within the sentence.
- `$...$` is inline TeX, `$$...$$` is display TeX (rendered with KaTeX). Where a formula has numbers substituted
  in, I've shown the general form only, with a note like *(numbers substituted for this scoresheet)*. The
  substituted versions are generated; edit the general form and tell Claude if the substitution should change.
- `[[metric_key|link text]]` is a link that switches to that metric.
- `[text]{tip: ...}` is a term with a hover/tap tooltip.
- `**bold**`, `*italic*` are as in the site.
- `<!-- ... -->` are notes to you about context (where it appears, when it's shown). They are not site text.
- Text under a heading like "Shown when ..." only appears in that situation.
- Metric descriptions are **plain text** apart from the `[[...]]` links (no TeX); the worked files have the formulas.
