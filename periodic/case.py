"""Case definitions for periodic lattice unit analysis."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PeriodicCase:
    """Parameters needed to build one periodic lattice unit model."""

    name: str
    num_subsections: int
    ls: float
    ws: float
    num_sections: int = 1
    elastic_modulus: float = 2.06e11
    poisson_ratio: float = 0.31
    density: float = 7850.0
    thermal_expansion: float = 1.2e-5
    leg_b: float = 0.16
    leg_h: float = 0.16
    leg_tw: float = 0.014
    leg_tf: float = 0.014
    diaphragm_b: float = 0.08
    diaphragm_h: float = 0.08
    diaphragm_tw: float = 0.006
    diaphragm_tf: float = 0.006
    brace_area: float = 7.412e-4

    @property
    def cell_length(self) -> float:
        """Periodic unit length."""
        return self.num_subsections * self.ls

