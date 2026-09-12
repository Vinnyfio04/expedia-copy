"""Shared helpers for reading the supplied CSV data files."""

from csv import DictReader
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


def read_csv_rows(filename: str) -> list[dict[str, str]]:
    """Return all rows from one supplied UTF-8 CSV file."""
    path = DATA_DIRECTORY / filename
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        return list(DictReader(csv_file))
