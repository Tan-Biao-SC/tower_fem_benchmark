"""Parsers for periodic analysis results."""

from __future__ import annotations

import csv
import re
from pathlib import Path


FLOAT_PATTERN = r"[+-]?\d+(?:\.\d+)?(?:E[+-]?\d+)?"
MASS_MATRIX_DOFS = ["UX", "UY", "UZ", "ROTX", "ROTY", "ROTZ"]


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


def _float_values(text: str) -> list[float]:
    return [float(value) for value in re.findall(FLOAT_PATTERN, text)]


def parse_mass_matrix(path: Path) -> list[list[float]]:
    """Parse the 6x6 rigid-body mass matrix from ANSYS IRLIST output."""
    text = Path(path).read_text(errors="replace")
    marker = "TOTAL RIGID BODY MASS MATRIX ABOUT ORIGIN"
    if marker not in text:
        raise ValueError(f"Mass matrix marker not found in {path}")

    translational_rows: list[list[float]] = []
    coupled_rows: list[list[float]] = []
    rotational_rows: list[list[float]] = []
    in_rotational_block = False

    for line in text.split(marker, 1)[1].splitlines():
        if "TOTAL MASS" in line:
            break

        if "Rotational mass" in line:
            in_rotational_block = True
            continue

        if not in_rotational_block and "|" in line:
            left, right = line.split("|", 1)
            left_values = _float_values(left)
            right_values = _float_values(right)
            if len(left_values) >= 3 and len(right_values) >= 3:
                translational_rows.append(left_values[:3])
                coupled_rows.append(right_values[:3])
            continue

        if in_rotational_block:
            values = _float_values(line)
            if len(values) >= 3:
                rotational_rows.append(values[:3])

    if (
        len(translational_rows) != 3
        or len(coupled_rows) != 3
        or len(rotational_rows) != 3
    ):
        raise ValueError(f"Could not parse a complete 6x6 mass matrix from {path}")

    matrix = [
        [*translational_rows[row], *coupled_rows[row]]
        for row in range(3)
    ]
    matrix.extend(
        [
            coupled_rows[0][row],
            coupled_rows[1][row],
            coupled_rows[2][row],
            *rotational_rows[row],
        ]
        for row in range(3)
    )
    return matrix


def write_mass_matrix_csv(
    inertia_path: Path,
    output_path: Path | None = None,
) -> Path:
    """Write the parsed 6x6 mass matrix to CSV with DOF labels."""
    inertia_path = Path(inertia_path)
    output_path = output_path or inertia_path.with_name(
        inertia_path.name.replace("_inertia.txt", "_mass_matrix.csv")
    )
    matrix = parse_mass_matrix(inertia_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["dof", *MASS_MATRIX_DOFS])
        for dof, row in zip(MASS_MATRIX_DOFS, matrix):
            writer.writerow([dof, *row])
    return output_path


def parse_inertia_summary(path: Path) -> dict[str, object]:
    """Parse key values from ANSYS IRLIST text output."""
    text = Path(path).read_text(errors="replace")
    result: dict[str, object] = {}

    mass_match = re.search(rf"TOTAL MASS\s*=\s*({FLOAT_PATTERN})", text)
    if mass_match:
        result["total_mass"] = float(mass_match.group(1))

    com_match = re.search(
        r"CENTER OF MASS \(X,Y,Z\)=\s*"
        rf"({FLOAT_PATTERN})\s+"
        rf"({FLOAT_PATTERN})\s+"
        rf"({FLOAT_PATTERN})",
        text,
    )
    if com_match:
        result["center_of_mass"] = tuple(float(value) for value in com_match.groups())

    inertia_marker = "TOTAL INERTIA ABOUT CENTER OF MASS"
    if inertia_marker in text:
        after_marker = text.split(inertia_marker, 1)[1]
        rows = []
        for line in after_marker.splitlines():
            values = re.findall(FLOAT_PATTERN, line)
            if len(values) >= 3:
                rows.append([float(value) for value in values[:3]])
            if len(rows) == 3:
                break
        if len(rows) == 3:
            result["inertia_center_of_mass"] = rows

    return result
