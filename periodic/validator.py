"""Validation helpers for periodic lattice unit results."""

from __future__ import annotations

import math
from pathlib import Path

from .parser import parse_dmatrix, parse_inertia_summary


def _dcoef_map(path: Path) -> dict[str, float]:
    return {
        str(row["dcoef"]): float(row["diagonal_stiffness"])
        for row in parse_dmatrix(path)
    }


def validate_dmatrix(
    computed: Path,
    reference: Path,
    rtol: float = 1e-4,
    verbose: bool = True,
) -> bool:
    """Compare diagonal stiffness coefficients by D11...D66 labels."""
    comp = _dcoef_map(computed)
    ref = _dcoef_map(reference)
    common = sorted(set(comp) & set(ref))
    if not common:
        if verbose:
            print("  No common stiffness coefficients found.")
        return False

    errors = {
        dcoef: abs(comp[dcoef] - ref[dcoef]) / abs(ref[dcoef])
        for dcoef in common
        if ref[dcoef] != 0
    }
    max_dcoef = max(errors, key=errors.get)
    max_error = errors[max_dcoef]
    if verbose:
        print(f"  Coefficients compared: {len(common)}, max relative error: {max_error:.2e}")
        if max_error > rtol:
            print(
                f"  Worst coefficient: {max_dcoef}, "
                f"comp={comp[max_dcoef]:.6e}, ref={ref[max_dcoef]:.6e}"
            )
    return bool(max_error < rtol)


def validate_total_mass(
    computed: Path,
    reference: Path,
    rtol: float = 1e-4,
    verbose: bool = True,
) -> bool:
    """Compare total mass parsed from IRLIST output."""
    comp = parse_inertia_summary(computed).get("total_mass")
    ref = parse_inertia_summary(reference).get("total_mass")
    if comp is None or ref is None:
        if verbose:
            print("  Total mass missing from computed or reference inertia output.")
        return False

    ok = math.isclose(float(comp), float(ref), rel_tol=rtol)
    if verbose:
        rel_error = abs(float(comp) - float(ref)) / abs(float(ref))
        print(f"  Total mass relative error: {rel_error:.2e}")
    return ok

