from __future__ import annotations

import csv
import json
from pathlib import Path


def relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv_header_and_count(path: Path) -> tuple[list[str], int]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return [], 0
        count = sum(1 for _ in reader)
    return header, count


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_key_value_csv(path: Path) -> dict[str, str]:
    rows = read_csv_rows(path)
    values: dict[str, str] = {}
    for row in rows:
        key = row.get("field", "")
        if key:
            values[key] = row.get("value", "")
    return values


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    ensure_directory(path.parent)
    fieldnames: list[str] = []
    if rows:
        fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            handle.write("")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def string_value(value: object | None) -> str:
    if value is None:
        return ""
    return str(value)
