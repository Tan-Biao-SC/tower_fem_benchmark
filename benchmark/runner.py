"""ANSYS runner: execute APDL, manage working directories, collect results."""

import subprocess
import shutil
import shlex
from pathlib import Path

from common.ansys import DEFAULT_ANSYS_EXE, run_ansys

from .case import CaseDefinition, AnalysisType
from .engine import TemplateEngine


class AnsysRunner:
    """Runs ANSYS APDL, manages working directories, collects results.

    Working directory layout::

        cases/       ← ANSYS CWD: .inp files + ANSYS artifacts (.db, .rst, ...)
        results/     ← final output: .log, .txt result files
    """

    def __init__(
        self,
        engine: TemplateEngine,
        cases_dir: Path,
        results_dir: Path,
        ansys_exe: str = DEFAULT_ANSYS_EXE,
        figures_dir: Path | None = None,
    ):
        self.engine = engine
        self.cases_dir = Path(cases_dir)
        self.results_dir = Path(results_dir)
        self.figures_dir = (
            Path(figures_dir) if figures_dir else self.results_dir / "figures"
        )
        self.ansys_exe = ansys_exe
        self.cases_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)

    def run_case(self, case: CaseDefinition) -> subprocess.CompletedProcess:
        """Full pipeline: generate .inp → run ANSYS → collect results."""
        # 1. Build APDL input
        content = self.engine.build(case)

        # 2. Write .inp to cases/ (ANSYS working directory)
        inp_path = self.cases_dir / f"{case.name}.inp"
        inp_path.write_text(content)

        # 3. Run ANSYS with CWD = cases/ so .db/.rst land there
        log_path = self.results_dir / f"{case.name}.log"
        cmd = [self.ansys_exe, "-b", "-i", str(inp_path), "-o", str(log_path)]
        print(f"[{case.name}] Running: {shlex.join(cmd)}")
        result = run_ansys(inp_path, log_path, self.cases_dir, self.ansys_exe)

        # 4. Collect result .txt files from ANSYS CWD → results/
        self._collect_results(case)

        if result.returncode != 0:
            print(
                f"[{case.name}] ANSYS returned non-zero exit code: {result.returncode}"
            )
        return result

    def run_post_shape(
        self, case: CaseDefinition, target_mode: int
    ) -> subprocess.CompletedProcess:
        """Run 06_modal_post_shape as a separate ANSYS job.

        Requires: .db and .rst files from a prior modal run in cases/.
        """
        content = self.engine.build_post_shape(case, target_mode)

        suffix = f"_shape_{target_mode}"
        inp_path = self.cases_dir / f"{case.name}{suffix}.inp"
        inp_path.write_text(content)

        log_path = self.results_dir / f"{case.name}{suffix}.log"
        cmd = [self.ansys_exe, "-b", "-i", str(inp_path), "-o", str(log_path)]
        print(f"[{case.name}{suffix}] Running post-shape extraction...")
        print(f"[{case.name}{suffix}] Running: {shlex.join(cmd)}")
        result = run_ansys(inp_path, log_path, self.cases_dir, self.ansys_exe)

        # Collect shape output file
        fname = f"{case.name}_shape_{target_mode}.txt"
        src = self.cases_dir / fname
        if src.exists():
            shutil.move(str(src), str(self.results_dir / fname))
            print(f"[{case.name}{suffix}] Collected {fname}")
        return result

    def run_plot_shape(
        self, case: CaseDefinition, num_plot_modes: int
    ) -> subprocess.CompletedProcess:
        """Run 06_modal_plot_shape as a separate ANSYS job.

        Requires: .db and .rst files from a prior modal run in cases/.
        Produces PNG images and shape data files for each mode.
        """
        content = self.engine.build_plot_shape(case, num_plot_modes)

        suffix = f"_plot_{num_plot_modes}"
        inp_path = self.cases_dir / f"{case.name}{suffix}.inp"
        inp_path.write_text(content)

        log_path = self.results_dir / f"{case.name}{suffix}.log"
        cmd = [self.ansys_exe, "-b", "-i", str(inp_path), "-o", str(log_path)]
        print(
            f"[{case.name}{suffix}] Running plot-shape for {num_plot_modes} modes..."
        )
        print(f"[{case.name}{suffix}] Running: {shlex.join(cmd)}")
        result = run_ansys(inp_path, log_path, self.cases_dir, self.ansys_exe)

        # Collect shape output files (one per mode)
        for imode in range(1, num_plot_modes + 1):
            fname = f"{case.name}_shape_{imode}.txt"
            src = self.cases_dir / fname
            if src.exists():
                shutil.move(str(src), str(self.results_dir / fname))

        # Collect and rename PNG files
        # ANSYS generates <case>NNN.png (auto-incrementing); rename to <case>_mode_<N>.png
        png_files = sorted(self.cases_dir.glob(f"{case.name}???.png"))
        for idx, png_path in enumerate(png_files, start=1):
            target_png = self.figures_dir / f"{case.name}_mode_{idx}.png"
            shutil.move(str(png_path), str(target_png))
            print(
                f"[{case.name}_plot_{num_plot_modes}] Collected {target_png.name}"
            )

        return result

    def _collect_results(self, case: CaseDefinition):
        """Move output .txt files from ANSYS CWD to results/."""
        # Determine expected output filename based on analysis type
        if case.analysis == AnalysisType.MODAL:
            patterns = [f"{case.name}_freq.txt"]
        elif case.analysis == AnalysisType.STATIC_CANTILEVER:
            patterns = [f"{case.name}_cantilever.txt"]
        elif case.analysis == AnalysisType.STATIC_SIMPLE:
            patterns = [f"{case.name}_simple.txt"]
        else:
            patterns = []

        for fname in patterns:
            src = self.cases_dir / fname
            if src.exists():
                shutil.move(str(src), str(self.results_dir / fname))
                print(f"[{case.name}] Collected {fname}")

    def run_all(self, cases: list[CaseDefinition]) -> dict[str, bool]:
        """Sequential execution. Returns {case_name: success}."""
        results = {}
        for case in cases:
            try:
                proc = self.run_case(case)
                results[case.name] = proc.returncode == 0
            except Exception as e:
                results[case.name] = False
                print(f"[{case.name}] FAILED: {e}")
        return results
