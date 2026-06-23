"""Summary table generation for periodic lattice unit results."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .case import PeriodicCase
from .parser import parse_dmatrix, parse_inertia_summary


DCOEFS = ["D11", "D22", "D33", "D44", "D55", "D66"]


def _dmatrix_values(path: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    if not path.exists():
        return values
    for row in parse_dmatrix(path):
        values[str(row["dcoef"])] = float(row["diagonal_stiffness"])
    return values


def _matrix_value(matrix: Any, i: int, j: int) -> float | None:
    if not isinstance(matrix, list) or len(matrix) <= i or len(matrix[i]) <= j:
        return None
    return float(matrix[i][j])


def build_periodic_summary_rows(
    cases: list[PeriodicCase],
    results_dir: Path,
) -> list[dict[str, object]]:
    """Build one wide summary row per periodic case with complete outputs."""
    rows: list[dict[str, object]] = []
    for case in cases:
        pbc_path = results_dir / f"{case.name}_pbc_Dmatrix.csv"
        rp_path = results_dir / f"{case.name}_rp_Dmatrix.csv"
        inertia_path = results_dir / f"{case.name}_inertia.txt"

        if not (pbc_path.exists() and rp_path.exists() and inertia_path.exists()):
            continue

        pbc = _dmatrix_values(pbc_path)
        rp = _dmatrix_values(rp_path)
        inertia = parse_inertia_summary(inertia_path)
        com = inertia.get("center_of_mass", (None, None, None))
        inertia_matrix = inertia.get("inertia_center_of_mass")

        row: dict[str, object] = {
            "case": case.name,
            "num_subsections": case.num_subsections,
            "ls": case.ls,
            "ws": case.ws,
            "cell_length": case.cell_length,
            "total_mass": inertia.get("total_mass"),
            "com_x": com[0],
            "com_y": com[1],
            "com_z": com[2],
            "ixx": _matrix_value(inertia_matrix, 0, 0),
            "ixy": _matrix_value(inertia_matrix, 0, 1),
            "ixz": _matrix_value(inertia_matrix, 0, 2),
            "iyy": _matrix_value(inertia_matrix, 1, 1),
            "iyz": _matrix_value(inertia_matrix, 1, 2),
            "izz": _matrix_value(inertia_matrix, 2, 2),
        }

        for dcoef in DCOEFS:
            row[f"pbc_{dcoef}"] = pbc.get(dcoef)
            row[f"rp_{dcoef}"] = rp.get(dcoef)
            if dcoef in pbc and dcoef in rp and rp[dcoef] != 0:
                row[f"pbc_over_rp_{dcoef}"] = pbc[dcoef] / rp[dcoef]
            else:
                row[f"pbc_over_rp_{dcoef}"] = None

        rows.append(row)
    return rows


def write_periodic_summary(
    cases: list[PeriodicCase],
    results_dir: Path,
    output_path: Path | None = None,
) -> Path:
    """Write results/periodic/periodic_summary.csv."""
    results_dir = Path(results_dir)
    output_path = output_path or results_dir / "periodic_summary.csv"
    rows = build_periodic_summary_rows(cases, results_dir)

    fieldnames = [
        "case",
        "num_subsections",
        "ls",
        "ws",
        "cell_length",
        *[f"pbc_{dcoef}" for dcoef in DCOEFS],
        *[f"rp_{dcoef}" for dcoef in DCOEFS],
        *[f"pbc_over_rp_{dcoef}" for dcoef in DCOEFS],
        "total_mass",
        "com_x",
        "com_y",
        "com_z",
        "ixx",
        "ixy",
        "ixz",
        "iyy",
        "iyz",
        "izz",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path

