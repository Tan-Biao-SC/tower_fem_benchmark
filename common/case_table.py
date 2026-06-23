"""CSV-backed case table helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generic, Iterable, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class CaseTableEntry(Generic[T]):
    """One row from a CSV case table plus its parsed case object."""

    id: str
    name: str
    tags: tuple[str, ...]
    enabled: bool
    description: str
    case: T


def parse_bool(value: str, *, field: str, row_num: int) -> bool:
    text = value.strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Row {row_num}: invalid boolean for {field}: {value!r}")


def optional_int(value: str, default: int | None = None) -> int | None:
    text = value.strip()
    return default if text == "" else int(text)


def optional_float(value: str, default: float | None = None) -> float | None:
    text = value.strip()
    return default if text == "" else float(text)


def require_text(row: dict[str, str], key: str, row_num: int) -> str:
    value = row.get(key, "").strip()
    if not value:
        raise ValueError(f"Row {row_num}: missing required field {key!r}")
    return value


def load_case_table(
    path: Path,
    case_factory: Callable[[dict[str, str], int], T],
) -> list[CaseTableEntry[T]]:
    """Read a CSV case table and validate stable identifiers."""
    entries: list[CaseTableEntry[T]] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            case_id = require_text(row, "id", row_num)
            name = require_text(row, "name", row_num)

            if case_id in seen_ids:
                raise ValueError(f"Row {row_num}: duplicate case id {case_id!r}")
            if name in seen_names:
                raise ValueError(f"Row {row_num}: duplicate case name {name!r}")
            seen_ids.add(case_id)
            seen_names.add(name)

            tags = tuple(row.get("tags", "").split())
            enabled = parse_bool(
                row.get("enabled", "true"),
                field="enabled",
                row_num=row_num,
            )
            description = row.get("description", "").strip()
            case = case_factory(row, row_num)
            entries.append(
                CaseTableEntry(
                    id=case_id,
                    name=name,
                    tags=tags,
                    enabled=enabled,
                    description=description,
                    case=case,
                )
            )

    return entries


def select_case_entries(
    entries: list[CaseTableEntry[T]],
    *,
    indices: Iterable[int] | None = None,
    ids: Iterable[str] | None = None,
    names: Iterable[str] | None = None,
    tags: Iterable[str] | None = None,
) -> list[CaseTableEntry[T]]:
    """Select rows by legacy indices or stable CSV metadata.

    If no selector is provided, only enabled rows are returned. Explicit
    selectors can include disabled rows.
    """
    index_set = set(indices or [])
    id_set = set(ids or [])
    name_set = set(names or [])
    tag_set = set(tags or [])
    has_selector = bool(index_set or id_set or name_set or tag_set)

    if not has_selector:
        return [entry for entry in entries if entry.enabled]

    selected: list[CaseTableEntry[T]] = []
    seen_positions: set[int] = set()
    for idx, entry in enumerate(entries):
        entry_tags = set(entry.tags)
        matches = (
            idx in index_set
            or entry.id in id_set
            or entry.name in name_set
            or bool(tag_set and tag_set.issubset(entry_tags))
        )
        if matches and idx not in seen_positions:
            selected.append(entry)
            seen_positions.add(idx)

    valid_indices = set(range(len(entries)))
    missing_indices = sorted(index_set - valid_indices)
    missing_ids = sorted(id_set - {entry.id for entry in entries})
    missing_names = sorted(name_set - {entry.name for entry in entries})
    available_tags = {tag for entry in entries for tag in entry.tags}
    missing_tags = sorted(tag_set - available_tags)

    errors = []
    if missing_indices:
        errors.append(f"indices={missing_indices}")
    if missing_ids:
        errors.append(f"ids={missing_ids}")
    if missing_names:
        errors.append(f"names={missing_names}")
    if missing_tags:
        errors.append(f"tags={missing_tags}")
    if errors:
        raise ValueError("No matching case table entries for " + ", ".join(errors))
    if not selected:
        raise ValueError("No case table entries matched the requested selectors")

    return selected


def print_case_list(cases: list[object]) -> None:
    """Print legacy Python default cases with their 0-based index."""
    rows = [
        {
            "case_index": str(idx),
            "case_name": getattr(case, "name", str(case)),
        }
        for idx, case in enumerate(cases)
    ]
    _print_rows(rows, ["case_index", "case_name"])


def print_case_table(entries: list[CaseTableEntry[object]]) -> None:
    """Print a compact case table for the CLI."""
    rows = [
        {
            "case_index": str(idx),
            "case_id": entry.id,
            "case_name": entry.name,
            "enabled": "true" if entry.enabled else "false",
            "tags": " ".join(entry.tags),
            "description": entry.description,
        }
        for idx, entry in enumerate(entries)
    ]
    columns = ["case_index", "case_id", "case_name", "enabled", "tags", "description"]
    _print_rows(rows, columns)


def _print_rows(rows: list[dict[str, str]], columns: list[str]) -> None:
    """Print rows with simple fixed-width columns."""
    if not rows:
        print("(no cases)")
        return

    widths = {
        column: max(len(column), *(len(row[column]) for row in rows))
        for column in columns
    }

    header = "  ".join(column.ljust(widths[column]) for column in columns)
    print(header)
    print("  ".join("-" * widths[column] for column in columns))
    for row in rows:
        print("  ".join(row[column].ljust(widths[column]) for column in columns))
