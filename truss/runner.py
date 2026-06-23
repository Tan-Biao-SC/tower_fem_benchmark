"""ANSYS runner for finite-length truss analyses."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from common.ansys import DEFAULT_ANSYS_EXE, collect_files, run_ansys
from common.paths import ProjectPaths

from .case import AnalysisType, CaseDefinition
from .engine import TemplateEngine


class AnsysRunner:
    """Generate APDL, run ANSYS in per-case tmp dirs, and collect results."""

    def __init__(
        self,
        engine: TemplateEngine,
        paths: ProjectPaths,
        ansys_exe: str = DEFAULT_ANSYS_EXE,
    ):
        self.engine = engine
        self.paths = paths
        self.ansys_exe = ansys_exe
        self.paths.ensure_base_dirs()

    def run_case(self, case: CaseDefinition) -> subprocess.CompletedProcess:
        """Full pipeline: generate .inp, run ANSYS, collect results."""
        content = self.engine.build(case)
        inp_path = self.paths.cases_dir / f"{case.name}.inp"
        inp_path.write_text(content, encoding="utf-8")

        work_dir = self.paths.work_dir(case.name)
        log_path = self.paths.results_dir / f"{case.name}.log"
        cmd = [self.ansys_exe, "-b", "-i", str(inp_path), "-o", str(log_path)]
        print(f"[{case.name}] Running: {shlex.join(cmd)}")

        result = run_ansys(inp_path, log_path, work_dir, self.ansys_exe)
        self._collect_results(case, work_dir)

        if result.returncode != 0:
            print(
                f"[{case.name}] ANSYS returned non-zero exit code: {result.returncode}"
            )
        return result

    def run_post_shape(
        self, case: CaseDefinition, target_mode: int
    ) -> subprocess.CompletedProcess:
        """Run 06_modal_post_shape as a separate ANSYS job."""
        content = self.engine.build_post_shape(case, target_mode)

        suffix = f"_shape_{target_mode}"
        inp_path = self.paths.cases_dir / f"{case.name}{suffix}.inp"
        inp_path.write_text(content, encoding="utf-8")

        work_dir = self.paths.work_dir(case.name)
        log_path = self.paths.results_dir / f"{case.name}{suffix}.log"
        cmd = [self.ansys_exe, "-b", "-i", str(inp_path), "-o", str(log_path)]
        print(f"[{case.name}{suffix}] Running post-shape extraction...")
        print(f"[{case.name}{suffix}] Running: {shlex.join(cmd)}")

        result = run_ansys(inp_path, log_path, work_dir, self.ansys_exe)
        collect_files(
            work_dir,
            self.paths.results_dir,
            [f"{case.name}_shape_{target_mode}.txt"],
        )
        return result

    def run_plot_shape(
        self, case: CaseDefinition, num_plot_modes: int
    ) -> subprocess.CompletedProcess:
        """Run 06_modal_plot_shape as a separate ANSYS job."""
        content = self.engine.build_plot_shape(case, num_plot_modes)

        suffix = f"_plot_{num_plot_modes}"
        inp_path = self.paths.cases_dir / f"{case.name}{suffix}.inp"
        inp_path.write_text(content, encoding="utf-8")

        work_dir = self.paths.work_dir(case.name)
        log_path = self.paths.results_dir / f"{case.name}{suffix}.log"
        cmd = [self.ansys_exe, "-b", "-i", str(inp_path), "-o", str(log_path)]
        print(
            f"[{case.name}{suffix}] Running plot-shape for {num_plot_modes} modes..."
        )
        print(f"[{case.name}{suffix}] Running: {shlex.join(cmd)}")

        result = run_ansys(inp_path, log_path, work_dir, self.ansys_exe)

        collect_files(
            work_dir,
            self.paths.results_dir,
            [
                f"{case.name}_shape_{imode}.txt"
                for imode in range(1, num_plot_modes + 1)
            ],
        )

        png_files = sorted(work_dir.glob(f"{case.name}???.png"))
        for idx, png_path in enumerate(png_files, start=1):
            target_png = self.paths.figures_dir / f"{case.name}_mode_{idx}.png"
            png_path.replace(target_png)
            print(f"[{case.name}_plot_{num_plot_modes}] Collected {target_png.name}")

        return result

    def _collect_results(self, case: CaseDefinition, work_dir: Path) -> None:
        """Move expected output files from ANSYS CWD to results/."""
        if case.analysis == AnalysisType.MODAL:
            patterns = [f"{case.name}_freq.txt"]
        elif case.analysis == AnalysisType.STATIC_CANTILEVER:
            patterns = [f"{case.name}_cantilever.txt"]
        elif case.analysis == AnalysisType.STATIC_SIMPLE:
            patterns = [f"{case.name}_simple.txt"]
        else:
            patterns = []

        for target_path in collect_files(work_dir, self.paths.results_dir, patterns):
            print(f"[{case.name}] Collected {target_path.name}")

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
