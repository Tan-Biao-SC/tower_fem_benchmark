"""Periodic lattice unit runner shell."""

from __future__ import annotations

from common.paths import ProjectPaths

from .case import PeriodicCase
from .engine import PeriodicTemplateEngine


def dry_run_cases(
    cases: list[PeriodicCase],
    paths: ProjectPaths,
    engine: PeriodicTemplateEngine | None = None,
) -> None:
    """Generate periodic APDL inputs without invoking ANSYS."""
    paths.ensure_base_dirs()
    engine = engine or PeriodicTemplateEngine()

    for case in cases:
        input_path = paths.cases_dir / f"{case.name}.inp"
        input_path.write_text(engine.build(case))
        print(f"[{case.name}] Written {input_path}")

    print(
        f"\nPeriodic dry run complete. {len(cases)} .inp files generated in {paths.cases_dir}/"
    )

