# anki-flags

Generates Anki flashcard decks for the flags of every country.

## Decks

| File | Contents |
|---|---|
| `flags-africa.apkg` | 54 African nations |
| `flags-asia.apkg` | ~49 Asian nations |
| `flags-europe.apkg` | ~45 European nations |
| `flags-north-america.apkg` | ~24 North/Central American & Caribbean nations |
| `flags-south-america.apkg` | 12 South American nations |
| `flags-oceania.apkg` | 14 Oceanian nations |
| `flags-world-cup-2026.apkg` | 48 teams of the 2026 FIFA World Cup |

Each card shows a flag on the front; the country name is revealed on the back.

## Prerequisites

- Python 3.9+
- pip

## Usage

```bash
pip install -r requirements.txt
python generate.py
```

Flag images are downloaded from [flagcdn.com](https://flagcdn.com) on the first run and cached in `flags_cache/`. The seven `.apkg` files are written to `output/`.

Import any `.apkg` file into Anki via **File → Import**.

## Tags

Every card is tagged for flexible filtering inside Anki:

- `continent::Africa` / `continent::Europe` / etc.
- `region::Western_Africa` / `region::Southeast_Asia` / etc.
- `world_cup::2026` — all 48 World Cup 2026 teams
- `confederation::UEFA` / `confederation::CAF` / etc. — on World Cup cards

## Data

Country and World Cup data lives in `data/countries.json`. Edit that file and re-run `generate.py` to regenerate the decks.

## License

Apache 2.0
