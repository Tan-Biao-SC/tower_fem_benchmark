"""Parsers for periodic analysis results."""

from __future__ import annotations

import csv
import re
from pathlib import Path


def parse_dmatrix(path: Path) -> list[dict[str, float | int | str]]:
    """Parse PBC/RP diagonal stiffness CSV output."""
    rows: list[dict[str, float | int | str]] = []
    with Path(path).open(newline="") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "case": int(row["case"]),
                    "dof": row["dof"],
                    "dcoef": row["dcoef"],
                    "total_strain_energy": float(row["total_strain_energy"]),
                    "diagonal_stiffness": float(row["diagonal_stiffness"]),
                }
            )
    return rows


def parse_inertia_summary(path: Path) -> dict[str, object]:
    """Parse key values from ANSYS IRLIST text output."""
    text = Path(path).read_text(errors="replace")
    result: dict[str, object] = {}

    mass_match = re.search(r"TOTAL MASS\s*=\s*([+-]?\d+(?:\.\d+)?(?:E[+-]?\d+)?)", text)
    if mass_match:
        result["total_mass"] = float(mass_match.group(1))

    com_match = re.search(
        r"CENTER OF MASS \(X,Y,Z\)=\s*"
        r"([+-]?\d+(?:\.\d+)?(?:E[+-]?\d+)?)\s+"
        r"([+-]?\d+(?:\.\d+)?(?:E[+-]?\d+)?)\s+"
        r"([+-]?\d+(?:\.\d+)?(?:E[+-]?\d+)?)",
        text,
    )
    if com_match:
        result["center_of_mass"] = tuple(float(value) for value in com_match.groups())

    inertia_marker = "TOTAL INERTIA ABOUT CENTER OF MASS"
    if inertia_marker in text:
        after_marker = text.split(inertia_marker, 1)[1]
        rows = []
        for line in after_marker.splitlines():
            values = re.findall(r"[+-]?\d+(?:\.\d+)?(?:E[+-]?\d+)?", line)
            if len(values) >= 3:
                rows.append([float(value) for value in values[:3]])
            if len(rows) == 3:
                break
        if len(rows) == 3:
            result["inertia_center_of_mass"] = rows

    return result

