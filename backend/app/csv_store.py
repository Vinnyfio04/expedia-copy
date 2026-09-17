"""Shared helpers for reading and appending to the CSV data files."""

from csv import DictReader, DictWriter
from pathlib import Path
from tempfile import NamedTemporaryFile


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


def read_csv_rows(filename: str) -> list[dict[str, str]]:
    """Return all rows from one supplied UTF-8 CSV file."""
    path = DATA_DIRECTORY / filename
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        return list(DictReader(csv_file))


def append_csv_rows(rows_by_filename: list[tuple[str, dict[str, str]]]) -> None:
    """Append validated rows and roll back every file if an append fails."""
    prepared_rows: list[tuple[Path, list[str], dict[str, str]]] = []

    for filename, row in rows_by_filename:
        path = DATA_DIRECTORY / filename
        with path.open(encoding="utf-8-sig", newline="") as csv_file:
            fieldnames = DictReader(csv_file).fieldnames

        if fieldnames is None:
            raise ValueError(f"{filename} does not contain a CSV header.")
        if set(row) != set(fieldnames):
            raise ValueError(f"{filename} row does not match its CSV header.")

        prepared_rows.append((path, fieldnames, row))

    starting_sizes = {path: path.stat().st_size for path, _, _ in prepared_rows}

    try:
        for path, fieldnames, row in prepared_rows:
            with path.open("a", encoding="utf-8", newline="") as csv_file:
                DictWriter(csv_file, fieldnames=fieldnames).writerow(row)
    except Exception:
        for path, starting_size in starting_sizes.items():
            with path.open("r+b") as csv_file:
                csv_file.truncate(starting_size)
        raise


def update_csv_row(
    filename: str,
    identifier_column: str,
    identifier: str,
    updates: dict[str, str],
) -> dict[str, str]:
    """Replace fields in one identified CSV row without removing any rows."""
    path = DATA_DIRECTORY / filename
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = DictReader(csv_file)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if fieldnames is None:
        raise ValueError(f"{filename} does not contain a CSV header.")
    if identifier_column not in fieldnames:
        raise ValueError(f"{filename} does not contain {identifier_column}.")
    if not set(updates).issubset(fieldnames):
        raise ValueError(f"{filename} update does not match its CSV header.")

    matches = [row for row in rows if row[identifier_column] == identifier]
    if len(matches) != 1:
        raise LookupError(f"{identifier} was not found in {filename}.")

    updated_row = matches[0]
    updated_row.update(updates)
    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8-sig",
            newline="",
            delete=False,
            dir=path.parent,
            prefix=f".{path.stem}-",
            suffix=".tmp",
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            writer = DictWriter(temporary_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        temporary_path.replace(path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise

    return updated_row
