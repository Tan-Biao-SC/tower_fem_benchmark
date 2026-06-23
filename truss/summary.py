"""Summary table generation for finite-length truss results."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .case import AnalysisType, CaseDefinition
from .parser import parse_cantilever, parse_freq, parse_simple


def _modal_row(case: CaseDefinition, results_dir: Path) -> dict[str, object] | None:
    path = results_dir / f"{case.name}_freq.txt"
    if not path.exists():
        return None
    freq = np.atleast_2d(parse_freq(path))
    return {
        "case": case.name,
        "analysis": case.analysis.value,
        "num_sections": case.num_sections,
        "num_subsections": case.num_subsections,
        "ls": case.ls,
        "ws": case.ws,
        "bc": case.bc.value,
        "brace": case.brace.value,
        "diaph": case.diaph.value,
        "num_result_rows": len(freq),
        "first_frequency_hz": float(freq[0, 1]),
        "max_abs_response": None,
    }


def _cantilever_row(
    case: CaseDefinition, results_dir: Path
) -> dict[str, object] | None:
    path = results_dir / f"{case.name}_cantilever.txt"
    if not path.exists():
        return None
    values = parse_cantilever(path)
    return {
        "case": case.name,
        "analysis": case.analysis.value,
        "num_sections": case.num_sections,
        "num_subsections": case.num_subsections,
        "ls": case.ls,
        "ws": case.ws,
        "bc": case.bc.value,
        "brace": case.brace.value,
        "diaph": case.diaph.value,
        "num_result_rows": len(values),
        "first_frequency_hz": None,
        "max_abs_response": float(np.max(np.abs(values))),
    }


def _simple_row(case: CaseDefinition, results_dir: Path) -> dict[str, object] | None:
    path = results_dir / f"{case.name}_simple.txt"
    if not path.exists():
        return None
    _, _, values = parse_simple(path)
    return {
        "case": case.name,
        "analysis": case.analysis.value,
        "num_sections": case.num_sections,
        "num_subsections": case.num_subsections,
        "ls": case.ls,
        "ws": case.ws,
        "bc": case.bc.value,
        "brace": case.brace.value,
        "diaph": case.diaph.value,
        "num_result_rows": len(values),
        "first_frequency_hz": None,
        "max_abs_response": float(np.max(np.abs(values))),
    }


def build_truss_summary_rows(
    cases: list[CaseDefinition],
    results_dir: Path,
) -> list[dict[str, object]]:
    """Build one compact summary row per truss case with available outputs."""
    rows: list[dict[str, object]] = []
    for case in cases:
        if case.analysis == AnalysisType.MODAL:
            row = _modal_row(case, results_dir)
        elif case.analysis == AnalysisType.STATIC_CANTILEVER:
            row = _cantilever_row(case, results_dir)
        elif case.analysis == AnalysisType.STATIC_SIMPLE:
            row = _simple_row(case, results_dir)
        else:
            row = None

        if row is not None:
            rows.append(row)
    return rows


def write_truss_summary(
    cases: list[CaseDefinition],
    results_dir: Path,
    output_path: Path | None = None,
) -> Path:
    """Write results/truss/truss_summary.csv."""
    results_dir = Path(results_dir)
    output_path = output_path or results_dir / "truss_summary.csv"
    rows = build_truss_summary_rows(cases, results_dir)
    fieldnames = [
        "case",
        "analysis",
        "num_sections",
        "num_subsections",
        "ls",
        "ws",
        "bc",
        "brace",
        "diaph",
        "num_result_rows",
        "first_frequency_hz",
        "max_abs_response",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path

