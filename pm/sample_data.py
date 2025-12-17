"""Sample data loader for generating party records from CSV only."""

from __future__ import annotations

import csv
from pathlib import Path

SAMPLE_CSV_PATH = Path(__file__).parent / "sample_data.csv"
CSV_HEADERS = [
    "ExternalRef",
    "PartyType",
    "GivenName",
    "MiddleName",
    "Surname",
    "CountryCode",
    "City",
    "PostalCode",
    "Email",
    "Phone",
    "Status",
]


def load_csv_rows(path: Path = SAMPLE_CSV_PATH) -> list[tuple[str, ...]]:  # type: ignore[type-arg]
    if not path.exists():
        raise FileNotFoundError(f"Sample CSV missing at {path}")
    rows: list[tuple[str, ...]] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        _ = next(reader, None)  # skip header
        for row in reader:
            rows.append(tuple(row))
    return rows
