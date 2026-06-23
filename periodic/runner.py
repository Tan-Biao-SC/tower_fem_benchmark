"""Periodic lattice unit runner."""

from __future__ import annotations

import shlex
import subprocess

from common.ansys import DEFAULT_ANSYS_EXE, collect_files, run_ansys
from common.paths import ProjectPaths

from .case import PeriodicCase
from .engine import PeriodicTemplateEngine


class PeriodicRunner:
    """Generate periodic APDL scripts, run ANSYS, and collect results."""

    def __init__(
        self,
        engine: PeriodicTemplateEngine,
        paths: ProjectPaths,
        ansys_exe: str = DEFAULT_ANSYS_EXE,
    ):
        self.engine = engine
        self.paths = paths
        self.ansys_exe = ansys_exe
        self.paths.ensure_base_dirs()

    def write_input(self, case: PeriodicCase) -> None:
        input_path = self.paths.cases_dir / f"{case.name}.inp"
        input_path.write_text(self.engine.build(case), encoding="utf-8")
        print(f"[{case.name}] Written {input_path}")

    def run_case(self, case: PeriodicCase) -> subprocess.CompletedProcess:
        self.write_input(case)

        input_path = self.paths.cases_dir / f"{case.name}.inp"
        work_dir = self.paths.work_dir(case.name)
        log_path = self.paths.results_dir / f"{case.name}.log"
        cmd = [self.ansys_exe, "-b", "-i", str(input_path), "-o", str(log_path)]
        print(f"[{case.name}] Running: {shlex.join(cmd)}")

        result = run_ansys(input_path, log_path, work_dir, self.ansys_exe)
        self.collect_results(case)

        if result.returncode != 0:
            print(
                f"[{case.name}] ANSYS returned non-zero exit code: {result.returncode}"
            )
        return result

    def collect_results(self, case: PeriodicCase) -> None:
        work_dir = self.paths.work_dir(case.name)
        patterns = [
            f"{case.name}_pbc_Dmatrix.csv",
            f"{case.name}_rp_Dmatrix.csv",
            f"{case.name}_inertia.txt",
        ]
        for target_path in collect_files(work_dir, self.paths.results_dir, patterns):
            print(f"[{case.name}] Collected {target_path.name}")

    def dry_run(self, cases: list[PeriodicCase]) -> None:
        for case in cases:
            self.write_input(case)
        print(
            f"\nPeriodic dry run complete. {len(cases)} .inp files generated in {self.paths.cases_dir}/"
        )

    def run_all(self, cases: list[PeriodicCase]) -> dict[str, bool]:
        results = {}
        for case in cases:
            try:
                proc = self.run_case(case)
                results[case.name] = proc.returncode == 0
            except Exception as e:
                results[case.name] = False
                print(f"[{case.name}] FAILED: {e}")
        return results
