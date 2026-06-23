"""CSV case table support for finite-length truss cases."""

from __future__ import annotations

from pathlib import Path

from common.case_table import (
    CaseTableEntry,
    load_case_table,
    optional_int,
    require_text,
)

from .case import AnalysisType, BCType, BraceType, CaseDefinition, DiaphType


def _case_from_row(row: dict[str, str], row_num: int) -> CaseDefinition:
    name = require_text(row, "name", row_num)
    num_modes = optional_int(row.get("num_modes", ""), default=30)
    target_mode = optional_int(row.get("target_mode", ""), default=None)
    num_plot_modes = optional_int(row.get("num_plot_modes", ""), default=None)

    return CaseDefinition(
        name=name,
        num_sections=int(require_text(row, "num_sections", row_num)),
        num_subsections=int(require_text(row, "num_subsections", row_num)),
        ls=float(require_text(row, "ls", row_num)),
        ws=float(require_text(row, "ws", row_num)),
        diaph=DiaphType(require_text(row, "diaph", row_num)),
        brace=BraceType(require_text(row, "brace", row_num)),
        bc=BCType(require_text(row, "bc", row_num)),
        analysis=AnalysisType(require_text(row, "analysis", row_num)),
        num_modes=30 if num_modes is None else num_modes,
        target_mode=target_mode,
        num_plot_modes=num_plot_modes,
    )


def load_truss_case_table(path: Path) -> list[CaseTableEntry[CaseDefinition]]:
    """Load truss cases from a CSV case table."""
    return load_case_table(path, _case_from_row)
