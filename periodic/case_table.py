"""CSV case table support for periodic lattice unit cases."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import get_type_hints

from common.case_table import CaseTableEntry, load_case_table, require_text

from .case import PeriodicCase


def _case_from_row(row: dict[str, str], row_num: int) -> PeriodicCase:
    values: dict[str, object] = {"name": require_text(row, "name", row_num)}
    type_hints = get_type_hints(PeriodicCase)

    for field in fields(PeriodicCase):
        if field.name == "name":
            continue
        raw_value = row.get(field.name, "").strip()
        if raw_value == "":
            continue
        target_type = type_hints[field.name]
        if target_type is int:
            values[field.name] = int(raw_value)
        elif target_type is float:
            values[field.name] = float(raw_value)
        else:
            values[field.name] = raw_value

    for required_field in ("num_subsections", "ls", "ws"):
        require_text(row, required_field, row_num)

    return PeriodicCase(**values)


def load_periodic_case_table(path: Path) -> list[CaseTableEntry[PeriodicCase]]:
    """Load periodic cases from a CSV case table."""
    return load_case_table(path, _case_from_row)
