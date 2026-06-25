"""Rate library loader/saver for GI Cost Calculator."""
import json
from pathlib import Path

RATES_DIR = Path(__file__).parent.parent / "data"


def load_rates(region: str = "uae") -> dict:
    """Load the rate library for a given region."""
    path = RATES_DIR / f"rates_{region.lower()}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_rates(rates: dict, region: str = "uae") -> None:
    """Persist an edited rate library back to disk."""
    path = RATES_DIR / f"rates_{region.lower()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rates, f, indent=2)


def list_regions() -> list"""Return all regions for which a rate file exists."""
    return [p.stem.replace("rates_", "").upper() for p in RATES_DIR.glob("rates_*.json")]