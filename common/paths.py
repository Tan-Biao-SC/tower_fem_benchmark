"""Project path layout helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved directories for one analysis module."""

    root: Path
    module: str

    @classmethod
    def for_module(cls, root: Path, module: str) -> "ProjectPaths":
        return cls(Path(root), module)

    @property
    def templates_dir(self) -> Path:
        module_templates = self.root / "templates" / self.module
        if module_templates.exists():
            return module_templates
        return self.root / "templates"

    @property
    def cases_dir(self) -> Path:
        return self.root / "cases" / self.module

    @property
    def results_dir(self) -> Path:
        return self.root / "results" / self.module

    @property
    def figures_dir(self) -> Path:
        return self.root / "figures" / self.module

    @property
    def tmp_dir(self) -> Path:
        return self.root / "tmp" / self.module

    def work_dir(self, case_name: str) -> Path:
        return self.tmp_dir / case_name

    def ensure_base_dirs(self) -> None:
        for path in (
            self.cases_dir,
            self.results_dir,
            self.figures_dir,
            self.tmp_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

