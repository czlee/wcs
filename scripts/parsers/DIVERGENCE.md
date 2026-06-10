# Vendored parsers — divergence from `~/who-woulda-won`

These files are copied from `~/who-woulda-won/core/` so this project doesn't
depend on that repo at runtime (mirroring how `scripts/download.py` already
inlined that repo's *discovery* logic). They are intended to be **near-verbatim**
copies so a future re-sync stays mechanical.

## What was changed when copying

1. **Imports rewritten** (every file): `core.models` → `.models`,
   `core.parsers` → `.` (the package), `core.parsers.base` → `.base`.

2. **`models.py`**: copied **only** the `Scoresheet` dataclass. The voting-only
   `Placement` and `VotingResult` models were omitted (not needed for extraction).

3. **`__init__.py`**: copied the parser registry (`register_parser`,
   `get_all_parsers`, `detect_parser`, `detect_parser_by_content`). Omitted
   `get_supported_url_formats` (user-facing help text, unused here).

4. **`base.py`, `scoring_dance.py`, `eepro.py`, `danceconvention.py`**: verbatim
   apart from the import rewrites above.

## What was NOT changed

No parser *logic* was edited. Project-specific behaviour — validation severity,
covariate normalisation, division-blob isolation, ID slugs, the `0`-placeholder
skip policy — lives entirely in `scripts/extract.py`, never in these files. Keep
it that way so these stay diffable against upstream.

## Source

`~/who-woulda-won/core/models.py` and
`~/who-woulda-won/core/parsers/{__init__,base,scoring_dance,eepro,danceconvention}.py`.
