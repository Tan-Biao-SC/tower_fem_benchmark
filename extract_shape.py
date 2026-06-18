#!/usr/bin/env python3
"""Extract modal shape data from completed ANSYS modal analysis results.

Usage:
    python extract_shape.py <case_name> <mode_number>
    python extract_shape.py <case_name> --plot <num_modes>

Examples:
    # Extract single mode shape (mode 7)
    python extract_shape.py W1p5_cant_modal 7

    # Plot and extract first 7 modes
    python extract_shape.py W1p5_cant_modal --plot 7

    # List available cases
    python extract_shape.py --list
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

BASE = Path(__file__).parent
TEMPLATES_DIR = BASE / "templates"
CASES_DIR = BASE / "cases"
RESULTS_DIR = BASE / "results"
FIGURES_DIR = BASE / "figures"


def find_case_definition(case_name: str) -> CaseDefinition:
    """Reconstruct CaseDefinition from case name by checking existing .inp files."""
    inp_path = CASES_DIR / f"{case_name}.inp"
    if not inp_path.exists():
        print(
            f"Error: No .inp file found for case '{case_name}' in {CASES_DIR}/"
        )
        print(
            "Run the modal analysis first with: python run.py --cases <index>"
        )
        sys.exit(1)

    # Parse parameters from the .inp file
    content = inp_path.read_text()
    params = {}
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("NUM_SECTIONS"):
            params["num_sections"] = int(line.split("=")[1].strip())
        elif line.startswith("NUM_SUB_SECTIONS"):
            params["num_subsections"] = int(line.split("=")[1].strip())
        elif line.startswith("LS") and not line.startswith("L"):
            params["ls"] = float(line.split("=")[1].strip())
        elif line.startswith("WS") and "=" in line:
            params["ws"] = float(line.split("=")[1].strip())
        elif line.startswith("NUM_MODES"):
            params["num_modes"] = int(line.split("=")[1].strip())

    # Determine diaph/brace/bc/analysis from template markers in the file
    diaph = DiaphType.X
    brace = BraceType.X
    bc = BCType.NONE
    analysis = AnalysisType.MODAL

    if "02_a_model_diaph_x" in content or "X-braced" in content:
        diaph = DiaphType.X
    if "02_b_model_diaph_slash" in content or "Single-Braced" in content:
        diaph = DiaphType.SLASH
    if "03_a_model_brace_x" in content:
        brace = BraceType.X
    if "03_b_model_brace_w" in content:
        brace = BraceType.W
    if "03_c_model_brace_n" in content:
        brace = BraceType.N
    if "04_a_bc_fix_free" in content:
        bc = BCType.FIX_FREE
    if "04_b_bc_simple" in content:
        bc = BCType.SIMPLE
    if "05_static_cantilever" in content:
        analysis = AnalysisType.STATIC_CANTILEVER
    if "05_static_simple" in content:
        analysis = AnalysisType.STATIC_SIMPLE

    return CaseDefinition(
        name=case_name,
        num_sections=params.get("num_sections", 10),
        num_subsections=params.get("num_subsections", 2),
        ls=params.get("ls", 3.0),
        ws=params.get("ws", 2.0),
        diaph=diaph,
        brace=brace,
        bc=bc,
        analysis=analysis,
        num_modes=params.get("num_modes", 30),
    )


def list_cases():
    """List available cases in cases/ directory."""
    if not CASES_DIR.exists():
        print("No cases/ directory found. Run a modal analysis first.")
        return
    inp_files = sorted(CASES_DIR.glob("*.inp"))
    # Filter out post-shape and plot-shape inp files
    main_files = [
        f
        for f in inp_files
        if "_shape_" not in f.name and "_plot_" not in f.name
    ]
    if not main_files:
        print("No case .inp files found in cases/.")
        return
    print("Available cases:")
    for f in main_files:
        # Check if .db and .rst exist
        db_exists = (CASES_DIR / f"{f.stem}.db").exists()
        rst_exists = (CASES_DIR / f"{f.stem}.rst").exists()
        status = (
            "✓ results ready" if (db_exists and rst_exists) else "✗ no results"
        )
        print(f"  {f.stem:30s} {status}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract modal shape data from ANSYS results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python extract_shape.py W1p5_cant_modal 7       # Extract mode 7 shape
  python extract_shape.py W1p5_cant_modal --plot 7  # Plot first 7 modes
  python extract_shape.py --list                    # List available cases""",
    )
    parser.add_argument(
        "case_name", nargs="?", help="Case name (e.g. W1p5_cant_modal)"
    )
    parser.add_argument(
        "mode",
        nargs="?",
        type=int,
        help="Mode number to extract (for single mode)",
    )
    parser.add_argument(
        "--plot", type=int, metavar="N", help="Plot and extract first N modes"
    )
    parser.add_argument(
        "--ansys-exe",
        default="ansys221",
        help="ANSYS executable path (default: ansys221)",
    )
    parser.add_argument(
        "--list", action="store_true", help="List available cases and exit"
    )
    args = parser.parse_args()

    if args.list:
        list_cases()
        return

    if not args.case_name:
        parser.print_help()
        sys.exit(1)

    # Check that .db and .rst exist
    db_path = CASES_DIR / f"{args.case_name}.db"
    rst_path = CASES_DIR / f"{args.case_name}.rst"
    if not db_path.exists() or not rst_path.exists():
        print(f"Error: Missing result files for '{args.case_name}':")
        if not db_path.exists():
            print(f"  {db_path} not found")
        if not rst_path.exists():
            print(f"  {rst_path} not found")
        print("Run the modal analysis first: python run.py --cases <index>")
        sys.exit(1)

    engine = TemplateEngine(TEMPLATES_DIR)
    runner = AnsysRunner(
        engine,
        CASES_DIR,
        RESULTS_DIR,
        ansys_exe=args.ansys_exe,
        figures_dir=FIGURES_DIR,
    )
    case = find_case_definition(args.case_name)

    if args.plot:
        # Plot and extract multiple modes
        print(f"[{args.case_name}] Plotting first {args.plot} modal shapes...")
        runner.run_plot_shape(case, num_plot_modes=args.plot)
    elif args.mode:
        # Extract single mode shape
        print(f"[{args.case_name}] Extracting mode {args.mode} shape...")
        runner.run_post_shape(case, target_mode=args.mode)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
