#!/usr/bin/env python3
"""Generate Anki flashcard decks for country flags."""

import base64
import hashlib
import json
import sys
import time
from pathlib import Path

import cairosvg
import genanki
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CACHE_DIR = ROOT / "flags_cache"
OUTPUT_DIR = ROOT / "output"
FLAG_URL = "https://raw.githubusercontent.com/lipis/flag-icons/main/flags/4x3/{iso2}.svg"

CONTINENTS = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]

DECK_DISPLAY_NAMES = {
    **{c: f"Flags: {c}" for c in CONTINENTS},
    "World Cup 2026": "Flags: 2026 FIFA World Cup",
}


def _stable_id(name: str) -> int:
    digest = hashlib.sha256(f"anki-flags:{name}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def _note_guid(iso2: str) -> str:
    digest = hashlib.sha256(f"anki-flags:{iso2}".encode()).digest()
    return base64.urlsafe_b64encode(digest[:9]).decode().rstrip("=")


MODEL_ID = _stable_id("model:v2")
DECK_IDS = {c: _stable_id(f"deck:{c}") for c in CONTINENTS}
DECK_IDS["World Cup 2026"] = _stable_id("deck:World Cup 2026")

# Flag field stores the <img> tag so Anki's media scanner finds the reference
# inside the note itself, which is required for reliable media import on mobile.
FRONT_TMPL = '<div class="flag-card">{{Flag}}</div>'

BACK_TMPL = """\
{{FrontSide}}
<hr id="answer">
<div class="country-name">{{Country}}</div>"""

CSS = """\
.card {
  font-family: Arial, Helvetica, sans-serif;
  font-size: 20px;
  text-align: center;
  color: #1a1a1a;
  background-color: #ffffff;
  padding: 20px;
}
.flag-card img {
  max-width: 320px;
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.12);
}
.country-name {
  font-size: 28px;
  font-weight: bold;
  margin-top: 16px;
}
hr#answer {
  border: none;
  border-top: 1px solid #cccccc;
  margin: 20px auto;
  width: 60%;
}"""


def build_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "Country Flag",
        fields=[{"name": "Country"}, {"name": "Flag"}],
        templates=[{"name": "Flag → Country", "qfmt": FRONT_TMPL, "afmt": BACK_TMPL}],
        css=CSS,
    )


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def download_flags(
    countries: list[dict], session: requests.Session
) -> dict[str, Path]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    result: dict[str, Path] = {}
    for country in countries:
        iso2 = country["iso2"]
        local_path = CACHE_DIR / f"flag_{iso2}.png"
        if local_path.exists():
            result[iso2] = local_path
            continue
        url = FLAG_URL.format(iso2=iso2)
        try:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
            png = cairosvg.svg2png(bytestring=resp.content, output_width=320)
            local_path.write_bytes(png)
            result[iso2] = local_path
            time.sleep(0.05)
        except Exception as exc:
            print(
                f"WARNING: could not download flag for {country['name']} ({iso2}): {exc}",
                file=sys.stderr,
            )
    return result


def _make_tags(country: dict, is_wc_deck: bool) -> list[str]:
    continent = country["continent"].replace(" ", "_")
    tags = [f"continent::{continent}", f"region::{country['region']}"]
    if country.get("wc2026"):
        tags.append("world_cup::2026")
    if is_wc_deck and country.get("confederation"):
        tags.append(f"confederation::{country['confederation']}")
    return tags


def build_deck(
    label: str,
    countries: list[dict],
    flag_paths: dict[str, Path],
    model: genanki.Model,
    is_wc_deck: bool = False,
) -> tuple[genanki.Deck, list[str]]:
    deck = genanki.Deck(DECK_IDS[label], DECK_DISPLAY_NAMES[label])
    media_files: list[str] = []
    for country in countries:
        iso2 = country["iso2"]
        if iso2 not in flag_paths:
            continue
        img_tag = f'<img src="flag_{iso2}.png">'
        note = genanki.Note(
            model=model,
            fields=[country["name"], img_tag],
            tags=_make_tags(country, is_wc_deck),
        )
        note.guid = _note_guid(iso2)
        deck.add_note(note)
        media_files.append(str(flag_paths[iso2]))
    return deck, media_files


def save_package(deck: genanki.Deck, media_files: list[str], output_path: Path) -> None:
    pkg = genanki.Package(deck)
    pkg.media_files = media_files
    pkg.write_to_file(str(output_path))


def _slug(label: str) -> str:
    return label.lower().replace(" ", "-")


def main() -> None:
    countries = json.loads((DATA_DIR / "countries.json").read_text())
    model = build_model()
    session = make_session()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = sum(1 for c in countries if not c.get("fifa_only"))
    print(f"Loaded {len(countries)} entries ({total} continent cards + fifa_only entries)")

    for continent in CONTINENTS:
        subset = [c for c in countries if c["continent"] == continent and not c.get("fifa_only")]
        print(f"\n{continent}: {len(subset)} countries — downloading flags...", end="", flush=True)
        flag_paths = download_flags(subset, session)
        deck, media = build_deck(continent, subset, flag_paths, model)
        out = OUTPUT_DIR / f"flags-{_slug(continent)}.apkg"
        save_package(deck, media, out)
        print(f" {len(deck.notes)} cards → {out.name}")

    wc_countries = [c for c in countries if c.get("wc2026")]
    print(f"\nWorld Cup 2026: {len(wc_countries)} teams — downloading flags...", end="", flush=True)
    wc_flag_paths = download_flags(wc_countries, session)
    deck, media = build_deck("World Cup 2026", wc_countries, wc_flag_paths, model, is_wc_deck=True)
    out = OUTPUT_DIR / "flags-world-cup-2026.apkg"
    save_package(deck, media, out)
    print(f" {len(deck.notes)} cards → {out.name}")

    print("\nDone! .apkg files are in output/")


if __name__ == "__main__":
    main()
