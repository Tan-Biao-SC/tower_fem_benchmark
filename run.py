#!/usr/bin/env python3
"""Unified entry point for tower FEM benchmark workflows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common.ansys import DEFAULT_ANSYS_EXE
from common.paths import ProjectPaths
from periodic.defaults import DEFAULT_CASES as PERIODIC_CASES
from periodic.engine import PeriodicTemplateEngine
from periodic.runner import PeriodicRunner
from truss.case import AnalysisType
from truss.defaults import ALL_CASES as TRUSS_CASES
from truss.engine import TemplateEngine
from truss.runner import AnsysRunner


BASE = Path(__file__).parent
VALIDATIONS_DIR = BASE / "validations"


def add_common_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate .inp files only, don't run ANSYS",
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
        default=DEFAULT_ANSYS_EXE,
        help=f"ANSYS executable path (default: {DEFAULT_ANSYS_EXE})",
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Build summary CSV from existing result files without running ANSYS",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parametric FEM benchmark runner"
    )
    subparsers = parser.add_subparsers(dest="module", metavar="{periodic,truss}")

    periodic_parser = subparsers.add_parser(
        "periodic",
        help="Run periodic lattice unit analysis",
    )
    add_common_run_args(periodic_parser)
    periodic_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate periodic results against available reference data",
    )

    truss_parser = subparsers.add_parser(
        "truss",
        help="Run finite-length truss analysis",
    )
    add_common_run_args(truss_parser)
    truss_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate results against reference data after running",
    )
    truss_parser.add_argument(
        "--plot-shapes",
        type=int,
        default=None,
        metavar="N",
        help="Plot first N modal shapes (requires prior modal run)",
    )

    return parser


def select_cases(all_cases, indices: list[int] | None):
    if indices is None:
        return all_cases
    return [all_cases[i] for i in indices]


def run_periodic(args: argparse.Namespace) -> int:
    paths = ProjectPaths.for_module(BASE, "periodic")
    cases = select_cases(PERIODIC_CASES, args.cases)
    engine = PeriodicTemplateEngine(paths.templates_dir)
    runner = PeriodicRunner(engine, paths, ansys_exe=args.ansys_exe)

    if args.summarize:
        from periodic.summary import write_periodic_summary

        summary_path = write_periodic_summary(cases, paths.results_dir)
        print(f"Periodic summary written: {summary_path}")
        if args.validate:
            validate_periodic(cases, paths.results_dir)
        return 0

    if args.dry_run:
        runner.dry_run(cases)
        return 0

    results = runner.run_all(cases)

    print("\n=== Summary ===")
    for name, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  {name}: {status}")

    from periodic.summary import write_periodic_summary

    summary_path = write_periodic_summary(cases, paths.results_dir)
    print(f"\nPeriodic summary written: {summary_path}")

    if args.validate:
        validate_periodic(cases, paths.results_dir)

    return 0 if all(results.values()) else 1


def validate_periodic(cases, results_dir: Path) -> None:
    from periodic.validator import validate_dmatrix, validate_total_mass

    print("\n=== Periodic Validation ===")
    for case in cases:
        ref_dir = VALIDATIONS_DIR / "periodic" / case.name
        if not ref_dir.exists():
            print(f"[{case.name}] No reference data found, skipped.")
            continue

        print(f"[{case.name}] PBC stiffness:")
        validate_dmatrix(
            results_dir / f"{case.name}_pbc_Dmatrix.csv",
            ref_dir / "pbc_Dmatrix.csv",
        )
        print(f"[{case.name}] RP stiffness:")
        validate_dmatrix(
            results_dir / f"{case.name}_rp_Dmatrix.csv",
            ref_dir / "rp_Dmatrix.csv",
        )
        print(f"[{case.name}] Total mass:")
        validate_total_mass(
            results_dir / f"{case.name}_inertia.txt",
            ref_dir / "inertia.txt",
        )


def dry_run_truss(cases, paths: ProjectPaths, engine: TemplateEngine) -> None:
    paths.ensure_base_dirs()
    for case in cases:
        content = engine.build(case)
        inp_path = paths.cases_dir / f"{case.name}.inp"
        inp_path.write_text(content)
        print(f"[{case.name}] Written {inp_path}")
    print(
        f"\nTruss dry run complete. {len(cases)} .inp files generated in {paths.cases_dir}/"
    )


def run_truss(args: argparse.Namespace) -> int:
    paths = ProjectPaths.for_module(BASE, "truss")
    cases = select_cases(TRUSS_CASES, args.cases)
    engine = TemplateEngine(paths.templates_dir)

    if args.summarize:
        from truss.summary import write_truss_summary

        summary_path = write_truss_summary(cases, paths.results_dir)
        print(f"Truss summary written: {summary_path}")
        return 0

    if args.dry_run:
        dry_run_truss(cases, paths, engine)
        return 0

    runner = AnsysRunner(
        engine,
        paths,
        ansys_exe=args.ansys_exe,
    )
    results = runner.run_all(cases)

    if args.plot_shapes:
        for case in cases:
            if case.analysis == AnalysisType.MODAL:
                print(f"[{case.name}] Plotting {args.plot_shapes} modal shapes...")
                runner.run_plot_shape(case, args.plot_shapes)

    print("\n=== Summary ===")
    for name, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  {name}: {status}")

    from truss.summary import write_truss_summary

    summary_path = write_truss_summary(cases, paths.results_dir)
    print(f"\nTruss summary written: {summary_path}")

    if args.validate:
        from truss.validator import validate_frequencies, validate_tip_disp

        print("\n=== Validation ===")
        ref_freq = VALIDATIONS_DIR / "modal/modal_freq.txt"
        ref_tip = VALIDATIONS_DIR / "static/tip_disp.txt"

        for case in cases:
            if case.analysis == AnalysisType.MODAL:
                freq_file = paths.results_dir / f"{case.name}_freq.txt"
                if freq_file.exists() and ref_freq.exists():
                    print(f"[{case.name}] Frequency:")
                    validate_frequencies(freq_file, ref_freq)
            elif case.analysis == AnalysisType.STATIC_CANTILEVER:
                tip_file = paths.results_dir / f"{case.name}_cantilever.txt"
                if tip_file.exists() and ref_tip.exists():
                    print(f"[{case.name}] Tip displacement:")
                    validate_tip_disp(tip_file, ref_tip)

    return 0 if all(results.values()) else 1


def normalize_legacy_args(argv: list[str]) -> list[str]:
    """Map old root-level options to the truss subcommand."""
    if not argv or argv[0] in {"periodic", "truss", "-h", "--help"}:
        return argv
    return ["truss", *argv]


def main(argv: list[str] | None = None) -> int:
    argv = normalize_legacy_args(list(sys.argv[1:] if argv is None else argv))
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.module == "periodic":
        return run_periodic(args)
    if args.module == "truss":
        return run_truss(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
