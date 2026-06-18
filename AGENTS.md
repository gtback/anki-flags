# AGENTS.md

Guidelines for AI agents working in this repository.

## Project overview

Generates Anki `.apkg` flashcard decks for country flags using Python + genanki.

## Entry point

```bash
pip install -r requirements.txt
python generate.py
```

Outputs 7 `.apkg` files to `output/`. Flag images are downloaded to `flags_cache/` on first run (gitignored).

## Key files

| File | Purpose |
|---|---|
| `generate.py` | Main script — all logic for downloading flags and building decks |
| `data/countries.json` | Source of truth for country data |
| `requirements.txt` | Python dependencies: genanki, requests |

## Modifying country data

- Add/remove countries: edit `data/countries.json`, then re-run `generate.py`.
- Update World Cup 2026 teams: flip the `wc2026` boolean in the relevant entries.
- Each entry must have: `name`, `iso2` (flagcdn.com code, lowercase), `continent`, `region`.
- Optional fields: `wc2026` (bool), `confederation` (string), `fifa_only` (bool).
- `fifa_only: true` entries appear only in the World Cup deck, not in continent decks. Use this for football associations that share a flag with another country entry (e.g. England / United Kingdom).

## Stable IDs

Deck IDs and model IDs are derived with `_stable_id()` (sha256 hash of a namespaced string). The model key is `"model:v1"` — bump to `"model:v2"` only if the field schema changes in a way that would break existing Anki imports.

Note GUIDs are `_note_guid(iso2)` — stable per ISO code. Changing a country's display name will update existing Anki cards without creating duplicates.

## Testing

There are no automated tests. Verify by:

1. Running `python generate.py` and checking the output for warnings.
2. Importing an `.apkg` into Anki and spot-checking cards.
3. Confirming World Cup deck has 48 cards and each continent deck count matches `data/countries.json`.
