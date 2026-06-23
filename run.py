#!/usr/bin/env python3
"""Parametric FEM benchmark for lattice transmission towers using ANSYS APDL.

Usage:
    python run.py              # run all cases
    python run.py --dry-run    # generate .inp files only, don't run ANSYS
    python run.py --validate   # run + validate against reference data
"""

import argparse
import sys
from pathlib import Path

from benchmark.case import (
    CaseDefinition,
    DiaphType,
    BraceType,
    BCType,
    AnalysisType,
)
from benchmark.engine import TemplateEngine
from benchmark.runner import AnsysRunner
from benchmark.parser import parse_freq, parse_cantilever, parse_simple
from benchmark.validator import validate_frequencies, validate_tip_disp

# ── Paths ──
BASE = Path(__file__).parent
TEMPLATES_DIR = BASE / "templates"
CASES_DIR = BASE / "cases"
RESULTS_DIR = BASE / "results"
FIGURES_DIR = BASE / "figures"
VALIDATIONS_DIR = BASE / "validations"

# ── Case definitions ──
# Width sweep — cantilever modal (X-brace, X-diaphragm)
WIDTH_CASES = [
    CaseDefinition(
        f"W{w:.1f}_cant_modal",
        num_sections=10,
        num_subsections=2,
        ls=3.0,
        ws=w,
        diaph=DiaphType.X,
        brace=BraceType.X,
        bc=BCType.FIX_FREE,
        analysis=AnalysisType.MODAL,
        num_modes=30,
    )
    for w in [1.5, 2.0, 3.0, 4.0, 6.0]
]

# Section count sweep — cantilever modal (X-brace, X-diaphragm)
SECTION_CASES = [
    CaseDefinition(
        f"S{ns}_cant_modal",
        num_sections=ns,
        num_subsections=4,
        ls=1.5,
        ws=2.0,
        diaph=DiaphType.X,
        brace=BraceType.X,
        bc=BCType.FIX_FREE,
        analysis=AnalysisType.MODAL,
        num_modes=30,
    )
    for ns in [4, 6, 8, 10, 15, 20]
]

# Sub-section sweep — cantilever modal (X-brace, X-diaphragm)
SUBSECTION_CASES = [
    CaseDefinition(
        f"NC{nc}_cant_modal",
        num_sections=10,
        num_subsections=nc,
        ls=3.0,
        ws=2.0,
        diaph=DiaphType.X,
        brace=BraceType.X,
        bc=BCType.FIX_FREE,
        analysis=AnalysisType.MODAL,
        num_modes=30,
    )
    for nc in [2, 3, 4, 6, 8]
]

# Brace type sweep — cantilever static
BRACE_CASES = [
    CaseDefinition(
        f"brace_{bt.value}_cant_static",
        num_sections=10,
        num_subsections=2,
        ls=3.0,
        ws=2.0,
        diaph=DiaphType.X,
        brace=bt,
        bc=BCType.FIX_FREE,
        analysis=AnalysisType.STATIC_CANTILEVER,
    )
    for bt in [BraceType.X, BraceType.W, BraceType.N]
]

# Simple support static — X-brace, X-diaphragm
SIMPLE_CASES = [
    CaseDefinition(
        "xbrace_xdiaph_simple_static",
        num_sections=10,
        num_subsections=2,
        ls=3.0,
        ws=2.0,
        diaph=DiaphType.X,
        brace=BraceType.X,
        bc=BCType.SIMPLE,
        analysis=AnalysisType.STATIC_SIMPLE,
    ),
]

# Free-free modal — X-brace, X-diaphragm
FREE_MODAL_CASES = [
    CaseDefinition(
        "xbrace_xdiaph_free_modal",
        num_sections=10,
        num_subsections=2,
        ls=3.0,
        ws=2.0,
        diaph=DiaphType.X,
        brace=BraceType.X,
        bc=BCType.NONE,
        analysis=AnalysisType.MODAL,
        num_modes=30,
    ),
]

# All cases combined
ALL_CASES = (
    WIDTH_CASES
    + SECTION_CASES
    + SUBSECTION_CASES
    + BRACE_CASES
    + SIMPLE_CASES
    + FREE_MODAL_CASES
)


def main():
    parser = argparse.ArgumentParser(
        description="Parametric FEM benchmark runner"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate .inp files only, don't run ANSYS",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate results against reference data after running",
    )
    parser.add_argument(
        "--plot-shapes",
        type=int,
        default=None,
        metavar="N",
        help="Plot first N modal shapes (requires prior modal run)",
    )
    parser.add_argument(
        "--cases",
        nargs="+",
        type=int,
        default=None,
        help="Run only specific case indices (0-based)",
    )
    parser.add_argument(
        "--ansys-exe",
        default="ansys221",
        help="ANSYS executable path (default: ansys221)",
    )
    args = parser.parse_args()

    # Select cases
    cases = (
        ALL_CASES if args.cases is None else [ALL_CASES[i] for i in args.cases]
    )

    engine = TemplateEngine(TEMPLATES_DIR)

    # Dry run: just generate .inp files
    if args.dry_run:
        CASES_DIR.mkdir(parents=True, exist_ok=True)
        for case in cases:
            content = engine.build(case)
            inp_path = CASES_DIR / f"{case.name}.inp"
            inp_path.write_text(content)
            print(f"[{case.name}] Written {inp_path}")
        print(
            f"\nDry run complete. {len(cases)} .inp files generated in {CASES_DIR}/"
        )
        return

    # Full run
    runner = AnsysRunner(
        engine,
        CASES_DIR,
        RESULTS_DIR,
        ansys_exe=args.ansys_exe,
        figures_dir=FIGURES_DIR,
    )
    results = runner.run_all(cases)

    # Plot modal shapes (requires prior modal run)
    if args.plot_shapes:
        for case in cases:
            if case.analysis == AnalysisType.MODAL:
                print(
                    f"[{case.name}] Plotting {args.plot_shapes} modal shapes..."
                )
                runner.run_plot_shape(case, args.plot_shapes)

    # Summary
    print("\n=== Summary ===")
    for name, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  {name}: {status}")

    # Validation
    if args.validate:
        print("\n=== Validation ===")
        ref_freq = VALIDATIONS_DIR / "modal/modal_freq.txt"
        ref_tip = VALIDATIONS_DIR / "static/tip_disp.txt"

        for case in cases:
            if case.analysis == AnalysisType.MODAL:
                freq_file = RESULTS_DIR / f"{case.name}_freq.txt"
                if freq_file.exists() and ref_freq.exists():
                    print(f"[{case.name}] Frequency:")
                    validate_frequencies(freq_file, ref_freq)
            elif case.analysis == AnalysisType.STATIC_CANTILEVER:
                tip_file = RESULTS_DIR / f"{case.name}_cantilever.txt"
                if tip_file.exists() and ref_tip.exists():
                    print(f"[{case.name}] Tip displacement:")
                    validate_tip_disp(tip_file, ref_tip)


if __name__ == "__main__":
    main()
