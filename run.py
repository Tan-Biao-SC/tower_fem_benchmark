#!/usr/bin/env python3
"""Unified entry point for tower FEM benchmark workflows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common.ansys import DEFAULT_ANSYS_EXE
from common.case_table import print_case_list, print_case_table, select_case_entries
from common.paths import ProjectPaths
from periodic.case_table import load_periodic_case_table
from periodic.defaults import DEFAULT_CASES as PERIODIC_CASES
from periodic.engine import PeriodicTemplateEngine
from periodic.runner import PeriodicRunner
from truss.case import AnalysisType
from truss.case_table import load_truss_case_table
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
        help="Run only specific case indices (0-based, legacy)",
    )
    parser.add_argument(
        "--case-table",
        type=Path,
        default=None,
        help="Read cases from a CSV case table",
    )
    parser.add_argument(
        "--case-ids",
        nargs="+",
        default=None,
        help="Run only cases with these CSV ids",
    )
    parser.add_argument(
        "--case-names",
        nargs="+",
        default=None,
        help="Run only cases with these names",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        default=None,
        help="Run cases containing all of these space-separated CSV tags",
    )
    parser.add_argument(
        "--list-cases",
        action="store_true",
        help="List available cases and exit",
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


def load_cases_from_args(args: argparse.Namespace, default_cases, table_loader):
    """Return cases from either Python defaults or a CSV case table."""
    if args.case_table is None:
        cases = select_cases(default_cases, args.cases)
        if args.list_cases:
            print_case_list(cases)
            return cases, True
        if args.case_ids or args.case_names or args.tags:
            raise ValueError(
                "--case-ids, --case-names, and --tags require --case-table"
            )
        return cases, False

    entries = table_loader(args.case_table)
    if args.list_cases:
        print_case_table(entries)
        return [entry.case for entry in entries], True

    selected = select_case_entries(
        entries,
        indices=args.cases,
        ids=args.case_ids,
        names=args.case_names,
        tags=args.tags,
    )
    return [entry.case for entry in selected], False


def run_periodic(args: argparse.Namespace) -> int:
    paths = ProjectPaths.for_module(BASE, "periodic")
    default_case_table = BASE / "cases" / "periodic_cases.csv"
    summarize_all_registered = (
        args.summarize
        and args.case_table is None
        and args.cases is None
        and args.case_ids is None
        and args.case_names is None
        and args.tags is None
        and default_case_table.exists()
    )
    if summarize_all_registered:
        # A summary rebuild should cover every registered case that has complete
        # result files, including disabled CSV rows.  The Python defaults are a
        # small development subset and would silently omit parameter sweeps.
        entries = load_periodic_case_table(default_case_table)
        cases = [entry.case for entry in entries]
        listed = False
    else:
        cases, listed = load_cases_from_args(
            args,
            PERIODIC_CASES,
            load_periodic_case_table,
        )
    if listed:
        return 0
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
        inp_path.write_text(content, encoding="utf-8")
        print(f"[{case.name}] Written {inp_path}")
    print(
        f"\nTruss dry run complete. {len(cases)} .inp files generated in {paths.cases_dir}/"
    )


def run_truss(args: argparse.Namespace) -> int:
    paths = ProjectPaths.for_module(BASE, "truss")
    cases, listed = load_cases_from_args(
        args,
        TRUSS_CASES,
        load_truss_case_table,
    )
    if listed:
        return 0
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

    try:
        if args.module == "periodic":
            return run_periodic(args)
        if args.module == "truss":
            return run_truss(args)
    except ValueError as e:
        parser.error(str(e))

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
